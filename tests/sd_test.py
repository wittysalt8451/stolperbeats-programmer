# SD-kaartpaneel. showDirectoryPicker wordt vervangen door een map in OPFS (een echte
# FileSystemDirectoryHandle), zodat scannen, back-up en schrijven getest kunnen worden.
import os, io, json, pathlib, tempfile, threading, zipfile, functools, http.server
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'out'; OUT.mkdir(exist_ok=True)
BANK = (HERE / 'fixtures' / 'PatternBank004.txt').read_text()
CFG = ('MIDI_CHANNEL_KICK: 1;\r\n'
       'PATTERNBANK_ACTIVE: 1111000000000000, 0000000000000000, 0000000000000000, 0000000000000000;\r\n'
       'SOMETHING ELSE\r\n'
       'TEMPO: 120;\r\n')
CARD = {
    'PatternBank000.txt': BANK,
    'PatternBank004.txt': BANK,
    '._PatternBank004.txt': 'x',
    'MachineConfig.txt': CFG,
    'MIDI/MidiBank00.txt': 'CH > 1;\n',
}

fails = 0
def ok(c, m):
    global fails
    print('ok  ' if c else 'FAIL', m)
    if not c: fails += 1

# OPFS werkt alleen in een secure context; file:// telt daar niet altijd als zodanig.
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
handler = functools.partial(Quiet, directory=str(HERE.parent))
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{srv.server_port}/stolperbeats-bank-editor.html'

SETUP = '''async files => {
  const root = await navigator.storage.getDirectory();
  try { await root.removeEntry('card', { recursive: true }); } catch (_) {}
  const card = await root.getDirectoryHandle('card', { create: true });
  for (const [path, text] of Object.entries(files)) {
    const parts = path.split('/');
    let d = card;
    for (const p of parts.slice(0, -1)) d = await d.getDirectoryHandle(p, { create: true });
    const w = await (await d.getFileHandle(parts.at(-1), { create: true })).createWritable();
    await w.write(text); await w.close();
  }
  const bin = await (await card.getFileHandle('state.bin', { create: true })).createWritable();
  await bin.write(new Uint8Array([0, 1, 2, 255, 0x53, 0x42])); await bin.close();
  window.showDirectoryPicker = async () => card;
}'''
READ = '''async path => {
  const card = await (await navigator.storage.getDirectory()).getDirectoryHandle('card');
  try { return await (await (await card.getFileHandle(path)).getFile()).text(); } catch (_) { return null; }
}'''

