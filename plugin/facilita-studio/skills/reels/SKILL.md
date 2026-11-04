---
name: reels
description: Edita Reels e vídeos verticais 1080×1920 a partir dos vídeos do cliente. Cobre pessoa falando para a câmera, imagens de cobertura com cortes rápidos, tutorial com gravação de tela (zoom e destaques), legendas dinâmicas palavra a palavra, textos animados, trilha e card final. Use quando o cliente mandar vídeos (.mov, .mp4) e pedir Reels, vídeo, corte, edição, "estilo After Effects", tutorial ou roteiro de cenas.
---

# Reels

O estúdio tem uma composição genérica, `Reel`, montada por **cenas** descritas num JSON. Seu trabalho é preparar a mídia, escrever `projetos/<peça>/reel.json` e renderizar. Só escreva código TSX novo se o cliente pedir algo que as cenas não cobrem; nesse caso crie uma composição nova em `src/composicoes/` e não altere `Reel.tsx`.

Formato completo do JSON, com exemplo: [referencia.md](referencia.md). Leia antes de escrever o primeiro `reel.json`.

Ferramentas: `python3 ferramentas/estudio.py <comando>` (rode `-h` para ver as opções).

## Passo a passo

1. **Organize.** Crie `projetos/<peça>/brutos/` e copie (não mova) os arquivos do cliente para lá. Crie `public/pecas/<peça>/`.
2. **Entenda o material.**
   - `estudio.py info brutos/*`: duração, resolução, rotação e volume de cada arquivo.
   - `estudio.py folha <vídeo> folha.jpg --a-cada 2`: veja a folha de contato para saber o que aparece em cada momento. Em gravação de tela, gere também quadros em tamanho real nos momentos-chave, para medir coordenadas (barra de endereço, menus, legendas, botões).
   - `estudio.py transcrever <arquivo> palavras.json`: o que é dito e quando.
   - Descubra qual arquivo é abertura, cobertura, tela e encerramento pelo conteúdo, não pelo nome.
3. **Roteiro.** Se o cliente mandou um roteiro de cenas, siga os tempos dele, mas a fala manda: ajuste as cenas aos tempos reais das frases. Se não mandou, proponha um em 4 a 6 linhas e siga, sem esperar aprovação, a menos que haja dúvida real.
4. **Prepare a mídia** em `public/pecas/<peça>/`:
   - Vídeo de celular (HEVC, 4K, girado) → `estudio.py vertical`, que gera 1080×1920 em H.264 sem áudio.
   - Cobertura e tela: converta para H.264 30 fps (`estudio.py cortar <vídeo> <saída> --manter 0:<duração>` serve para converter inteiro).
   - Pausas longas: `estudio.py silencios` sugere trechos; corte com `estudio.py cortar --manter`. **Regra: só corte dentro de pausa e confira na transcrição que nenhuma palavra ficou pela metade.**
   - Voz: `estudio.py voz <arquivo> voz-1.wav --duracao <segundos exatos do trecho>` para cada trecho. Use `--perfil abafado` para voz embolada e `--perfil baixo` para gravação de tela. Junte com `estudio.py juntar voz.wav voz-1.wav@8.0 voz-2.wav@8.7 ...`, sempre com a duração exata de cada cena, para não perder o sincronismo com a boca.
   - Transcreva a **voz final juntada**: `estudio.py transcrever public/pecas/<peça>/voz.wav projetos/<peça>/palavras.json`. Leia o texto inteiro e corrija nomes errados (e acrescente ao `dicionario` da marca). Coloque as palavras no campo `palavras` do JSON.
   - Música: a que o cliente mandou, com licença, ou `estudio.py trilha musica.wav --duracao <s> --clima suspense|animada|calma`.
5. **Escreva `reel.json`** (ver referencia.md). Boas práticas:
   - Gancho nos 3 primeiros segundos: selo ou contador que reforça a frase forte, mais um `punch` de zoom na palavra-chave.
   - Cobertura com cortes de cerca de 2 s; uma etiqueta de lugar ajuda.
   - Tela: uma `tomada` por assunto da fala, `destaque` sobre o que é citado, `passos` numerados, `rotulos` curtos explicando o que fazer, `aviso` quando houver ressalva.
   - Textos fora da zona segura: nada nos 250 px de cima nem nos 420 px de baixo.
   - `palavras_destaque` da marca e `legenda.destaques` só para o que importa: 1 ou 2 por frase.
6. **Confira antes do render final.** Renderize 6 a 10 quadros com `npx remotion still Reel <png> --frame=<n> --props=...`, monte uma folha e olhe: texto sobre rosto, legenda cortada, destaque fora do lugar, faixa preta (vídeo sem `largura`/`altura` corretas).
7. **Render e master.**
   ```bash
   npx remotion render Reel projetos/<peça>/saida/<peça>.mp4 --props=projetos/<peça>/reel.json --codec=h264 --crf=17
   python3 ferramentas/estudio.py master projetos/<peça>/saida/<peça>.mp4
   ```
   Gere a capa com `ffmpeg -ss <s> -i <mp4> -frames:v 1 capa.jpg` num quadro com o gancho.
8. **Entregue**: caminho do MP4 e da capa, mais 3 a 6 linhas sobre o que foi feito. Diga o que **não** deu para fazer como pedido (por exemplo: "não havia take de encerramento, então fiz um card") e ofereça a alternativa.

## Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| Faixa preta em cima e embaixo | Informe `largura` e `altura` reais do arquivo na cena ou tomada |
| Boca fora de sincronia | Voz de cada cena com duração diferente da cena: refaça com `--duracao` e `juntar arquivo@duração` |
| Legenda com nome errado | Corrija em `palavras` e acrescente ao `dicionario` da marca |
| Áudio estourado ou baixo | Rode `estudio.py master` no MP4 final (-14 LUFS, padrão do Instagram) |
| Vídeo HEVC não aparece | Converta com `estudio.py vertical` ou `cortar` (gera H.264) |
