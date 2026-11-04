# Como instalar o Facilita Studio

Leva uns 10 minutos na primeira vez.

## 1. Guarde a pasta do plugin num lugar fixo

Descompacte o arquivo `.zip` e mova a pasta **facilita-studio** para a sua pasta pessoal, por exemplo:

- Mac: `/Users/<seu-usuário>/facilita-studio`
- Linux: `/home/<seu-usuário>/facilita-studio`

**Não apague nem mova essa pasta depois**: o Claude usa o plugin direto dela.

## 2. Instale no Claude Code

Abra o Claude Code (app do Claude, aba **Code**, ou `claude` no terminal) e envie, trocando o caminho pelo da sua pasta:

```
/plugin marketplace add /Users/<seu-usuário>/facilita-studio
/plugin install facilita-studio@facilita-studio
```

Se pedir, reinicie a conversa.

## 3. Comece

Escreva na conversa: **quero começar o estúdio**

O Claude vai conferir o computador (Node, Python, ffmpeg e whisper), mostrar o que falta instalar, criar a pasta do seu estúdio e montar a sua marca com você.

## Atualizar para uma versão nova

1. Descompacte a versão nova por cima da pasta antiga (mesmo lugar, mesmo nome).
2. No Claude Code: `/plugin marketplace update facilita-studio`
3. No seu estúdio, peça: **atualize as ferramentas do estúdio**

Suas marcas, projetos e vídeos ficam na pasta do estúdio e não são afetados.
