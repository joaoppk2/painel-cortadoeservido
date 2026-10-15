"""Grava um vídeo curto por recurso do Painel (radar, fila, refazer, regras, números, avisos, ideias, grade, corte
tocando), a 60 quadros por segundo, sem mudar nada na produção: todo envio que não seja leitura fica bloqueado nesta
janela, nenhum pedido é feito e nenhuma decisão é gravada. Uso: grava_cenas.py <pasta de saída> [cena ...]"""
import asyncio, base64, json, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
import websockets

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
FFMPEG = str(next(Path.home().glob("AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/*/bin/ffmpeg.exe")))
destino = Path(sys.argv[1])
LARG, ALT, LENTO, FPS, porta = 1280, 800, 2.5, 60, 9381
perfil = tempfile.mkdtemp(prefix="cenas")
proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", f"--remote-debugging-port={porta}",
                         f"--user-data-dir={perfil}", "--remote-allow-origins=*", "--mute-audio",
                         "--autoplay-policy=no-user-gesture-required", "about:blank"], stderr=subprocess.DEVNULL)

ANTES = r"""
try{localStorage.clear();history.scrollRestoration='manual';sessionStorage.setItem('abriu','1')}catch{}
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
 #id-lista{display:none}`;
 document.head.append(s);
 const p=document.createElement('div');p.id='__p';
 p.innerHTML='<i></i><svg width="26" height="26" viewBox="0 0 24 24"><path d="M4 2l15 11h-7l-3 8z" fill="#fff" stroke="#000" stroke-width="1.4" stroke-linejoin="round"/></svg>';
 document.body.append(p);
 const visivel=sel=>[...document.querySelectorAll(sel)].find(e=>e.getClientRects().length);
 window.__casa=()=>{(document.querySelector('dialog[open]')||document.body).append(p)};
 window.__vai=(x,y)=>{__casa();p.style.transform=`translate(${x}px,${y}px)`};
 window.__ate=sel=>{const e=visivel(sel);if(!e)return false;
  const r=e.getBoundingClientRect();__vai(r.left+Math.min(r.width*.5,420),r.top+r.height*.55);return true};
 window.__toca=()=>{p.classList.remove('toca');void p.offsetWidth;p.classList.add('toca')};
 window.__clica=sel=>{const e=visivel(sel);if(e)e.click();return !!e};
 const quem=()=>[document.getElementById('tela'),document.scrollingElement].find(e=>e&&e.scrollHeight>e.clientHeight+10)||document.scrollingElement;
 // rolagem própria (a do navegador não acompanha a câmera lenta): alvo é um seletor (leva ao topo) ou um tanto em px
 window.__rola=(alvo,ms)=>{const q=quem(), de=q.scrollTop;
  const ate=typeof alvo=='number'?de+alvo:de+visivel(alvo).getBoundingClientRect().top-90, t0=performance.now();
  const passo=t=>{const k=Math.min(1,(t-t0)/ms), s=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;q.scrollTop=de+(ate-de)*s;if(k<1)requestAnimationFrame(passo)};
  requestAnimationFrame(passo)};
 __vai(innerWidth*.6,innerHeight*.62);
 // um ponto de 2 px que muda a cada quadro: sem ele, tela parada não gera quadro e o ponteiro sai aos pulos
 const k=document.createElement('i');k.style.cssText='position:fixed;right:0;bottom:0;width:2px;height:2px;z-index:2147483646';document.body.append(k);
 let f=0;(function t(){k.style.background=(f^=1)?'#0a0a0a':'#0b0b0b';requestAnimationFrame(t)})();
})()
"""
CORTES = "document.getElementById('aba-cortes').click()"
FILA = CORTES + " >> document.querySelector('#filtro-l button[data-e=\"fila\"]').click()"
MENU = "#n-canal + .menu"
IDEIA = "Mostrar na fila a hora em que o plano reinicia"
ALERTA = "A Meta está recusando o nosso app: API access blocked. · desde 03/10 21h40"
# cena: (duração, preparo fora da gravação, [(segundo, ação, argumento)])
CENAS = {
    "radar": (6.5, "", [(.3, "rola", ("#radar", 1.1)), (1.7, "ate", "#radar .ep-r"), (2.7, "ate", "#radar .ep-r:nth-child(3)"),
                        (3.5, "rola", (330, 1.4)), (5.1, "ate", "#radar .ep-r:nth-child(6)")]),
    "fila": (6.5, "", [(.4, "ate", "#agora"), (1.8, "ate", ".pedido.agora"), (2.9, "ate", ".pedido.baixado,.pedido:nth-child(3)"),
                       (3.8, "rola", ("#lista", 1.5)), (5.4, "ate", "#lista .cab")]),
    "refazer": (7.5, CORTES, [(.4, "ate", "#grupos .corte .capa"), (1.4, "toca", ""), (1.5, "js", "__clica('#grupos .corte .capa')"),
                              (3.8, "ate", "#voto-nao"), (4.8, "toca", ""), (4.9, "js", "abreFolha('com');__casa()"),
                              (5.7, "ate", "#f-com button")]),
    "regras": (6.5, "", [(.4, "ate", MENU + " .menu-b"), (1.4, "toca", ""), (1.5, "js", f"__clica('{MENU} .menu-b')"),
                         (2.3, "ate", MENU + " .menu-l button:nth-of-type(3)"), (3.4, "ate", MENU + " .menu-l button:nth-of-type(6)"),
                         (4.5, "js", f"__clica('{MENU} .menu-b')"), (4.8, "ate", "#n-fontes")]),
    "numeros": (6.5, CORTES, [(.5, "ate", "#canal .cab"), (1.5, "toca", ""), (1.6, "js", "__clica('#canal .cab')"),
                              (2.8, "ate", "#canal svg"), (4.2, "js", "__vai(innerWidth*.75,innerHeight*.45)")]),
    "avisos": (5.5, "", [(.9, "js", f"const a=document.getElementById('meta-alerta');a.textContent={json.dumps(ALERTA)};a.removeAttribute('hidden');Object.defineProperty(a,'hidden',{{set(){{}},get(){{return false}}}});Object.defineProperty(a,'textContent',{{set(){{}}}})"),
                         (1.6, "ate", "#meta-alerta"), (3.6, "ate", "#avisos")]),
    "ideias": (7.5, "", [(.4, "ate", "#aba-ideias"), (1.4, "toca", ""), (1.5, "js", "__clica('#aba-ideias');__casa()"),
                         (2.2, "ate", "#id-texto"), (2.9, "tipo", ("id-texto", IDEIA, 2.2)), (5.6, "ate", "#id-envia")]),
    "grade": (6.5, FILA, [(.5, "ate", "#grupos .corte .capa"), (1.3, "rola", (430, 1.9)), (3.6, "ate", "#grupos .corte:nth-child(2) .capa"),
                          (4.4, "rola", (380, 1.4))]),
    "toca": (6.5, FILA, [(.3, "ate", "#grupos .corte .capa"), (1.2, "toca", ""), (1.3, "js", "__clica('#grupos .corte .capa')"),
                           (3.2, "js", "__vai(innerWidth*.78,innerHeight*.7)")]),
}


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
            if r.get("exceptionDetails"):
                print("   erro no js:", expr[:70], "->", r["exceptionDetails"].get("exception", {}).get("description", "")[:120])
            return r.get("result", {}).get("value")

        await manda("Emulation.setDeviceMetricsOverride", width=LARG, height=ALT, deviceScaleFactor=1, mobile=False)
        await manda("Page.enable")
        await manda("Animation.enable")
        await manda("Page.addScriptToEvaluateOnNewDocument", source=ANTES)

        for nome in (sys.argv[2:] or list(CENAS)):
            dura, preparo, passos = CENAS[nome]
            quadros = Path(tempfile.mkdtemp(prefix="q-" + nome))
            await manda("Animation.setPlaybackRate", playbackRate=1)
            await manda("Page.navigate", url="http://localhost:8770/")
            await asyncio.sleep(6)
            await js(PONTEIRO)
            for parte in preparo.split(" >> ") if preparo else []:
                await js(parte)
                await asyncio.sleep(1.5)
            await manda("Animation.setPlaybackRate", playbackRate=1 / LENTO)
            await js(f"(()=>{{const v=document.getElementById('vid'),r={1 / LENTO};v.defaultPlaybackRate=r;"
                     "v.addEventListener('ratechange',()=>{if(v.playbackRate!=r)v.playbackRate=r})})()")
            chegou = []

            def quadro(p, chegou=chegou, quadros=quadros):
                (quadros / f"{len(chegou):05d}.jpg").write_bytes(base64.b64decode(p["data"]))
                chegou.append(time.perf_counter())
                asyncio.get_running_loop().create_task(manda("Page.screencastFrameAck", sessionId=p["sessionId"]))

            eventos["Page.screencastFrame"] = quadro
            await manda("Page.startScreencast", format="jpeg", quality=82, maxWidth=4000, maxHeight=4000, everyNthFrame=1)
            await asyncio.sleep(.7)
            t0 = time.perf_counter()

            async def em(t):
                await asyncio.sleep(max(0, t0 + t * LENTO - time.perf_counter()))

            for t, acao, arg in passos:
                await em(t)
                if acao == "ate":
                    if not await js(f"__ate({json.dumps(arg)})"):
                        print("   não achei", arg)
                elif acao == "toca":
                    await js("__toca()")
                elif acao == "js":
                    await js(arg)
                elif acao == "rola":
                    await js(f"__rola({json.dumps(arg[0])},{arg[1] * LENTO * 1000})")
                elif acao == "tipo":
                    campo, texto, tempo = arg
                    await js(f"document.getElementById('{campo}').focus()")
                    for i in range(1, len(texto) + 1):
                        await em(t + tempo * i / len(texto))
                        await js(f"document.getElementById('{campo}').value={json.dumps(texto[:i])}")
            await em(dura + .2)
            await manda("Page.stopScreencast")
            await asyncio.sleep(.3)

            antes = [i for i, t in enumerate(chegou) if t <= t0]
            ini = antes[-1] if antes else 0
            fim = t0 + dura * LENTO
            lista = quadros / "lista.txt"
            with open(lista, "w", encoding="utf-8") as f:
                for i in range(ini, len(chegou)):
                    a, b = max(chegou[i], t0), min(chegou[i + 1] if i + 1 < len(chegou) else fim, fim)
                    if b > a:
                        f.write(f"file '{i:05d}.jpg'\nduration {(b - a) / LENTO:.5f}\n")
                        ultimo = i
                f.write(f"file '{ultimo:05d}.jpg'\n")
            mp4 = destino / f"rec-{nome}.mp4"
            subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                            "-vf", f"fps={FPS},scale=trunc(iw/2)*2:trunc(ih/2)*2", "-t", str(dura), "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", "-crf", "26", "-preset", "slow", "-g", str(FPS), "-movflags", "+faststart",
                            "-an", str(mp4)], check=True)
            subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", str(dura * .7), "-i", str(mp4), "-frames:v", "1",
                            "-q:v", "4", str(mp4.with_suffix(".jpg"))], check=True)
            print(nome, round((len(chegou) - ini) / dura), "quadros por segundo,", mp4.stat().st_size // 1024, "KB")
            shutil.rmtree(quadros, ignore_errors=True)
        leitor.cancel()

try:
    asyncio.run(main())
finally:
    proc.kill()
