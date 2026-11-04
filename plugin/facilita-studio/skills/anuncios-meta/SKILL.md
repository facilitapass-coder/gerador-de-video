---
name: anuncios-meta
description: Cria, publica e acompanha campanhas de anúncios no Facebook e Instagram (Meta Ads) com os criativos do estúdio, usando o conector Meta Ads do próprio cliente. Também faz relatórios de gasto e desempenho e sugere ajustes de orçamento. Use quando o cliente pedir anúncio, campanha, impulsionar, tráfego pago, relatório de anúncios, orçamento ou "como estão os anúncios".
---

# Anúncios Meta

Funciona com o **conector Meta Ads** ligado na conta Claude do cliente (Configurações → Conectores). Cada cliente conecta a própria conta: o estúdio nunca usa token de outra pessoa. Se as ferramentas `ads_*` não aparecerem, explique como conectar e pare.

## Antes de criar qualquer coisa

1. Liste as contas de anúncio (`ads_get_ad_accounts`) e **pergunte em qual publicar**, mostrando nome e ID. Grave a escolha em `marca.json` → `regras` (ex.: "Anúncios só na conta X (ID ...)") e confira sempre antes de cada criação.
2. Confirme a página do Facebook e o Instagram ligados à conta.
3. Defina com o cliente: objetivo (mensagens no WhatsApp, tráfego, alcance), orçamento diário, público (cidade/raio, idade) e por quanto tempo.

## Criar

- Crie tudo **pausado**: campanha → conjunto → criativo → anúncio. Mostre um resumo (conta, objetivo, orçamento, público, criativo, texto) e **só ative com um "pode ativar" explícito** do cliente. A aprovação vale para aquela campanha, não para as próximas.
- Use criativos do estúdio (`arte` ou `reels`). Mande imagem por `image_hash` **ou** por URL, nunca os dois juntos.
- Para WhatsApp: CTA `WHATSAPP_MESSAGE`, destino `WHATSAPP`, otimização para conversas.
- Não invente IDs de interesse: busque pela ferramenta ou use público aberto com localização e idade.
- Não marque declarações em nome do cliente (ex.: conteúdo gerado por IA, categoria especial); pergunte.
- Mudar o orçamento de uma campanha ativa pode pausá-la. Confira o status depois e reative só com o "sim" do cliente.

## Acompanhar

Regras para avaliar (salvo se o cliente definir outras):
- **Fase de aprendizado:** não julgue antes de cerca de R$ 40 gastos ou 3 dias.
- **Custo por resultado** (conversa, clique): quanto menor, melhor o criativo. Sugira pausar o que estiver 50% ou mais acima do melhor anúncio do mesmo conjunto.
- **CTR abaixo de 0,8%:** criativo fraco; sugira nova arte ou novo gancho.
- **Frequência acima de 3:** público saturado; troque o criativo ou amplie o público.
- **Escala:** aumente no máximo 20% por vez, no anúncio que está melhor.
- **Orçamento mensal:** projete o gasto do mês (gasto até hoje + diário × dias restantes) e avise se passar do teto combinado.

Relatório: tabela com campanha, gasto, resultados, custo por resultado, CTR e frequência, seguida de 3 a 5 recomendações objetivas. Salve em `projetos/anuncios/relatorios/AAAA-MM-DD.md`.

Se o cliente quiser acompanhamento diário, ofereça criar uma tarefa agendada que **só lê e relata**, sem alterar nada na conta.
