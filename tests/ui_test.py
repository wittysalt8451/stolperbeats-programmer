import sys, json, os, pathlib
from playwright.sync_api import sync_playwright
HERE=pathlib.Path(__file__).resolve().parent
S=str(HERE/'fixtures')
OUT=str(HERE/'out'); os.makedirs(OUT, exist_ok=True)
url=(HERE.parent/'stolperbeats-bank-editor.html').as_uri()
with sync_playwright() as p:
    b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    pg=b.new_page(viewport={'width':1280,'height':900}, accept_downloads=True)
    errs=[]
    pg.on('console', lambda m: errs.append(m.text) if m.type=='error' else None)
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(url)
    pg.set_input_files('#fileInput', S+'/PatternBank004.txt')
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
    m=b.new_page(viewport={'width':390,'height':844}, device_scale_factor=2)
    m.goto(url); m.set_input_files('#fileInput', S+'/PatternBank004.txt')
    m.screenshot(path=OUT+'/mobile.png', full_page=False)
    m.evaluate('window.scrollTo(0,700)'); m.screenshot(path=OUT+'/mobile2.png')
    print('mobile horizontal overflow:', m.evaluate('document.documentElement.scrollWidth')>390)
    print('errors:', errs)
    b.close()
