# Facilita Studio · plugin para Claude

Estúdio de conteúdo para redes sociais dentro do Claude. O cliente conversa com o Claude e recebe peças prontas com a marca dele:

- **Reels** com legendas dinâmicas palavra a palavra, zoom, selos, contadores, cortes rápidos e card final
- **Tutoriais com gravação de tela**: zoom no que é citado, destaques, passos numerados e avisos
- **Artes estáticas**: feed, story, quadrado, WhatsApp e anúncio
- **Áudio**: limpeza de voz abafada ou baixa, trilha sem direitos autorais e volume no padrão do Instagram
- **Roteiro e legenda**: ganchos, CTA com propósito e pauta da semana
- **Anúncios Meta**: criação pausada, ativação só com aprovação e relatórios de desempenho

Tudo roda no computador do cliente. A IA usa a assinatura ou a chave de API do **próprio cliente**.

## O que o cliente precisa

- Claude Code (app desktop, aba Code, ou terminal), com plano Pro/Max ou chave de API própria
- macOS ou Linux (Windows via WSL)
- Node 18+, Python 3, ffmpeg e whisper.cpp. A skill `comecar` confere e mostra como instalar o que faltar

## Instalação

No Claude Code:

```
/plugin marketplace add facilitapass-coder/facilita-studio
/plugin install facilita-studio@facilita-studio
```

Depois, numa conversa: **"quero começar o estúdio"**. A skill `comecar` confere o computador, cria a pasta do estúdio e monta o kit de marca.

O repositório é privado: o cliente precisa estar logado no GitHub com uma conta convidada como colaboradora (Settings → Collaborators). Para testar localmente: `/plugin marketplace add <caminho da pasta do plugin>`.

## Skills

| Skill | Para quê |
|---|---|
| `comecar` | Primeira configuração: dependências, pasta do estúdio, kit de marca |
| `marca` | Cores, fonte, logo, tom, dicionário, frases proibidas e regras |
| `reels` | Edição de Reels e tutoriais com gravação de tela |
| `arte` | Peças estáticas em qualquer formato |
| `audio` | Limpeza de voz, trilha e volume final |
| `roteiro` | Roteiro, gancho, legenda do post, CTA e pauta |
| `anuncios-meta` | Campanhas e relatórios no Meta Ads (conector do próprio cliente) |

## Estrutura

```
.claude-plugin/        plugin.json e marketplace.json
skills/                instruções que o Claude segue
scripts/
  checar-ambiente.sh   confere Node, ffmpeg, whisper e o modelo
  criar-estudio.sh     cria o estúdio do cliente a partir de modelo/
  estudio.py           ferramentas de mídia (info, folha, silencios, cortar, vertical, voz, juntar, transcrever, trilha, master)
modelo/                projeto Remotion copiado para cada cliente
  marca.json           kit de marca
  src/composicoes/     Reel (por cenas) e Arte (estáticos), guiados por JSON
  exemplos/            props de exemplo
```

## Licenças e responsabilidades

- **Remotion**: gratuito para pessoas físicas e empresas com até 3 pessoas. Empresas maiores precisam da licença de empresa (remotion.pro). Avise cada cliente.
- **Fontes**: as do Google Fonts são de uso livre. Fonte própria é responsabilidade do cliente.
- **Música**: só trilhas geradas pelo `estudio.py trilha` ou com licença comercial do cliente.
- **Meta Ads**: cada cliente usa o próprio conector. Publicar e ativar sempre exige aprovação dele.

## Versão

0.1.0 · piloto
