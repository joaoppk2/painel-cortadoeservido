# Painel Cortado e Servido · site

Apresentação do **Painel**, o aplicativo que cria, revisa e agenda os cortes do canal Cortado e Servido.

- Portfólio: https://joaoppk2.github.io/painel-cortadoeservido/
- Vendas: https://joaoppk2.github.io/painel-cortadoeservido/vendas.html

Publicado pelo GitHub Pages a partir do branch `main` (pasta raiz). O código do aplicativo fica no repositório
privado `youtube-shorts`.

## Arquivos

| Arquivo | O que é |
|---|---|
| `index.html` | página de portfólio |
| `vendas.html` | página de vendas |
| `painel.css`, `painel.js` | estilo e comportamento das duas páginas |
| `motion.js` | biblioteca Motion (movimento ao rolar a página) |
| `videos/` | vídeos do aplicativo em uso, gravados com os scripts de `gravacao/` |
| `gravacao/` | scripts que gravam os vídeos e as fotos do Painel |

## Gravação dos vídeos

Os scripts abrem o Chrome pelo protocolo de depuração e gravam o Painel sem mudar nada na produção: todo envio que
não seja leitura fica bloqueado na janela de gravação. Precisam do Chrome, do FFmpeg (instalado pelo winget) e do
pacote `websockets`.

| Script | Uso |
|---|---|
| `gravacao/painel_teste.py <pasta do worktree>` | sobe o Painel de um worktree na porta 8771, sem fila, downloads, radar nem avisos |
| `gravacao/grava_demo.py <saida.mp4> <largura> <altura> <escala>` | vídeo do topo: colar o link, ver a fila, aprovar, calendário |
| `gravacao/grava_cenas.py <pasta> [cena ...]` | um vídeo curto por recurso, a 60 quadros por segundo |
| `gravacao/foto_uma.py <url> <arquivo> <largura> <altura> <espera>` | uma foto da tela |
| `gravacao/passos_video.py` | histórico: ajuste de uma vez só, feito na versão antiga das páginas e já aplicado |

## Branches

- `main`: o site publicado.
- `cinema`: teste do modo cinema (`cinema.html`), ainda não decidido para a página de vendas.
