"""Sobe o painel de um worktree na porta 8771 só para olhar a tela: nada de fila, pedidos, downloads, radar, coleta
das redes ou avisos (tudo trocado por funções vazias). Uso: painel_teste.py <pasta do worktree>"""
import sys, time
from pathlib import Path

raiz = Path(sys.argv[1])
sys.path.insert(0, str(raiz / "aplicativo"))
sys.path.insert(0, str(raiz / "shorts"))
import painel


def parado(*a, **k):
    while True:
        time.sleep(3600)


painel.PORTA = 8771
for nome in ("produz", "baixa_fila", "radar_sozinho", "coleta_views", "vigia_meta", "vigia_claude", "vigia"):
    setattr(painel, nome, parado)
painel.avisa_celular = lambda *a, **k: []
sys.argv = ["painel.py", "--servidor"]
painel.main()
