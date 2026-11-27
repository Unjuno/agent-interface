'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const zlib = require('node:zlib');

const ROOT = '/src';
const INPUTS = '/inputs';
const OUTPUTS = '/results';
const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'manifest.json'), 'utf8'));
const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

function sha256(buf) { return crypto.createHash('sha256').update(buf).digest('hex'); }
function crc32(buf) {
  let c = 0xffffffff;
  for (const b of buf) {
    c ^= b;
    for (let k = 0; k < 8; k++) c = (c >>> 1) ^ ((c & 1) ? 0xedb88320 : 0);
  }
  return (c ^ 0xffffffff) >>> 0;
}
function parsePng(buf) {
  if (!buf.subarray(0, 8).equals(signature)) throw new Error('PNG signature mismatch');
  let offset = 8, ihdr, idat = [];
  while (offset < buf.length) {
    const len = buf.readUInt32BE(offset); offset += 4;
    const type = buf.subarray(offset, offset + 4); offset += 4;
    const data = buf.subarray(offset, offset + len); offset += len;
    const recorded = buf.readUInt32BE(offset); offset += 4;
    const check = Buffer.concat([type, data]);
    if (crc32(check) !== recorded) throw new Error(`PNG CRC mismatch: ${type.toString()}`);
    if (type.toString() === 'IHDR') ihdr = data;
    else if (type.toString() === 'IDAT') idat.push(data);
    else if (type.toString() === 'IEND') break;
  }
  if (!ihdr || ihdr.length !== 13) throw new Error('missing IHDR');
  const width = ihdr.readUInt32BE(0), height = ihdr.readUInt32BE(4);
  if (ihdr[8] !== 8 || ihdr[9] !== 2 || ihdr[10] !== 0 || ihdr[11] !== 0 || ihdr[12] !== 0)
    throw new Error('only non-interlaced 8-bit RGB PNG is supported');
  const bpp = 3, stride = width * bpp;
  const packed = zlib.inflateSync(Buffer.concat(idat));
  if (packed.length !== height * (stride + 1)) throw new Error('unexpected PNG scanline length');
  const pixels = Buffer.alloc(height * stride);
  let src = 0;
  for (let y = 0; y < height; y++) {
    const filter = packed[src++], row = y * stride;
    for (let x = 0; x < stride; x++) {
      const raw = packed[src++], left = x >= bpp ? pixels[row + x - bpp] : 0;
      const up = y ? pixels[row - stride + x] : 0;
      const upperLeft = y && x >= bpp ? pixels[row - stride + x - bpp] : 0;
      let value;
      if (filter === 0) value = raw;
      else if (filter === 1) value = raw + left;
      else if (filter === 2) value = raw + up;
      else if (filter === 3) value = raw + Math.floor((left + up) / 2);
      else if (filter === 4) {
        const p = left + up - upperLeft;
        const pa = Math.abs(p - left), pb = Math.abs(p - up), pc = Math.abs(p - upperLeft);
        value = raw + (pa <= pb && pa <= pc ? left : pb <= pc ? up : upperLeft);
      } else throw new Error(`unknown PNG filter ${filter}`);
      pixels[row + x] = value & 255;
    }
  }
  return { width, height, pixels };
}
function chunk(type, data) {
  const name = Buffer.from(type), len = Buffer.alloc(4), crc = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  crc.writeUInt32BE(crc32(Buffer.concat([name, data])));
  return Buffer.concat([len, name, data, crc]);
}
function encodePng(width, height, pixels) {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0); ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 2;
  const stride = width * 3, scan = Buffer.alloc(height * (stride + 1));
  for (let y = 0; y < height; y++) {
    scan[y * (stride + 1)] = 0;
    pixels.copy(scan, y * (stride + 1) + 1, y * stride, (y + 1) * stride);
  }
  return Buffer.concat([signature, chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(scan, { level: 6 })), chunk('IEND', Buffer.alloc(0))]);
}
function cropPixels(frame, roi) {
  const out = Buffer.alloc(roi.width * roi.height * 3);
  for (let y = 0; y < roi.height; y++) {
    const from = ((roi.y + y) * frame.width + roi.x) * 3;
    frame.pixels.copy(out, y * roi.width * 3, from, from + roi.width * 3);
  }
  return out;
}
function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${canonical(value[k])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

fs.mkdirSync(path.join(OUTPUTS, 'artifacts'), { recursive: true });
const rows = [];
let totalFullBytes = 0, totalFocusedBytes = 0;
for (const item of manifest.frames) {
  const source = fs.readFileSync(path.join(INPUTS, item.file));
  if (sha256(source) !== item.png_sha256) throw new Error(`source PNG SHA mismatch: ${item.frame_id}`);
  const frame = parsePng(source);
  if (frame.width !== item.width || frame.height !== item.height) throw new Error(`dimension mismatch: ${item.frame_id}`);
  if (sha256(frame.pixels) !== item.source_pixel_sha256) throw new Error(`source pixel SHA mismatch: ${item.frame_id}`);
  const pixels = cropPixels(frame, manifest.roi);
  const crop = encodePng(manifest.roi.width, manifest.roi.height, pixels);
  const cropName = `${item.sequence}.png`;
  fs.writeFileSync(path.join(OUTPUTS, 'artifacts', cropName), crop, { flag: 'wx' });
  const fullPayload = {
    frame_id: item.frame_id, mode: 'FULL_FRAME', png_base64: source.toString('base64'),
    sequence: item.sequence, source_pixel_sha256: item.source_pixel_sha256,
  };
  const focusedPayload = {
    focus: { height: manifest.roi.height, reason: 'post_input_text_state_tracking', width: manifest.roi.width, x: manifest.roi.x, y: manifest.roi.y },
    frame_id: item.frame_id, mode: 'FOCUSED_REGION', png_base64: crop.toString('base64'),
    sequence: item.sequence, source_pixel_sha256: item.source_pixel_sha256,
  };
  const fullBytes = Buffer.byteLength(canonical(fullPayload), 'utf8');
  const focusedBytes = Buffer.byteLength(canonical(focusedPayload), 'utf8');
  totalFullBytes += fullBytes; totalFocusedBytes += focusedBytes;
  rows.push({
    crop_file: `artifacts/${cropName}`, crop_png_sha256: sha256(crop),
    crop_pixel_sha256: sha256(pixels), focused_payload_bytes: focusedBytes,
    frame_id: item.frame_id, full_payload_bytes: fullBytes,
    roi_pixel_sha256: sha256(pixels), sequence: item.sequence,
    source_png_sha256: sha256(source), source_pixel_sha256: item.source_pixel_sha256,
  });
}
const distinctRoiStates = new Set(rows.map(row => row.roi_pixel_sha256)).size;
const result = {
  allocation: manifest.allocation,
  rows,
  summary: {
    distinct_roi_states: distinctRoiStates,
    focused_payload_bytes: totalFocusedBytes,
    full_frame_payload_bytes: totalFullBytes,
    saved_bytes: totalFullBytes - totalFocusedBytes,
  },
};
fs.writeFileSync(path.join(OUTPUTS, 'candidate.json'), `${JSON.stringify(result, null, 2)}\n`, { flag: 'wx' });
process.stdout.write(`${JSON.stringify({ allocation: manifest.allocation, rows: rows.length, distinct_roi_states: distinctRoiStates, saved_bytes: totalFullBytes - totalFocusedBytes })}\n`);
