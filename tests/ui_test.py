import sys, json, os, pathlib
from playwright.sync_api import sync_playwright
HERE=pathlib.Path(__file__).resolve().parent
S=str(HERE/'fixtures')
OUT=str(HERE/'out'); os.makedirs(OUT, exist_ok=True)
url=(HERE.parent/'index.html').as_uri()
with sync_playwright() as p:
    exe=os.environ.get('CHROMIUM') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
    b=p.chromium.launch(executable_path=exe, args=['--autoplay-policy=no-user-gesture-required'])
    pg=b.new_page(viewport={'width':1280,'height':900}, accept_downloads=True)
    errs=[]
    pg.on('console', lambda m: errs.append(m.text) if m.type=='error' else None)
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(url)
    print('lands on start page:', pg.evaluate('tab')=='home', 'photo loaded:', pg.evaluate('document.querySelector("#heroImg").naturalWidth')>0)
    pg.screenshot(path=OUT+'/home.png', full_page=False)
    pg.set_input_files('#fileInput', S+'/PatternBank004.txt')
    pg.wait_for_function('document.querySelector("#noticeText").textContent.includes("Opened")')
    print('tab after opening a bank:', pg.evaluate('tab'))
    print('notice:', pg.inner_text('#noticeText'))
    print('bank field:', pg.input_value('#bankNum'), pg.inner_text('#fileName'))
    on_before = pg.eval_on_selector_all('.track:nth-child(1) .step.on','e=>e.length')
    # toggle first kick step twice via mouse (pointerdown)
    st = pg.locator('.track').nth(0).locator('.step').nth(1)
    st.click()
    on_after = pg.eval_on_selector_all('.track:nth-child(1) .step.on','e=>e.length')
    print('kick on before/after click:', on_before, on_after, 'dirty:', pg.inner_text('#dirty'))
    # drag paint across hihat1 steps 0..7
    hh = pg.locator('.track').nth(2).locator('.step')
    b0=hh.nth(0).bounding_box(); b7=hh.nth(7).bounding_box()
    pg.mouse.move(b0['x']+5,b0['y']+5); pg.mouse.down(); pg.mouse.move(b7['x']+5,b7['y']+5,steps=12); pg.mouse.up()
    print('hh1 painted on:', pg.eval_on_selector_all('.track:nth-child(3) .step.on','e=>e.length'))
    pg.keyboard.press('Control+z')
    print('after undo hh1 on:', pg.eval_on_selector_all('.track:nth-child(3) .step.on','e=>e.length'))
    # select pattern 5 for all, shuffle 7 (index 6), feeling rolls, linear, play
    pg.locator('#allStrip button').nth(5).click()
    pg.locator('#shuffleBtns button').nth(6).click()
    pg.locator('#feelBtns button').nth(1).click()
    pg.click('#btnLinear')
    pg.click('#btnPlay')
    pg.wait_for_timeout(1200)
    print('playhead cells:', pg.eval_on_selector_all('.step.ph','e=>e.length'), 'ctx state:', pg.evaluate('ctx.state'))
    pg.screenshot(path=OUT+'/desktop.png', full_page=True)
    pg.keyboard.press('Space')
    print('playing after space:', pg.evaluate('playing'))
    # copy/paste kick -> perc1 (64 -> 16)
    pg.locator('.track').nth(0).locator('[data-act=copy]').click()
    pg.locator('.track').nth(4).locator('[data-act=paste]').click()
    same = pg.evaluate('Array.from(bank.PERC1[sel.PERC1]).join("")===Array.from(bank.KICK[sel.KICK].slice(0,16)).join("")')
    print('paste 64->16 ok:', same)
    # download and compare with model
    with pg.expect_download() as d:
        pg.click('#btnDownload')
    dl=d.value; path=dl.path(); txt=open(path).read()
    print('download name:', dl.suggested_filename, 'matches model:', txt==pg.evaluate('serializeBank(bank,eol)'))
    # voice levels via offline render
    lv = pg.evaluate('''async()=>{
      const out={};
      for (const id of Object.keys(VOICES)){
        const off=new OfflineAudioContext(1,44100*0.6,44100);
        const saved=[ctx,master,noiseBuf,openHat];
        ctx=off; master=off.createGain(); master.connect(off.destination);
        noiseBuf=off.createBuffer(1,off.sampleRate,off.sampleRate); const d=noiseBuf.getChannelData(0); for(let i=0;i<d.length;i++) d[i]=Math.random()*2-1;
        openHat=null;
        VOICES[id](0.0);
        const buf=await off.startRendering(); const x=buf.getChannelData(0);
        let pk=0, ss=0; for(const v of x){pk=Math.max(pk,Math.abs(v)); ss+=v*v;}
        // rms over first 100ms
        let s2=0; for(let i=0;i<4410;i++) s2+=x[i]*x[i];
        out[id]={peak:+pk.toFixed(3), rms100ms:+Math.sqrt(s2/4410).toFixed(3)};
        [ctx,master,noiseBuf,openHat]=saved;
      }
      return out;}''')
    print(json.dumps(lv))
    # settings files from the SD card (default_settings/), opened at once
    REAL=HERE.parent/'default_settings'
    SETTINGS=['MachineConfig.txt','EnvelopeSettings.txt','MachineState.txt']
    def dl_text(page, sel):
        with page.expect_download() as d: page.click(sel)
        return d.value.suggested_filename, open(d.value.path(), newline='').read()
    def changed_lines(name, txt):
        a=(REAL/name).read_bytes().decode().split('\r\n'); c=txt.split('\r\n')
        return [l for i,l in enumerate(c) if i>=len(a) or l!=a[i]] if len(a)==len(c) else ['LINE COUNT DIFFERS']
    if REAL.exists():
        pg.set_input_files('#fileInput', [str(REAL/f) for f in SETTINGS])
        pg.wait_for_function('document.querySelector("#noticeText").textContent.includes("MachineState")')
        print('settings notice:', pg.inner_text('#noticeText').replace('\n',' | '))
        print('tab after open:', pg.evaluate('tab'))
        print('active banks shown:', pg.eval_on_selector_all('#panel-config .banks button[aria-pressed=true]','e=>e.map(b=>b.textContent).join(",")'))
        pg.locator('#panel-config .banks button').nth(9).click()
        print('config tab marked unsaved:', 'unsaved' in pg.get_attribute('#tab-config','class'))
        # transport out needs clock out: switch clock out off, expect a warning
        pg.click('#panel-config [aria-label="MIDI clock out"]')
        print('needs warning:', pg.locator('#panel-config .fwarn:visible').all_inner_texts())
        name, txt = dl_text(pg, '#panel-config [data-act=download]')
        print('config download:', name, changed_lines('MachineConfig.txt', txt))
        pg.screenshot(path=OUT+'/config.png', full_page=True)
        pg.click('#tab-env')
        print('env plots:', pg.eval_on_selector_all('#panel-env .envplot svg','e=>e.length'), 'captions:', pg.locator('#panel-env .envplot p').all_inner_texts())
        pg.locator('#panel-env .card').nth(0).locator('.seg').nth(0).locator('button').nth(0).click()
        pg.locator('#panel-env .card').nth(1).locator('.seg').nth(1).locator('button').nth(11).click()
        num = pg.locator('#panel-env [aria-label=ENV1_KICK_VEL][type=number]')
        num.fill('100'); num.press('Enter')
        print('env inactive groups:', pg.eval_on_selector_all('#panel-env .velgrp','e=>e.map(g=>g.classList.contains("inactive"))'))
        name, txt = dl_text(pg, '#panel-env [data-act=download]')
        print('env download:', name, changed_lines('EnvelopeSettings.txt', txt))
        pg.screenshot(path=OUT+'/env.png', full_page=True)
        pg.click('#tab-state')
        t = pg.locator('#panel-state [aria-label=TEMPO][type=number]'); t.fill('300'); t.press('Enter')
        pg.select_option('#panel-state select[aria-label=BANK]', '20')
        print('bank warning:', pg.locator('#panel-state .fwarn:visible').all_inner_texts())
        pg.click('#panel-state [aria-label="Mute Snare"]')
        pg.locator('#panel-state .seg').nth(1).locator('button').nth(6).click()
        name, txt = dl_text(pg, '#panel-state [data-act=download]')
        print('state download:', name, changed_lines('MachineState.txt', txt))
        pg.screenshot(path=OUT+'/state.png', full_page=True)
        pg.keyboard.press('Space')
        print('space on state tab does not play:', pg.evaluate('playing')==False)
    pg.click('.logo')
    print('logo opens start page:', pg.evaluate('tab'), pg.is_visible('#panel-home'), 'tabs selected:', pg.eval_on_selector_all('[role=tab][aria-selected=true]','e=>e.length'))
    print('tab order:', pg.eval_on_selector_all('[role=tab]','e=>e.map(b=>b.textContent).join(" | ")'))
    pg.locator('.jump button').nth(1).click(); print('start page link to envelopes:', pg.evaluate('tab'))
    pg.click('.logo')
    pg.screenshot(path=OUT+'/home-full.png', full_page=True)
    print('start page height:', pg.evaluate('document.documentElement.scrollHeight'))
    # info popups: every key used on the page exists, popups open, close and stay inside the viewport
    keys = pg.eval_on_selector_all('[data-info]', 'e=>[...new Set(e.map(b=>b.dataset.info))]')
    print('info keys on start page without content:', [k for k in keys if not pg.evaluate(f'!!INFO[{json.dumps(k)}]')])
    pg.locator('#panel-home .info').first.click()
    print('popup opens:', pg.is_visible('#tip'), pg.inner_text('#tip h4'), pg.get_attribute('#panel-home .info', 'aria-expanded'))
    pg.keyboard.press('Escape'); print('escape closes:', not pg.is_visible('#tip'))
    missing, outside = [], []
    for t in ['patterns', 'env', 'config', 'state']:
        pg.click('#tab-'+t)
        btns = pg.locator(f'#panel-{t} [data-info]:visible')
        for i in range(btns.count()):
            btn = btns.nth(i); key = btn.get_attribute('data-info')
            btn.scroll_into_view_if_needed(); btn.click()
            if not pg.is_visible('#tip') or not pg.inner_text('#tip h4'): missing.append(key)
            bb = pg.locator('#tip').bounding_box()
            if bb['x'] < 0 or bb['x'] + bb['width'] > 1280: outside.append(key)
            pg.mouse.click(2, 2)
    print('info popups that did not open:', missing, 'outside viewport:', outside)
    print('popup tables (waves, clockdivs):', pg.evaluate('[INFO.waveform.h().split("<tr>").length-2, INFO.clockdiv.h().split("<tr>").length-2]'))
    pg.click('#tab-env'); pg.locator('#panel-env [data-info=clockdiv]').first.click()
    pg.screenshot(path=OUT+'/info-popup.png')
    pg.mouse.click(2, 2); print('outside click closes:', not pg.is_visible('#tip'))
    pg.click('.logo')
    pg.goto(url+'#env'); print('hash opens tab:', pg.evaluate('tab'))
    m=b.new_page(viewport={'width':390,'height':844}, device_scale_factor=2)
    m.goto(url)
    m.screenshot(path=OUT+'/mobile-home.png', full_page=False)
    print('mobile home horizontal overflow:', m.evaluate('document.documentElement.scrollWidth')>390)
    m.locator('#panel-home .info').first.click()
    bb=m.locator('#tip').bounding_box(); print('mobile popup inside viewport:', bb['x']>=0 and bb['x']+bb['width']<=390)
    m.screenshot(path=OUT+'/mobile-info.png'); m.keyboard.press('Escape')
    m.set_input_files('#fileInput', S+'/PatternBank004.txt')
    m.wait_for_function('document.querySelector("#noticeText").textContent.includes("Opened")')
    m.screenshot(path=OUT+'/mobile.png', full_page=False)
    m.evaluate('window.scrollTo(0,700)'); m.screenshot(path=OUT+'/mobile2.png')
    print('mobile horizontal overflow:', m.evaluate('document.documentElement.scrollWidth')>390)
    if REAL.exists():
        m.set_input_files('#fileInput', [str(REAL/f) for f in SETTINGS])
        m.wait_for_function('document.querySelector("#noticeText").textContent.includes("MachineState")')
        for t in ['env','config','state']:
            m.click('#tab-'+t); m.screenshot(path=OUT+f'/mobile-{t}.png', full_page=True)
            print(f'mobile {t} horizontal overflow:', m.evaluate('document.documentElement.scrollWidth')>390)
    print('errors:', errs)
    b.close()
