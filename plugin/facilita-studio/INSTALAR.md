# Como instalar o Facilita Studio

## Jeito mais fácil

1. Abra o Claude Code (app do Claude, aba **Code**).
2. Arraste o arquivo **facilita-studio-vX.zip** para a conversa e escreva: **instala esse plugin**.
3. O Claude descompacta o arquivo e roda o instalador (`bash facilita-studio/instalar.sh`). Aprove quando ele pedir.
4. Se no final aparecerem dois comandos começando com `/plugin`, cole cada um no chat e envie.
5. Abra uma conversa nova e escreva: **quero começar o estúdio**.

O plugin fica guardado em `~/facilita-studio`. Não apague essa pasta.

## Jeito manual

1. Descompacte o `.zip`.
2. No terminal, rode `bash facilita-studio/instalar.sh`.
3. Siga o que ele mostrar.

## Atualizar para uma versão nova

Faça igual: arraste o `.zip` novo e escreva **instala esse plugin**. O instalador substitui a versão anterior. Depois, no seu estúdio, peça **atualize as ferramentas do estúdio**.

Suas marcas, projetos e vídeos ficam na pasta do estúdio e não são afetados.

---

### Passos do instalador (referência técnica)

1. Descompactar o `.zip` numa pasta temporária.
2. Rodar `bash <pasta>/facilita-studio/instalar.sh`. O script copia o plugin para `~/facilita-studio` e, se o comando `claude` existir, roda `claude plugin marketplace add ~/facilita-studio` e `claude plugin install facilita-studio@facilita-studio`.
3. Se o comando `claude` não existir, o script imprime dois comandos `/plugin`, que o usuário precisa colar no chat (comandos com barra só funcionam digitados pelo usuário).
