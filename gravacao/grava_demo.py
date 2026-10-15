"""Grava um vídeo do Painel em uso (colar o link, ver a fila, abrir o corte, aprovar, calendário) sem mudar nada na
produção: nenhum pedido é enviado e nenhuma decisão é gravada (todo envio que não seja leitura fica bloqueado nesta
janela). Uso: grava_demo.py <saida.mp4> <largura> <altura> <escala>"""
import asyncio, base64, json, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
import websockets

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
FFMPEG = str(next(Path.home().glob("AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/*/bin/ffmpeg.exe")))
saida, larg, alt, escala = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
celular = larg < 600
LINK = "https://www.youtube.com/watch?v=t0xq1uTi1cc"
porta = 9379
DURA = 24.0
LENTO = float(sys.argv[5]) if len(sys.argv) > 5 else 2.5
FPS = 60
perfil = tempfile.mkdtemp(prefix="demo")
quadros = Path(tempfile.mkdtemp(prefix="quadros"))
proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", f"--remote-debugging-port={porta}",
                         f"--user-data-dir={perfil}", "--remote-allow-origins=*", "--mute-audio",
                         "--autoplay-policy=no-user-gesture-required", "about:blank"], stderr=subprocess.DEVNULL)

ANTES = r"""
try{sessionStorage.setItem('abriu','1');localStorage.setItem('escala-base','2');if(innerWidth>600)localStorage.setItem('escala','125')}catch{}
const _fetch=window.fetch;
window.fetch=(u,o)=>(o&&o.method&&o.method.toUpperCase()!='GET')?Promise.reject(new Error('gravação: envio bloqueado')):_fetch(u,o);
"""
PONTEIRO = r"""
(()=>{
 const s=document.createElement('style');
 s.textContent=`#__p{position:fixed;left:0;top:0;z-index:2147483647;pointer-events:none;transition:transform .7s cubic-bezier(.3,.1,.2,1)}
 #__p svg{display:block;filter:drop-shadow(0 2px 4px #000c)}
 #__p i{position:absolute;left:-18px;top:-18px;width:36px;height:36px;border-radius:50%;border:3px solid #ffe500;opacity:0}
 #__p.toca i{animation:__t .5s ease-out}
 @keyframes __t{from{opacity:1;transform:scale(.3)}to{opacity:0;transform:scale(1.5)}}
 .__novo{animation:__n 1.4s ease-out}
 @keyframes __n{0%{box-shadow:0 0 0 0 #ffe500cc}100%{box-shadow:0 0 0 18px #ffe50000}}`;
 document.head.append(s);
 const p=document.createElement('div');p.id='__p';
 p.innerHTML=CEL?'<i></i><svg width="34" height="34" viewBox="0 0 34 34" style="margin:-17px 0 0 -17px"><circle cx="17" cy="17" r="13" fill="#ffffff55" stroke="#fff" stroke-width="2"/></svg>'
  :'<i></i><svg width="26" height="26" viewBox="0 0 24 24"><path d="M4 2l15 11h-7l-3 8z" fill="#fff" stroke="#000" stroke-width="1.4" stroke-linejoin="round"/></svg>';
 document.body.append(p);
 window.__casa=()=>{(document.querySelector('dialog[open]')||document.body).append(p)};
 window.__vai=(x,y)=>{__casa();p.style.transform=`translate(${x}px,${y}px)`};
 window.__ate=sel=>{const e=[...document.querySelectorAll(sel)].find(e=>e.getClientRects().length);if(!e)return false;
  const r=e.getBoundingClientRect();__vai(r.left+r.width*.5,r.top+r.height*.55);return true};
 window.__toca=()=>{p.classList.remove('toca');void p.offsetWidth;p.classList.add('toca')};
 __vai(innerWidth*.55,innerHeight*.6);
})()
""".replace("CEL", "true" if celular else "false")


