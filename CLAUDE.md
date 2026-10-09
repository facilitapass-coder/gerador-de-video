# Facilita Studio: notas para o Claude

Ferramenta local da Facilita Pass (Python + ffmpeg + Playwright). Textos de interface, mensagens e nomes em português.

## Fluxo de um Reels quando o Richard manda clips e roteiro
1. `facilita importar` e `facilita analisar` nos clips; abra as folhas de contato (`saida/analise/*/..._folha.jpg`).
2. Escreva/atualize o `clips.yaml` descrevendo o que aparece em cada clip (e trechos com tempo). Pergunte a origem se não foi dita: sem origem o clip é recusado.
3. `facilita cobertura` e mostre o mapa ao Richard **antes** de montar, com a lista do que falta gravar.
4. `facilita montar --previa`, depois o final. Relate as medidas do manifesto (duração, voz acima da música) e os avisos.

## Regras que não podem ser contornadas
- Nunca altere arquivos de origem; saídas só em `saida/`.
- Não invente fatos de hotel, quarto ou prato: só site oficial ou o que o Richard disse. Sem fonte → "(a confirmar)".
- Não baixe arquivos da internet sem aprovação do Richard (nome, origem, tamanho).
- Não use imagem por IA (decisão aberta, P1).
- Chaves de serviços externos só em `.env` (fora do git).

## Desenvolvimento
- `pytest` roda tudo (~1 min). Testes de imagem precisam de Chromium (`CHROMIUM_PATH` ou `playwright install chromium`).
- Marca e parâmetros ficam em `marca/marca.yaml`; não espalhe cores ou limites pelo código.
- Modelos de imagem: `facilita_studio/imagens/modelos/*.html` (Jinja2, estendem `base.html`).