exe = os.environ.get('CHROMIUM') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe)
    pg = b.new_page(viewport={'width': 1280, 'height': 900}, accept_downloads=True)
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'favicon' not in (m.location or {}).get('url', '') else None)
    dialogs = []
    def on_dialog(d):
        dialogs.append(d.message); d.dismiss()
    pg.on('dialog', on_dialog)
    pg.goto(url)
    pg.evaluate(SETUP, CARD)

    # scannen
    pg.click('#btnCard')
    pg.wait_for_selector('#sd:not([hidden]) .bk')
    summ = pg.inner_text('#sdSummary')
    ok('2 banken, 4 aan' in summ, f'samenvatting: {summ.strip()}')
    ok(pg.eval_on_selector_all('.bk.file', 'e=>e.map(x=>x.innerText.trim())') == ['1', '5'], 'bankbestanden 1 en 5 (._ genegeerd)')
    ok(pg.eval_on_selector_all('.bk-act[aria-pressed=true]', 'e=>e.length') == 4, '4 banken aan')
    rem = pg.inner_text('#sdRemarks')
    ok('bank 2, 3, 4' in rem and 'macOS' in rem, 'opmerkingen: aan zonder bestand, macOS-metadata')
    files = pg.inner_text('#sdFiles')
    ok('MIDI/MidiBank00.txt' in files and 'state.bin' in files and 'MachineConfig.txt' in files, 'overige bestanden, ook in submappen')
    ok('TEMPO' in pg.inner_text('#sdConfig') and '1 regel(s) in een ander formaat' in pg.inner_text('#sdConfig'), 'MachineConfig-tabel')
    ok(pg.inner_text('#btnSave') == 'Opslaan op kaart', 'opslaanknop schrijft naar kaart')

    # bekijken: tekst en hex
    rows = pg.locator('#sdFiles tr')
    for i in range(rows.count()):
        if 'state.bin' in rows.nth(i).inner_text(): rows.nth(i).locator('button').click()
    pg.wait_for_selector('#sdView:not([hidden])')
    ok('000000  00 01 02 ff 53 42' in pg.inner_text('#sdView'), 'binair bestand als hex')

    # bank 5 aanzetten en MachineConfig opslaan: eerst back-up
    pg.locator('.bk-act[data-n="5"]').click()
    ok(not pg.is_disabled('#sdCfgSave') and '1 bank' in pg.inner_text('#sdCfgInfo'), 'wijziging zichtbaar')
    with pg.expect_download() as d:
        pg.click('#sdCfgSave')
    dl = d.value
    pg.wait_for_function('document.querySelector("#sdCfgSave").disabled')
    ok(dl.suggested_filename.startswith('stolperbeats-sd-backup-') and dl.suggested_filename.endswith('.zip'), f'back-up: {dl.suggested_filename}')
    z = zipfile.ZipFile(io.BytesIO(open(dl.path(), 'rb').read()))
    ok(z.testzip() is None, 'zip is geldig')
    names = sorted(z.namelist())
    ok(names == sorted(list(CARD) + ['state.bin']), f'zip bevat alle bestanden: {names}')
    ok(z.read('MachineConfig.txt').decode() == CFG, 'zip bevat de originele MachineConfig')
    new_cfg = pg.evaluate(READ, 'MachineConfig.txt')
    ok(new_cfg == CFG.replace('1111000000000000, 0000', '1111100000000000, 0000', 1), 'alleen PATTERNBANK_ACTIVE gewijzigd, CRLF behouden')
    ok(pg.is_disabled('#sdCfgSave') and pg.eval_on_selector_all('.bk-act[aria-pressed=true]', 'e=>e.length') == 5, 'na opslaan: 5 aan, niets meer open')
    ok('Back-up gemaakt' in pg.inner_text('#sdStatus'), 'status toont back-up')

    # bank 5 openen, bewerken, opslaan op kaart (geen tweede back-up)
    pg.locator('.bk-open[data-n="5"]').click()
    pg.wait_for_function('document.querySelector("#fileName").textContent === "PatternBank004.txt"')
    ok(pg.locator('.bk.cur').inner_text().strip() == '5', 'geopende bank gemarkeerd')
    pg.locator('.track').nth(0).locator('.step').nth(3).click()
    downloads = []
    pg.on('download', lambda d: downloads.append(d))
    pg.keyboard.press('Control+s')
    pg.wait_for_function('document.querySelector("#dirty").textContent === ""')
    ok(pg.evaluate(READ, 'PatternBank004.txt') == pg.evaluate('serializeBank(bank, eol)'), 'bank 5 op kaart = editor')
    ok(not downloads and not dialogs, 'geen tweede back-up, geen vraag bij eigen bestand')

    # als bank 7 opslaan: nieuw bestand, staat uit
    pg.fill('#bankNum', '7'); pg.dispatch_event('#bankNum', 'change')
    pg.keyboard.press('Control+s')
    pg.wait_for_function('document.querySelector("#noticeText").textContent.includes("PatternBank006")')
    ok(pg.evaluate(READ, 'PatternBank006.txt') is not None, 'PatternBank006.txt aangemaakt')
    ok('Bank 7 staat uit' in pg.inner_text('#noticeText'), 'melding: bank 7 staat uit')
    ok(pg.locator('.bk.file').count() == 3, 'herscand: 3 banken')

    # als bank 1 opslaan: bestaat al, vraag; geweigerd = ongewijzigd
    pg.fill('#bankNum', '1'); pg.dispatch_event('#bankNum', 'change')
    pg.keyboard.press('Control+s')
    pg.wait_for_timeout(300)
    ok(dialogs and 'Overschrijven' in dialogs[-1], 'vraag bij overschrijven ander bestand')
    ok(pg.evaluate(READ, 'PatternBank000.txt') == BANK, 'weigeren laat bank 1 ongemoeid')

    # lege bank via raster
    pg.locator('#bankNum').blur()
    pg.evaluate('setDirty(false)')
    pg.locator('.bk-open[data-n="20"]').click()
    ok(pg.inner_text('#fileName') == 'PatternBank019.txt' and pg.evaluate('bank.KICK[0].every(v=>v===0)'), 'klik op lege bank geeft nieuwe bank 20')
    pg.screenshot(path=str(OUT / 'sd-desktop.png'), full_page=True)

    # terugval: webkitdirectory, alleen lezen
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td) / 'SDCARD'
        for path, text in CARD.items():
            f = root / path; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(text, newline='')
        fb = b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2, accept_downloads=True)
        fb.on('pageerror', lambda e: errs.append(str(e)))
        fb.add_init_script('delete window.showDirectoryPicker')
        fb.goto(url)
        fb.click('#btnCard')  # opent de verborgen input; bestanden zetten we direct
        fb.set_input_files('#dirInput', str(root))
        fb.wait_for_selector('#sd:not([hidden]) .bk')
        ok('alleen lezen' in fb.inner_text('#sdSummary') and 'SDCARD' in fb.inner_text('#sdSummary'), 'terugval: alleen lezen')
        ok(fb.locator('.bk.file').count() == 2, 'terugval: 2 banken')
        fb.locator('.bk-act[data-n="6"]').click()
        with fb.expect_download() as d:
            fb.click('#sdCfgSave')
        ok(d.value.suggested_filename == 'MachineConfig.txt' and
           open(d.value.path(), newline='').read() == CFG.replace('1111000000000000, 0000', '1111010000000000, 0000', 1),
           'terugval: MachineConfig als download')
        fb.screenshot(path=str(OUT / 'sd-mobile.png'), full_page=True)
        ok(fb.evaluate('document.documentElement.scrollWidth') <= 390, 'mobiel: geen horizontale scroll')

    ok(not errs, f'geen fouten in de console {errs}')
    b.close()
srv.shutdown()
raise SystemExit(1 if fails else 0)