async def main():
    for _ in range(40):
        try:
            abas = json.load(urllib.request.urlopen(f"http://127.0.0.1:{porta}/json"))
            break
        except Exception:
            time.sleep(.25)
    ws_url = [a for a in abas if a["type"] == "page"][0]["webSocketDebuggerUrl"]
    async with websockets.connect(ws_url, max_size=None) as ws:
        espera, eventos, n = {}, {}, 0

        async def le():
            async for m in ws:
                r = json.loads(m)
                if r.get("id") in espera:
                    espera.pop(r["id"]).set_result(r.get("result", {}))
                elif r.get("method") in eventos:
                    eventos[r["method"]](r["params"])

        leitor = asyncio.create_task(le())

        async def manda(metodo, **params):
            nonlocal n
            n += 1
            f = asyncio.get_running_loop().create_future()
            espera[n] = f
            await ws.send(json.dumps({"id": n, "method": metodo, "params": params}))
            return await f

        async def js(expr):
            r = await manda("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
            return r.get("result", {}).get("value")

        await manda("Emulation.setDeviceMetricsOverride", width=larg, height=alt, deviceScaleFactor=escala, mobile=celular)
        await manda("Page.enable")
        await manda("Page.addScriptToEvaluateOnNewDocument", source=ANTES)
        await manda("Page.navigate", url="http://localhost:8770/")
        await asyncio.sleep(6)
        await js(PONTEIRO)
        await asyncio.sleep(.5)

        # filmagem pelo screencast do Chrome (quadros na cadência da tela), com a hora de chegada de cada um
        chegou = []

        def quadro(p):
            (quadros / f"{len(chegou):05d}.jpg").write_bytes(base64.b64decode(p["data"]))
            chegou.append(time.perf_counter())
            asyncio.get_running_loop().create_task(manda("Page.screencastFrameAck", sessionId=p["sessionId"]))

        eventos["Page.screencastFrame"] = quadro
        await manda("Animation.enable")
        await manda("Animation.setPlaybackRate", playbackRate=1 / LENTO)
        await js(f"const v=document.getElementById('vid');v.defaultPlaybackRate={1 / LENTO};v.addEventListener('ratechange',()=>{{if(v.playbackRate!={1 / LENTO})v.playbackRate={1 / LENTO}}})")
        await manda("Page.startScreencast", format="jpeg", quality=82, maxWidth=4000, maxHeight=4000, everyNthFrame=1)
        await asyncio.sleep(.7)
        t0 = time.perf_counter()

        # roteiro com hora marcada, igual no computador e no celular, para os dois vídeos andarem juntos
        async def em(t):
            await asyncio.sleep(max(0, t0 + t * LENTO - time.perf_counter()))

        async def ate(t, sel):
            await em(t)
            await js(f"__ate({json.dumps(sel)})")
            await em(t + .9)
            await js("__toca()")

        # 1. colar o link e pedir os cortes (o pedido NÃO é enviado: o episódio do link é o que já está na fila)
        await ate(.6, "#n-url")
        await js("document.getElementById('n-url').focus()")
        for i in range(1, len(LINK) + 1):
            await em(1.8 + i * .035)
            await js(f"document.getElementById('n-url').value={json.dumps(LINK[:i])}")
        await ate(3.8, "#n-cria")
        await em(4.95)
        await js("document.getElementById('n-url').value='';document.getElementById('n-url').blur();"
                 "document.querySelector('.pedido.agora')?.classList.add('__novo')")
        await em(5.4)
        await js("__ate('.pedido.agora')")
        await em(6.6)
        await js("__ate('#agora')")

        # 2. os cortes prontos, em A revisar
        await ate(8.3, "#t-cortes,#aba-cortes")
        await em(9.4)
        await js("document.getElementById('aba-cortes').click()")

        # 3. abrir o primeiro corte e assistir
        await ate(10.9, "#grupos .corte .capa")
        await em(12.0)
        await js("document.querySelector('#grupos .corte .capa').click()")

        # 4. aprovar (só o desenho do botão e do joinha: a decisão não é gravada)
        await ate(16.4, "#voto-sim")
        await em(17.5)
        await js("document.getElementById('voto-sim').classList.add('ativa');"
                 "const c=document.getElementById('curtida');c.classList.remove('vai');void c.offsetWidth;c.classList.add('vai')")
        await em(19.0)
        await js("document.getElementById('vid').pause();document.fullscreenElement&&document.exitFullscreen();"
                 "document.getElementById('ver').close();document.getElementById('voto-sim').classList.remove('ativa');__casa()")

        # 5. o calendário das redes
        if not celular:
            await ate(19.5, "#aba-cal")
        await em(20.6)
        await js("document.getElementById('aba-cal').click()")
        await em(21.0)
        await js("__vai(innerWidth*.5,innerHeight*.62)")
        await ate(21.9, "#cal .menu-b")
        await em(22.9)
        await js("document.querySelector('#cal .menu-b').click();__casa()")
        await em(DURA + .2)
        await manda("Page.stopScreencast")
        leitor.cancel()

    # cada quadro vale até o seguinte chegar; o vídeo vai de t0 a t0+DURA cravados
    antes = [i for i, t in enumerate(chegou) if t <= t0]
    ini = antes[-1] if antes else 0
    lista = quadros / "lista.txt"
    with open(lista, "w", encoding="utf-8") as f:
        for i in range(ini, len(chegou)):
            a = max(chegou[i], t0)
            b = min(chegou[i + 1] if i + 1 < len(chegou) else t0 + DURA * LENTO, t0 + DURA * LENTO)
            if b > a:
                f.write(f"file '{i:05d}.jpg'\nduration {(b - a) / LENTO:.5f}\n")
                ultimo = i
        f.write(f"file '{ultimo:05d}.jpg'\n")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-vf", f"fps={FPS},scale=trunc(iw/2)*2:trunc(ih/2)*2", "-t", str(DURA), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "26", "-preset", "slow", "-g", str(FPS), "-movflags", "+faststart", "-an", str(saida)], check=True)
    shutil.copy(quadros / f"{ini:05d}.jpg", saida.with_suffix(".jpg"))
    n = len(chegou) - ini
    print(n, "quadros,", round(n / DURA, 1), "por segundo,", saida.stat().st_size // 1024, "KB")

try:
    asyncio.run(main())
finally:
    proc.kill()
