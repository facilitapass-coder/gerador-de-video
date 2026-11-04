# Formato do `reel.json`

Todos os tempos estão em **segundos**. Caminhos de mídia são relativos a `public/` (ex.: `pecas/minha-peca/fala.mp4`).

- Tempos de `cenas[].de/ate`, `textos` e `palavras`: na **linha do tempo final** do vídeo.
- Tempos **dentro** de uma cena `tela` (`tomadas`, `destaques`, `passos`, `rotulos`, `aviso`): a partir do **início daquela cena**, que é o mesmo segundo do arquivo de tela preparado (quando `inicio` = 0).

## Raiz

| Campo | Tipo | Observação |
|---|---|---|
| `duracao` | número | Duração total do vídeo |
| `voz` | caminho | Voz final juntada (`estudio.py juntar`) |
| `musica` | `{arquivo, volume, volumeFinal?}` | `volume` 0.25 a 0.35 sob a voz; `volumeFinal` (ex.: 0.95) sobe na cena `final` |
| `palavras` | `[{w, i, f}]` | Saída de `estudio.py transcrever` (palavra, início, fim) |
| `legenda` | `{ativa?, topo?, topoTela?, maxPalavras?, tamanho?, destaques?}` | Padrões: topo 1330, topoTela 1350, 3 palavras, tamanho 64 |
| `cenas` | lista | Uma das 4 cenas abaixo, em ordem |
| `textos` | lista | Selos, etiquetas, títulos e contadores sobre qualquer cena |

Toda cena tem `de`, `ate` e `flash` opcional (padrão `true`: flash branco na entrada, exceto na primeira).

## Cena `fala` (pessoa falando)

```json
{ "tipo": "fala", "de": 0, "ate": 8, "video": "pecas/x/rosto.mp4", "inicio": 0, "largura": 1080, "altura": 1920, "zoom": [1.0, 1.12], "punches": [3.0] }
```
`zoom`: escala no começo e no fim (zoom suave). `punches`: segundos da linha final onde entra um "soco" de +4%.

## Cena `cobertura` (imagens com cortes rápidos)

```json
{ "tipo": "cobertura", "de": 8, "ate": 16.7, "etiqueta": "MARINGÁ · PR", "filtro": "dramatico",
  "tomadas": [ { "video": "pecas/x/broll.mp4", "inicio": 5.2, "largura": 1034, "altura": 1518 }, { "video": "pecas/x/broll.mp4", "inicio": 10.3, "largura": 1034, "altura": 1518 } ] }
```
O tempo da cena é dividido igualmente entre as tomadas. `filtro`: `dramatico` (contraste alto, menos cor) ou `natural`.

## Cena `tela` (tutorial com gravação de tela)

A gravação aparece numa janela (x 40, y 360, 1000×960) e uma "câmera" passeia por ela.

```json
{ "tipo": "tela", "de": 16.7, "ate": 70.9, "video": "pecas/x/tela.mp4", "largura": 1436, "altura": 796,
  "tomadas": [ { "t": 0, "cx": 265, "cy": 70, "s": 2.7 }, { "t": 2.6, "cx": 370, "cy": 175, "s": 2.3 } ],
  "destaques": [ { "de": 0.3, "ate": 2.6, "tipo": "ret", "x": 148, "y": 44, "w": 140, "h": 32 },
                 { "de": 25, "ate": 29, "tipo": "circ", "x": 992, "y": 732, "w": 34, "h": 34, "paraX": 612, "mover": [26.5, 27.7] } ],
  "passos": [ { "de": 0, "rotulo": "PASSO 1", "titulo": "Acesse o site" }, { "de": 40, "rotulo": "⚠️ IMPORTANTE", "titulo": "Use com responsabilidade", "alerta": true } ],
  "rotulos": [ { "de": 12, "ate": 14, "texto": "🎨 Cor = velocidade", "posicao": "topo" }, { "de": 22, "ate": 23, "texto": "💨 40 km/h", "fundo": "alerta" } ],
  "aviso": { "de": 41.2, "titulo": "⚠️ ATENÇÃO", "itens": [ { "em": 42.7, "texto": "É uma PREVISÃO" } ] } }
```

- **Coordenadas em pixels do arquivo de tela** (meça num quadro em tamanho real).
- `tomadas`: `cx`/`cy` = centro do que mostrar; `s` = zoom. Na janela de 1000×960, `s` 1.3 mostra a tela quase inteira e `s` 2.5 a 2.7 mostra um menu ou campo de perto. A troca entre tomadas leva 0,6 s com suavização, e a câmera nunca sai da tela.
- `destaques`: `ret` usa x/y do canto e w/h; `circ` usa x/y do centro e w como diâmetro. `paraX`/`paraY` + `mover` faz o destaque acompanhar algo que se move (ex.: arrastar a linha do tempo).
- `rotulos`: pílulas fixas dentro da janela. `posicao` `topo` (padrão) ou `base`.
- `aviso`: card vermelho na base da janela; cada item entra no tempo `em`.

## Cena `final`

```json
{ "tipo": "final", "de": 70.9, "ate": 74.6, "imagem": "pecas/x/rosto.jpg",
  "linhas": [ { "texto": "SALVE", "tamanho": 104 }, { "texto": "E COMPARTILHE", "cor": "legenda", "tamanho": 104 }, { "texto": "ESTE VÍDEO!", "tamanho": 72 } ],
  "icones": ["salvar", "compartilhar"], "rodape": "Mande pra quem precisa ver isso", "logo": true }
```
`icones`: `salvar`, `compartilhar`, `seguir`, `whatsapp`. `imagem` é opcional (fundo desfocado). As legendas somem nesta cena.

## `textos`

```json
[ { "de": 2.95, "ate": 8, "texto": "🌪️ TORNADO F2", "estilo": "selo", "fundo": "alerta" },
  { "de": 5, "ate": 8, "texto": "", "estilo": "contador", "posicao": "alto", "linhas": true,
    "contador": { "de": 180, "ate": 250, "sufixo": " km/h", "t0": 5.6, "t1": 7.3, "legenda": "ventos de 180 a 250 km/h" } },
  { "de": 9.75, "ate": 16.7, "texto": "SITE 100% GRATUITO", "estilo": "etiqueta", "posicao": "alto", "fundo": "legenda" } ]
```
- `estilo`: `selo` (pílula grande inclinada), `etiqueta` (pílula média), `titulo` (texto grande sem fundo), `contador` (número que conta de `de` até `ate` entre `t0` e `t1`, na linha final).
- `posicao`: `topo` (y 260), `alto` (y 390) ou `meio` (y 760). Evite `meio` sobre rosto.
- `linhas`: linhas de movimento atrás (vento, velocidade).

## Cores (`fundo`, `cor`)

`destaque`, `alerta`, `primaria`, `clara`, `branco`, `legenda` (vêm da marca) ou um hex direto (`"#22C55E"`).
