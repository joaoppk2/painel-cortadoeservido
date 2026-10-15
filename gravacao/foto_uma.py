"""Uma foto em tempo real pelo protocolo do Chrome: url, arquivo, largura, altura, espera e, se quiser, um JS antes."""
import asyncio, base64, json, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
import websockets

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
url, saida, larg, alt, espera = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
js = sys.argv[6] if len(sys.argv) > 6 else ""
porta = 9378
perfil = tempfile.mkdtemp(prefix="cdp")
proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", f"--remote-debugging-port={porta}",
                         f"--user-data-dir={perfil}", "--remote-allow-origins=*", "--autoplay-policy=no-user-gesture-required",
                         "about:blank"], stderr=subprocess.DEVNULL)


async def main():
    for _ in range(40):
        try:
            abas = json.load(urllib.request.urlopen(f"http://127.0.0.1:{porta}/json"))
            break
        except Exception:
            time.sleep(.25)
    ws_url = [a for a in abas if a["type"] == "page"][0]["webSocketDebuggerUrl"]
    async with websockets.connect(ws_url, max_size=None) as ws:
        n = 0

        async def manda(metodo, **params):
            nonlocal n
            n += 1
            await ws.send(json.dumps({"id": n, "method": metodo, "params": params}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == n:
                    return r.get("result", {})

        await manda("Emulation.setDeviceMetricsOverride", width=larg, height=alt, deviceScaleFactor=2 if larg < 600 else 1,
                    mobile=larg < 600)
        await manda("Page.enable")
        await manda("Page.navigate", url=url)
        await asyncio.sleep(espera)
        if js:
            r = await manda("Runtime.evaluate", expression=js, returnByValue=True)
            print(json.dumps(r.get("result", {}).get("value"), ensure_ascii=False)[:3000])
            await asyncio.sleep(3)
        r = await manda("Page.captureScreenshot", format="png")
        saida.write_bytes(base64.b64decode(r["data"]))

try:
    asyncio.run(main())
finally:
    proc.kill()
