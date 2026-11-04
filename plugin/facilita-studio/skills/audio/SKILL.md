---
name: audio
description: Limpa e nivela a voz de vídeos (abafada, baixa, com chiado, ambiente com eco), cria trilhas sem direitos autorais e ajusta o volume final para o Instagram. Use quando o cliente disser que o áudio está abafado, baixo, ruim, com barulho, ou pedir música de fundo.
---

# Áudio

Ferramenta: `python3 ferramentas/estudio.py`.

## Diagnóstico antes de mexer

```bash
python3 ferramentas/estudio.py info <arquivo>
```
`volume_medio_db` em torno de -20 a -25 é normal para celular. Em -35 ou menos, a voz está baixa (comum em gravação de tela). Para saber se está abafada, compare graves e agudos:

```bash
ffmpeg -i <arq> -af "highpass=f=250,lowpass=f=500,volumedetect" -vn -f null - 2>&1 | grep mean
ffmpeg -i <arq> -af "highpass=f=1500,lowpass=f=4000,volumedetect" -vn -f null - 2>&1 | grep mean
```
Se a faixa 250–500 Hz estiver mais de 6 dB acima da faixa 1500–4000 Hz, a voz está abafada.

## Perfis de limpeza

| Perfil | Quando usar |
|---|---|
| `normal` | Celular em ambiente comum: tira ronco, ruído leve e nivela |
| `abafado` | Voz embolada: corta 180–550 Hz, realça 2,8–4,8 kHz, devolve brilho, controla o "s" |
| `baixo` | Gravação de tela ou microfone distante: ganho maior com compressão |

```bash
python3 ferramentas/estudio.py voz <entrada> <saida.wav> --perfil abafado --duracao <segundos>
```
Sempre passe `--duracao` igual à duração da cena de vídeo correspondente, senão a voz desalinha da boca.

Depois de limpar, compare as duas faixas de novo e ouça um trecho. Se ficou metálico ou com chiado, volte para `normal`. Guarde a versão anterior com outro nome antes de substituir.

## Trilha

- Se o cliente mandar música, pergunte se tem licença para uso comercial em rede social. A biblioteca de áudio do Instagram não vale para arquivos editados fora do app.
- Sem música licenciada, gere uma:
  ```bash
  python3 ferramentas/estudio.py trilha public/pecas/<peça>/musica.wav --duracao <s> --clima suspense|animada|calma
  ```
- Volume sob a voz: 0.25 a 0.35 no `reel.json`. Pode subir no card final (`volumeFinal`).

## Volume final

Todo MP4 entregue passa por:
```bash
python3 ferramentas/estudio.py master <video.mp4>
```
Isso deixa o áudio em -14 LUFS (padrão de Instagram e TikTok) sem recodificar a imagem.
