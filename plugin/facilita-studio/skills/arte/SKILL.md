---
name: arte
description: Cria peças estáticas com a marca aplicada (post de feed 1080×1350, story 1080×1920, quadrado 1080×1080, imagem para grupo de WhatsApp, anúncio estático) a partir de fotos reais do cliente. Use quando o cliente pedir arte, imagem, post, story, banner, anúncio estático, promoção, oferta ou capa.
---

# Arte estática

A composição `Arte` monta a peça a partir de `projetos/<peça>/arte.json`. Renderize com:

```bash
npx remotion still Arte projetos/<peça>/saida/<nome>.png --props=projetos/<peça>/arte.json
```
Para JPG (WhatsApp, anúncio), troque a extensão para `.jpg`.

## Campos de `arte.json`

| Campo | Uso |
|---|---|
| `largura`, `altura` | 1080×1350 feed · 1080×1920 story/reels · 1080×1080 quadrado |
| `foto`, `focoY` | Foto em `public/pecas/<peça>/` e posição vertical (0 = topo, 100 = base) |
| `etiqueta` | Pílula colorida no topo ("ORLANDO · FEV A MAI 2027", "SOMENTE HOJE · 20/10") |
| `etiquetaDireita` | Pílula com contorno à direita ("Estoque limitado") |
| `titulo`, `titulo2` | Título em duas linhas, a segunda na cor clara |
| `destaqueGrande` | `{valor, sufixo?, legenda?}`: número gigante ("7%" + "OFF") |
| `card` | `{linha1?, prefixo?, valor, linha2?, linha3?}`: card branco de preço |
| `chamada` | Faixa branca com seta ("Chama a gente e garanta o seu") |
| `rodape` | Letras miúdas; use `\n` para quebrar linha |
| `logo` | `false` para esconder o logo (padrão: aparece se a marca tiver logo) |
| `corDestaque` | Troca a cor de destaque só nesta peça |

## Regras

- **Foto real do cliente.** Converta HEIC com `sips -s format jpeg x.HEIC --out x.jpg` (Mac) ou `ffmpeg -i x.HEIC x.jpg`. Não gere fotos com IA sem o cliente pedir.
- **Preço:** use só valores informados pelo cliente, sempre com "a partir de" quando puder variar. Parcela por pessoa chama mais atenção que o total; deixe o total e as condições no rodapé.
- **Regras da marca:** confira `frases_proibidas` e `regras` em `marca.json` antes de escrever qualquer texto.
- **Vários formatos:** gere feed e story da mesma peça quando for anúncio. No story, nada importante nos 250 px de cima nem nos 420 px de baixo (a composição já respeita isso).
- **Variações:** para testar criativos, faça 2 ou 3 versões trocando a foto ou o título, não só a cor.
- Mostre a imagem pronta e, se ficar texto sobre um rosto ou sobre algo importante da foto, ajuste `focoY` antes de entregar.

## Precisa de algo diferente?

Se o layout pedido não cabe nesses campos (colagem, várias fotos, carrossel com várias telas), crie uma composição nova em `src/composicoes/` com `largura`/`altura` via `calculateMetadata`, usando `COR`, `FONTE` e `MARCA` de `src/marca.ts`, e registre em `src/Root.tsx`. Não altere `Arte.tsx`.
