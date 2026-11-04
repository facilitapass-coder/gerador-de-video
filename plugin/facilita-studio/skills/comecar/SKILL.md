---
name: comecar
description: Configura o Facilita Studio pela primeira vez. Confere o computador (Node, ffmpeg, whisper), cria a pasta do estúdio e monta o kit de marca conversando com o cliente. Use quando o cliente instalar o plugin, disser "começar", "configurar", "instalar o estúdio", ou quando não existir marca.json na pasta atual.
---

# Começar o estúdio

Objetivo: em uma conversa, deixar o cliente com um estúdio funcionando e a marca configurada, pronto para pedir o primeiro Reels ou a primeira arte.

A pasta do plugin fica dois níveis acima da pasta desta skill (`<pasta desta skill>/../..`). Chame-a de `PLUGIN` nos comandos abaixo.

## 1. Conferir o computador

```bash
bash "$PLUGIN/scripts/checar-ambiente.sh"
```

- Para cada item com ❌, mostre o comando de instalação que o script sugere e **peça autorização antes de rodar**. Instalações com `brew` ou `winget` podem pedir a senha do computador: nesse caso, peça para o próprio cliente rodar no terminal dele.
- O modelo do whisper tem cerca de 466 MB e vem do Hugging Face. Diga o nome, a origem e o tamanho e **só baixe com o "sim" do cliente**.
- Sem whisper o estúdio funciona, mas os Reels saem sem legenda automática. Avise.

## 2. Criar o estúdio

Pergunte onde criar (sugestão: `~/Estudio-<marca>`), depois rode:

```bash
bash "$PLUGIN/scripts/criar-estudio.sh" "<pasta>"
```

O script copia o modelo, instala o Remotion e copia `ferramentas/estudio.py`. Daí em diante, trabalhe **dentro dessa pasta**. Se o cliente abriu o Claude em outra pasta, diga para abrir o estúdio como pasta de trabalho.

Avise uma vez sobre a licença: o Remotion é gratuito para pessoas físicas e empresas com até 3 pessoas. Empresas maiores precisam da licença de empresa em remotion.pro.

## 3. Montar o kit de marca

Siga a skill `marca`. No mínimo: nome, nicho, cores, fonte, logo, tom de voz, Instagram e WhatsApp. Peça o logo em PNG com fundo transparente.

## 4. Primeira peça de teste

Renderize a arte de exemplo com a marca do cliente para provar que está tudo certo:

```bash
npx remotion still Arte projetos/teste/arte-teste.png --props=exemplos/arte.json
```

Mostre a imagem. Depois explique em 4 linhas o que dá para pedir:
- "Faz um Reels com esse vídeo" (fala, cortes, legendas, efeitos)
- "Faz um tutorial com essa gravação de tela"
- "Cria uma arte de oferta / post / story / imagem para o grupo"
- "Escreve o roteiro e a legenda do post"

## Atualizar um estúdio existente

Se `marca.json` já existe, não recrie nada. Para trazer a versão nova das ferramentas depois de atualizar o plugin, copie `$PLUGIN/scripts/estudio.py` para `ferramentas/`. As composições em `src/` só são atualizadas se o cliente pedir, porque ele pode ter personalizado.
