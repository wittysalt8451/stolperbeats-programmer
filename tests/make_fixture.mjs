// Generates a full bank in the exact format of PatternBank004.txt (Patchstorage).
import fs from 'fs';
import path from 'path';
const dir = path.join(path.dirname(new URL(import.meta.url).pathname), 'fixtures');
fs.mkdirSync(dir, { recursive: true });
const T = [['KICK', 4], ['SNARE', 4], ['HIHAT1', 1], ['HIHAT2', 1], ['PERC1', 1], ['PERC2', 1]];
const r = () => Array.from({ length: 16 }, () => (Math.random() < 0.3 ? '1' : '0')).join('');
const s = T.map(([id, n]) => Array.from({ length: 24 }, (_, i) =>
  `${id} > PTN${i}: ${Array.from({ length: n }, r).join(', ')};`).join('\n')).join('\n\n') + '\n';
fs.writeFileSync(path.join(dir, 'PatternBank004.txt'), s);
console.log('fixture written:', path.join(dir, 'PatternBank004.txt'));
