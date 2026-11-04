# Estúdio de conteúdo (Facilita Studio)

Esta pasta é o estúdio de criação desta marca. O Claude produz aqui Reels, Stories, posts e artes com a marca aplicada automaticamente.

## Onde fica cada coisa

| Pasta / arquivo | O que é |
|---|---|
| `marca.json` | Kit de marca: cores, fonte, logo, tom de voz, dicionário, frases proibidas, regras |
| `public/marca/` | Logo (PNG com fundo transparente) e selos |
| `public/fontes/` | Fonte própria da marca, se não for do Google Fonts |
| `projetos/<peça>/brutos/` | Arquivos originais enviados pelo cliente (nunca alterar) |
| `projetos/<peça>/reel.json` ou `arte.json` | Roteiro da peça em formato de props |
| `projetos/<peça>/saida/` | MP4, PNG, JPG finais e a legenda do post |
| `public/pecas/<peça>/` | Mídia preparada (cortada, convertida, voz limpa) usada no render |
| `ferramentas/estudio.py` | Ferramentas de mídia: `python3 ferramentas/estudio.py -h` |
| `src/` | Composições Remotion `Reel` e `Arte` (genéricas, guiadas por JSON) |

## Regras que valem sempre

1. **Leia `marca.json` antes de qualquer peça**: cores, fonte, logo, tom, `frases_proibidas` e `regras` são obrigatórios.
2. **Material real**: use as fotos e os vídeos do cliente. Não gere imagens ou vídeos com IA, a menos que o cliente peça.
3. **Não invente fatos**: preço, condição, prazo, o que está incluso e dados técnicos saem do cliente. Se faltar, pergunte.
4. **Nunca corte no meio de uma palavra ou frase.** Corte só dentro de pausas e confira a primeira e a última palavra de cada trecho na transcrição.
5. **Legendas**: corrija a grafia de nomes próprios com o `dicionario` da marca e confira a transcrição inteira antes do render.
6. **Zona segura do Instagram (1080×1920)**: nada importante nos 250 px de cima nem nos 420 px de baixo.
7. **Publicar, enviar ou ativar anúncios exige aprovação explícita do cliente a cada vez.** Gere o arquivo e mostre; não publique por conta própria.
8. **Música**: só trilhas sintetizadas por `estudio.py trilha` ou com licença comercial informada pelo cliente.
9. Entregue sempre o caminho do arquivo final e um resumo curto do que foi feito.

## Comandos de render

```bash
npx remotion render Reel projetos/<peça>/saida/<peça>.mp4 --props=projetos/<peça>/reel.json --codec=h264 --crf=17
python3 ferramentas/estudio.py master projetos/<peça>/saida/<peça>.mp4
npx remotion still Arte projetos/<peça>/saida/<peça>.png --props=projetos/<peça>/arte.json
npx remotion still Reel projetos/<peça>/saida/teste.png --frame=150 --props=projetos/<peça>/reel.json   # conferir um quadro
```
