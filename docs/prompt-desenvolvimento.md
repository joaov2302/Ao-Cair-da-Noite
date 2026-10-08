# Contexto para desenvolvimento

## Objetivo que deve ser preservado

Implementar o site de Ao Cair da Noite com criação guiada da ficha, acompanhamento do mestre e comparação dos quatro arquétipos utilizando personagens da campanha como referência. O planejamento foi solicitado pelo usuário e organizado no Obsidian.

## Leia em ordem

[[00 - Projeto do site]] → [[01 - Escopo do site]] → [[07 - Decisões de regras pendentes]] → [[06 - Motor de regras]] → [[04 - Tecnologias e arquitetura]] → [[05 - Modelo de dados]] → [[12 - Backlog de implementação]] → [[13 - Validação e critérios de aceite]].

## Prompt de execução revisado em 08/10/2026

Execute no repositório `C:\Users\pc\Documents\GitHub\Ao-Cair-da-Noite`, preservando alterações existentes. Inspecione README, instruções locais e estado do Git antes de editar. O repositório inicialmente contém apenas README e licença.

1. Preserve React + TypeScript + Vite no cliente, CSS nativo e Django 5.2 LTS + Django REST Framework no servidor. Use PostgreSQL na configuração de produção. SQLite é permitido somente no desenvolvimento; registre qual banco foi realmente testado. Instale dependências num ambiente virtual local e mantenha arquivos de lock.
2. Entregue primeiro o percurso verificável: criar conta/entrar → criar campanha ou aceitar convite → criar Guerreiro nível 1 → salvar e retomar rascunho → enviar snapshot → revisão do mestre → impressão e JSON versionado. Estenda a comparação aos quatro arquétipos e mantenha classe e arquétipo separados.
3. Calcule no servidor somente regras confirmadas: distribuição base de cinco atributos inteiros entre 0 e 3, soma máxima 9; recursos iniciais documentados; rolagem de atributo 0 com 2d20 e menor resultado, conforme decisão explícita do usuário em 08/10/2026. Essa decisão não define vantagem/desvantagem. Não infira bônus raciais, treinamento, defesa, evolução ou elegibilidade de técnicas.
4. Solicite as definições restantes de R03/R06/R08/R09. Continue construindo o que independe delas. Registre escolha manual como pendente, com motivo e origem; somente o mestre da campanha registra decisões. Uma interpretação não resolvida impede aprovação, sem impedir salvar o rascunho.
5. Separe PV/PE/sanidade atuais dos máximos. Revisão pertence ao snapshot exato; editar a ficha ou mudar decisões invalida a aprovação. Detecte conflitos de edição com HTTP 409, preservando a edição no navegador. Proteja sessões, CSRF inclusive no login e permissões por campanha/objeto.
6. Não copie o acervo privado nem livros, capturas ou tokens para Git, public ou static. Fixe o hash da fonte: `35233f337911babbb8814687c7729cf6da3649fa58acd64f4ff82868baebdd42`. A biblioteca começa vazia, até seleção e autorização explícitas de imagens e campos de personagens. Modelos da campanha ficam para curadoria; a comparação inicial usa apenas regras e mesmas entradas.
7. Use português e a direção visual de [[10 - Telas e experiência]]: papel marfim, carvão, vinho, jade e glicínias; campos claros, foco visível, responsividade e impressão clara. Inclua carregamento, falha de rede, sessão expirada, catálogo vazio e conflito.
8. Valide fórmulas, atributo zero, separação de recursos, snapshots, conflitos, CSRF e isolamento entre usuários/campanhas. Execute build TypeScript, testes Django e percurso no navegador em desktop e 360 px. Prepare CI e instruções reproduzíveis. Não marque PostgreSQL, piloto com jogadores, backup ou publicação como validados sem evidência concreta.
9. Registre entregas e limitações em `docs/execucao.md`. Não publique automaticamente: domínio, hospedagem, conteúdo liberado e piloto ainda exigem decisões específicas. B01 permanece parcial enquanto as definições da mesa estiverem pendentes; B14 permanece pendente até publicação autorizada e restauração comprovada.

## Regras de continuidade

- O usuário definiu Ao Cair da Noite.docx como fonte principal. O perfil atual adapta Ordem Paranormal e usa cinco atributos.
- A distribuição de cinco atributos está em uma imagem no Word: a soma base é 9 antes de benefícios, com mínimo 0 e máximo 3. Soma incompleta continua como rascunho; a obrigação de gastar todos os pontos é R09.
- Modelos atuais de nível 10 nas capturas: Guerreiro/Kylan, Lutador/Arashi, Sensitivo/Radan e Suporte/Yui. A exposição depende de seleção explícita de campos e imagens.
- Classes e arquétipos são campos distintos.
- Preservar origem e decisão de mestre em cada bônus e exceção.
- Recursos máximos e recursos atuais são campos diferentes.
- Conteúdo desta pasta é privado. Liberar somente a seleção de fontes e imagens feita para o site.
- Não inferir regras de D&D nem de outro manual apenas pela ambientação Demon Slayer.
- Atributo 0: rolar dois dados e pegar o menor valor, decisão explícita recebida em 08/10/2026. Vantagem/desvantagem ainda não foi definida.

## Materiais de apoio

`Dados/arquetipos.json`: fórmulas conferidas no Word, seções do Word e modelos atuais de referência; interpretações pendentes sinalizadas. Não publicar o arquivo inteiro sem curadoria.

`Dados/personagens.json`: catálogo dos oito personagens atuais e referência à transcrição do CRIS.

`Contexto/manifesto-acervo.json`: hashes, origem, destino e dimensões dos materiais copiados.

Templates disponíveis: [[Template - Ficha guiada]], [[Template - Comparação de arquétipo]] e [[Template - Decisão de regra]].

`Dados/cris-fichas.json` registra somente campos visíveis das capturas. Nenhum login foi realizado; o usuário preferiu fornecer as imagens. Ver [[18 - Livro Word e hierarquia de fontes]].

Modelo preenchível e especificação de campos: [[19 - Modelo de ficha e revisão do planejamento]].

Recomeçar pelo percurso vertical do backlog; resolver as interpretações pendentes antes de automatizar as regras afetadas. O estado de execução atualizado pertence ao relatório do repositório; documentação de planejamento não prova uma implementação ou aprovação.
