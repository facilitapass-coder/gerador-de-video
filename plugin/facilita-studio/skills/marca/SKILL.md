---
name: marca
description: Cria ou altera o kit de marca do estúdio (marca.json, logo, fonte, cores, tom de voz, dicionário, frases proibidas e regras de conteúdo). Use quando o cliente pedir para trocar cor, fonte ou logo, ensinar uma regra ("nunca fale X", "sempre escreva Y assim"), ou durante a configuração inicial.
---

# Kit de marca

Tudo o que é identidade fica em `marca.json` na raiz do estúdio. As composições leem esse arquivo, então trocar uma cor aqui muda todas as peças.

## Campos

| Campo | Como preencher |
|---|---|
| `nome`, `nicho` | Nome comercial e uma frase sobre o que vende e para quem |
| `instagram`, `whatsapp`, `site` | Para chamadas e rodapés |
| `cores.primaria` | Cor institucional (fundos, textos escuros) |
| `cores.destaque` | Cor de ação: preços, selos, botões |
| `cores.clara` | Cor clara de apoio (segunda linha de títulos) |
| `cores.alerta` | Vermelho para avisos e urgência (padrão `#FF3B30`) |
| `cores.legenda_destaque` | Cor das palavras-chave nas legendas (padrão amarelo `#FFD23F`, que lê bem sobre qualquer vídeo) |
| `fonte.familia` | Uma destas do Google Fonts: Poppins, Montserrat, Inter, Roboto, Open Sans, Lato, Raleway, Bebas Neue, Oswald, Playfair Display |
| `fonte.arquivos` | Só para fonte própria: `{"400": "fontes/Marca-Regular.ttf", "700": "fontes/Marca-Bold.ttf"}`, com arquivos em `public/fontes/` |
| `logo` | `"marca/logo.png"`: arquivo em `public/marca/`. Use `null` se ainda não houver |
| `tom` | Como a marca fala, incluindo o limite de emojis |
| `palavras_destaque` | Palavras que sempre ganham cor na legenda (produto, cidade, preço) |
| `dicionario` | Grafia correta de nomes que a transcrição erra (marcas, lugares, sites como `ventusky.com`) |
| `frases_proibidas` | Expressões que nunca podem aparecer em texto, legenda ou roteiro |
| `regras` | Regras do negócio em frases curtas ("Preço sempre com 'a partir de'", "Ingressos não inclusos") |
| `cta_padrao` | Chamada final padrão |

## Como conduzir

1. Se o cliente tiver manual de marca, site ou Instagram, peça o arquivo ou o link e extraia as cores (hex), a fonte e o tom. Confirme com ele antes de gravar.
2. Logo: peça o PNG com fundo transparente e salve em `public/marca/logo.png`. Se vier com fundo branco, avise que vai aparecer um retângulo branco sobre as fotos e peça a versão transparente.
3. Regras ditas na conversa ("não pode falar grátis", "sempre parcelado por pessoa") vão para `regras` ou `frases_proibidas` **na hora**, e você confirma: "Anotei no kit de marca".
4. Depois de qualquer mudança, rode `npx tsc --noEmit` e renderize `exemplos/arte.json` para mostrar o resultado.

## Contraste

Antes de gravar as cores, confira se `destaque` sobre branco e branco sobre `primaria` têm bom contraste. Se a cor de destaque for muito clara (amarelo, bege), avise que o texto dos selos sai escuro automaticamente.
