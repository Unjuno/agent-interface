"""Lossless conversion for the frozen private Xvfb true-color layout only."""
import struct
import zlib
def convert(blob):
    if len(blob)<100:raise ValueError('short XWD')
    h=struct.unpack('>25I',blob[:100])
    size,version,fmt,depth,width,height,offset,order,unit,bitorder,pad,bpp,stride,visual,red,green,blue,bits,cmap,colors,*_=h
    if (size<100 or version!=7 or fmt!=2 or depth!=24 or bpp!=32 or visual!=4
        or offset!=0 or order not in (0,1) or (red,green,blue)!=(0xff0000,0xff00,0xff)
        or not 0<width<=2048 or not 0<height<=2048 or stride<width*4):
        raise ValueError('unsupported XWD layout')
    start=size+12*colors
    if len(blob)!=start+stride*height:raise ValueError('XWD length')
    pixels=[]
    for y in range(height):
        row=bytearray([0])
        for x in range(width):
            at=start+y*stride+4*x
            value=int.from_bytes(blob[at:at+4],'little' if order==0 else 'big')
            row.extend(((value>>16)&255,(value>>8)&255,value&255))
        pixels.append(bytes(row))
    def chunk(name,data):return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(pixels)))+chunk(b'IEND',b'')
