import fs from 'fs';
const html = fs.readFileSync(new URL('../stolperbeats-bank-editor.html', import.meta.url),'utf8');
const core = html.split('// @core-start')[1].split('// @core-end')[0];
const api = new Function(core + '; return {TRACKS,parseBank,serializeBank,emptyBank,bankNumFromName,nameFromBankNum,hitsAt,SHUFFLES};')();
const {TRACKS,parseBank,serializeBank,bankNumFromName,nameFromBankNum,hitsAt} = api;
let fails=0; const ok=(c,m)=>{ if(!c){fails++;console.log('FAIL',m);} else console.log('ok  ',m); };

// 1) generate a full bank in the exact format of PatternBank004.txt (sections, blank line between, '; ')
const rnd=()=>Array.from({length:16},()=>Math.random()<.3?'1':'0').join('');
const secs = TRACKS.map(t=>Array.from({length:24},(_,i)=>`${t.id} > PTN${i}: ${Array.from({length:t.len/16},rnd).join(', ')};`).join('\n'));
const sample = secs.join('\n\n')+'\n';
// splice in real lines from the published bank to be sure
const real = 'KICK > PTN0: 1110000000000000, 1110000000000000, 1110000000000000, 1110000000000111;';
const sample2 = sample.replace(/^KICK > PTN0: .*$/m, real);
let r = parseBank(sample2);
ok(r.found===144 && r.missing===0 && r.unknown.length===0 && r.warnings.length===0, 'full bank parses clean');
ok(serializeBank(r.bank, r.eol)===sample2, 'round-trip identical (LF)');
// CRLF
const crlf = sample2.replace(/\n/g,'\r\n');
r = parseBank(crlf);
ok(r.eol==='\r\n' && serializeBank(r.bank,r.eol)===crlf, 'round-trip identical (CRLF)');
// tolerant input
r = parseBank('﻿kick>PTN3:1000100010001000,0,1;\n# comment\nHIHAT1 > PTN30: 1111111111111111;\nSNARE > PTN1: 10x1;\nPERC2 > PTN5: 1010101010101010\n');
ok(r.bank.KICK[3][0]===1 && r.bank.KICK[3][4]===1, 'lowercase/no spaces accepted');
ok(r.unknown.length===1, 'comment line reported as unknown');
ok(r.warnings.length===3, 'warnings: short kick, PTN30, invalid chars ('+r.warnings.length+')');
ok(r.bank.PERC2[5][0]===1, 'missing semicolon accepted');
// names
ok(bankNumFromName('PatternBank004.txt')===5 && nameFromBankNum(5)==='PatternBank004.txt' && nameFromBankNum(46)==='PatternBank045.txt', 'bank number <-> file name');
// linear
const b = api.emptyBank(); const sel={KICK:0,SNARE:0,HIHAT1:0,HIHAT2:0,PERC1:0,PERC2:0};
b.KICK[0][0]=1; b.SNARE[0][0]=1; b.HIHAT1[0][0]=1; b.HIHAT2[0][0]=1; b.PERC1[0][0]=1;
b.KICK[0][20]=1; b.HIHAT1[0][4]=1;
let h=hitsAt(b,sel,0,true);
ok(h.SNARE && !h.KICK && !h.HIHAT1 && !h.HIHAT2 && h.PERC1, 'linear: snare wins over kick and hats, perc untouched');
h=hitsAt(b,sel,20,true); ok(h.KICK && !h.HIHAT1, 'linear: kick wins over hat (step 21, hat loops 1 bar)');
h=hitsAt(b,sel,20,false); ok(h.KICK && h.HIHAT1, 'linear off: both');
process.exit(fails?1:0);
