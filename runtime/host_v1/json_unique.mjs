/** Parse JSON only when every object has unique decoded member names. */
export function parseUniqueJson(source) {
  if (typeof source !== 'string') throw new TypeError('JSON source must be a string');
  let offset = 0;
  const whitespace = () => {
    while (source[offset] === ' ' || source[offset] === '\t' ||
        source[offset] === '\n' || source[offset] === '\r') offset++;
  };
  function string() {
    const start = offset;
    if (source[offset++] !== '"') throw new SyntaxError('JSON object member must be a string');
    while (offset < source.length) {
      const character = source[offset++];
      if (character === '"') return JSON.parse(source.slice(start, offset));
      if (character === '\\' && offset < source.length) offset++;
    }
    throw new SyntaxError('unterminated JSON string');
  }
  function value() {
    whitespace();
    const character = source[offset];
    if (character === '"') { string(); return; }
    if (character === '{') {
      offset++;
      whitespace();
      if (source[offset] === '}') { offset++; return; }
      const members = new Set();
      while (true) {
        whitespace();
        const member = string();
        if (members.has(member)) throw new SyntaxError('duplicate JSON object member');
        members.add(member);
        whitespace();
        if (source[offset++] !== ':') throw new SyntaxError('missing JSON member colon');
        value();
        whitespace();
        if (source[offset] === '}') { offset++; return; }
        if (source[offset++] !== ',') throw new SyntaxError('invalid JSON object separator');
      }
    }
    if (character === '[') {
      offset++;
      whitespace();
      if (source[offset] === ']') { offset++; return; }
      while (true) {
        value();
        whitespace();
        if (source[offset] === ']') { offset++; return; }
        if (source[offset++] !== ',') throw new SyntaxError('invalid JSON array separator');
      }
    }
    const start = offset;
    while (offset < source.length && !' \t\n\r,]}'.includes(source[offset])) offset++;
    if (offset === start) throw new SyntaxError('invalid JSON value');
  }
  value();
  whitespace();
  if (offset !== source.length) throw new SyntaxError('trailing JSON content');
  return JSON.parse(source);
}
