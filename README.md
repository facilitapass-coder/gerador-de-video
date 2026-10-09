# Facilita Studio

Ferramenta da Facilita Pass que transforma roteiro e clips brutos em **Reels prontos (MP4 1080×1920)** e gera
**posts, carrosséis, stories e artes de WhatsApp (PNG)** com a marca aplicada automaticamente.
Esta é a primeira versão: os requisitos P0 do escopo. Tudo roda no computador local, sem enviar vídeo para a nuvem.

## Instalação

Requisitos: Python 3.10+, ffmpeg (com ffprobe) e Chromium para o Playwright.

```bash
pip install -e .
playwright install chromium        # ou: export CHROMIUM_PATH=/caminho/do/chrome
```

Depois, uma vez:

1. Copie os arquivos da Poppins para `marca/fontes/` (ver `marca/fontes/LEIA-ME.md`).
2. Copie o logo "Laranja Principal" para `marca/logo/laranja-principal.png` e rode `facilita logo-corrigir` se precisar.
3. Confira com `facilita marca`.

## Reels: do roteiro ao MP4

```bash
facilita importar clips/                       # resolução, duração e orientação de cada arquivo
facilita analisar clips/*.mp4 narracao.wav     # quadros a cada 2 s, folha de contato, volume da voz
facilita cobertura roteiro.md --clips clips.yaml   # qual clip cobre cada bloco e o que falta gravar
facilita montar roteiro.md --clips clips.yaml --previa   # prévia rápida 540×960
facilita montar roteiro.md --clips clips.yaml            # MP4 final
facilita legenda roteiro.md                    # legenda com CTA e lembrete da e-Visa
```

- **Roteiro** (`roteiro.md`): cabeçalho com título, narração, música, CTA; um `## Bloco N · Nome` por bloco, com
  `tempo`, `imagem`, `tela`, opcionalmente `clip: arquivo.mp4 @ 0:03` e `enquadramento: centro | foco 0.3 | desfocado`,
  e o texto da narração com `[pausa 0.5s]`. Sem `tempo`, os blocos são estimados pela narração e ajustados às pausas reais.
  Exemplo completo: `exemplos/xcaret-arte/roteiro.md`.
- **Biblioteca de clips** (`clips.yaml`): descrição, tags e **origem obrigatória** de cada clip. Exemplo: `exemplos/xcaret-arte/clips.yaml`.

O que a montagem faz:

| Etapa | Como |
| --- | --- |
| Reenquadramento 9:16 | corte central, ponto de foco ajustável ou fundo desfocado |
| Corte | um segmento por bloco, no tempo da narração; corte seco ou fade |
| Áudio | voz +7 dB com redução de ruído básica; música a 12% subindo nos 2 s finais; limitador |
| Títulos | Poppins Bold, marinho com barra laranja, sempre fora das zonas da interface do Instagram |
| CTA e logo | cartão final com logo e botão laranja nos últimos 4 s, até o último quadro; 2 s de respiro depois da fala |
| Exportação | H.264, AAC, até 60 s, `saida/reels/<slug>/<slug>_reels_1080x1920_v01.mp4` |

Cada exportação grava ao lado um `.json` com o hash do roteiro, os clips usados (e origem), os parâmetros e as medidas
(duração, resolução, quanto a voz ficou acima da música). Nova montagem vira `_v02`; nada é sobrescrito.

## Imagens: posts, carrosséis, stories e WhatsApp

```bash
facilita validar exemplos/oferta-xcaret.yaml        # confere regras sem gerar
facilita imagem exemplos/oferta-xcaret.yaml --formato feed --formato story --formato whatsapp
facilita imagem exemplos/carrossel-xcaret.yaml
```

A peça é um YAML com `modelo` (`oferta`, `hotel`, `story`, `whatsapp`, `carrossel`), `campos` (título, subtítulo, CTA…),
`fotos` (com `origem`) e `oferta`. O HTML/CSS é renderizado no Chromium a 2× e reduzido para 1080×1350 (feed) ou
1080×1920 (story/WhatsApp). Para refazer uma peça, troque o texto no YAML e rode o mesmo comando: sai uma nova
versão em `saida/imagens/<peca>/v02/`.

## Regras embutidas (`marca/marca.yaml`)

- Paleta marinho `#0D2D5E`, laranja `#E8572A`, dourado `#C9992A`; fonte Poppins; logo "Laranja Principal".
- Terminologia: "Xpert Xcaret" (nunca "embaixador"), "Faixa" (não "Nível"), "Valor Fixo Contratual" (não "Salário Fixo").
- Frases proibidas e limite de emojis (tom sóbrio).
- Ofertas: aeroporto de saída explícito, validade e pagamento obrigatórios, all inclusive só com bagagem de mão,
  parcelamento sempre sobre o total do casal ("10x de R$ X por casal" + "Total R$ Y para 2 pessoas").
- Fotos, clips e música só de fonte licenciada, com a origem registrada; imagem por IA é recusada nesta versão.
- Destaque de hotel sem fonte sai marcado "(a confirmar)".
- Lembrete da e-Visa do México nas legendas e, com `aviso_evisa: true`, na última tela do carrossel.

Qualquer violação **recusa** a peça com a explicação do que corrigir.

## Experimentar sem os arquivos reais

```bash
python exemplos/gerar_amostras.py     # clips, narração, música, logo e fotos sintéticos em exemplos/amostras/
```

Os exemplos usam essas amostras. Sem a Poppins instalada, acrescente `--permitir-fonte-substituta`.

## Testes

```bash
pip install -e '.[dev]'
pytest
```

Os testes cobrem os critérios de aceite da primeira versão: MP4 1080×1920 até 60 s com CTA e logo no último quadro,
mapa de cobertura, voz acima da música, carrossel 1080×1350 na paleta da marca, recusa de oferta sem aeroporto ou
validade e originais intocados.

## Fora desta versão

P1/P2 do escopo: legendas queimadas por transcrição, ajuste por pedido, selo Xpert Xcaret, capa, variações de layout,
imagem por IA, fila por planilha e agenda. Publicação automática, voz, vídeo horizontal e CRM estão fora do escopo.
