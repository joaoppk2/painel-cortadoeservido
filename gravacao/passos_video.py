"""Corta os vídeos do topo em trechos, um por passo, e troca as fotos dos passos por eles nas duas páginas."""
import re, subprocess
from pathlib import Path

aqui = Path(__file__).parent
site = Path.home() / "Developer/cortadoeservido-site"
FFMPEG = str(next(Path.home().glob("AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/*/bin/ffmpeg.exe")))
# trecho: (vídeo de origem, começo, fim, largura, altura)
TRECHOS = {"passo-link-pc": ("demo-pc", 0, 8.2, 1280, 800), "passo-fila-celular": ("demo-cel", 4.6, 10.7, 412, 856),
           "passo-aprovar-celular": ("demo-cel", 10.7, 19.0, 412, 856), "passo-calendario-pc": ("demo-pc", 19.3, 24, 1280, 800)}
for nome, (origem, a, b, _, _) in TRECHOS.items():
    mp4 = site / "videos" / f"{nome}.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", str(a), "-to", str(b), "-i", str(aqui / f"{origem}.mp4"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "25", "-preset", "slow", "-g", "60",
                    "-movflags", "+faststart", "-an", str(mp4)], check=True)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", str((b - a) * .6), "-i", str(mp4), "-frames:v", "1",
                    "-q:v", "4", str(mp4.with_suffix(".jpg"))], check=True)
    print(nome, mp4.stat().st_size // 1024, "KB")

FOTO = {"painel.html": {"producao-pc": "passo-link-pc", "producao-celular": "passo-fila-celular",
                        "cortes-celular": "passo-aprovar-celular", "calendario-pc": "passo-calendario-pc"},
        "painel-vendas.html": {"producao-pc": "passo-link-pc", "cortes-celular": "passo-aprovar-celular",
                               "calendario-pc": "passo-calendario-pc"}}
padrao = re.compile(r'(<div class="foto[^"]*"><div class="(?:janela|celular)">)<img src="fotos/([\w-]+)\.png" alt="([^"]*)"[^>]*>')
for pagina, mapa in FOTO.items():
    p = site / pagina
    t = p.read_text(encoding="utf-8")

    def troca(m):
        v = mapa[m[2]]
        _, _, _, w, h = TRECHOS[v]
        return (f'{m[1]}<video class="rola" src="videos/{v}.mp4" poster="videos/{v}.jpg" width="{w}" height="{h}" '
                f'muted loop playsinline preload="none" aria-label="{m[3]}"></video>')

    t, n = padrao.subn(troca, t)
    assert n == len(mapa), (pagina, n)
    p.write_text(t, encoding="utf-8", newline="\n")
    print(pagina, n, "passos")
