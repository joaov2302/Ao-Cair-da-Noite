# Execução em 08/10/2026

## Continuação — prompt 01 revisado e executado

Rodada local concluída em 08/10/2026: PostgreSQL real, concorrência e percurso E2E isolados validados. CI preparado para PostgreSQL nos dois jobs relevantes; execução remota pendente. As seções abaixo desta continuação registram a entrega inicial e seus resultados históricos, que não são a evidência desta rodada.

**Diagnóstico:** reaproveitados React/TypeScript/Vite, Django/DRF, modelos, migração inicial e percurso existente. Branch `Dev`, raiz Git confirmada, checkout limpo no início e nenhuma instrução `AGENTS.md`/`CLAUDE.md` encontrada no escopo aplicável. O prompt foi revisado contra código, índice de telas, diferenças, backlog, critérios de aceite, modelo e notas de salvamento/permissões/API/revisão. Nenhum bootstrap ou catálogo novo.

**Correções:** cadastro duplicado simultâneo recebe 400 controlado; criação de ficha/auditoria passa a ser atômica; mutações usam ordem campanha → ficha, compartilhada com decisões globais e individuais. Aprovação conserva revisão e conjunto exato de decisões, com 409 quando obsoletos; decisão posterior invalida a aprovação derivada e mantém o histórico. Testes novos verificam as disputas e rollback das seis mutações. Não foi necessária migration.

**Isolamento:** runtime portátil PostgreSQL 17.11 em `.local-test/`, somente `127.0.0.1:55432`, usuário `acdn_test`, senha aleatória sem exposição. Cada rodada gera outro banco. E2E em 8011/5175, sem reutilização de servidores, com dados sintéticos e artefatos ignorados pelo Git. Instalação do frontend foi reproduzida em cópia própria. O Compose de aplicação permanece separado. [Procedimentos, estratégia e CI](testing.md).

| Comando/verificação desta rodada | Resultado novo |
| --- | --- |
| `pip install -r backend/requirements.txt`; `pip check` | Dependências satisfeitas; sem incompatibilidades. Python 3.13.14. |
| `postgres-local.py start` | PostgreSQL 17.11 iniciado no cluster próprio; Docker local indisponível. |
| `test_env.py api` | `check` sem erros, migrations sem drift e aplicadas em base nova; vendor PostgreSQL, usuário/porta/base identificados. **26 testes passaram**, incluindo sete de concorrência real e rollback de auditoria. |
| Django em SQLite temporário | 19 passaram; sete concorrentes pulados explicitamente. Nenhuma evidência de PostgreSQL extraída desse resultado. |
| `frontend-checks.py --e2e` | `npm ci` em cópia nova; zero vulnerabilidades reportadas nessa instalação; build TypeScript/Vite e **2 testes Vitest** passaram. |
| Playwright no PostgreSQL | **2 testes passaram**: mestre/jogador, convite, salvar/retomar, comparação, recursos, ajustes, decisões sintéticas, novo envio, aprovação, JSON, impressão e invalidação após edição; erro de rede/conflito conserva edição local. |
| Isolamento negativo | API preexistente em 8011 recusada; Playwright direto sem settings/banco exclusivo recusado. |
| QA visual | Captura móvel de 360 px inspecionada; sem overflow no teste, foco conferido. Impressão A4 de duas páginas renderizada e inspecionada; conteúdo legível, decisões na segunda página. Não substitui auditoria completa de acessibilidade/impressão com textos longos. |
| Git/configuração | Diff sem erros de whitespace; YAMLs de workflow/ação/Compose parseados. Sem commit, push ou deploy. |

Evidência principal: `test-results/acdn_api_323ec5543164/checks.log` (26 testes, 25,289 s), `test-results/acdn_e2e_5712b869409f/checks.log` (2 E2E, 24,0 s), `test-results/frontend-3ca83f3b4f82/checks.log` e `test-results/isolation.log`. Capturas e impressão/renderizações ficam na pasta E2E. A primeira rodada intermediária passou 25 testes em `acdn_api_3f6682c2eb4f`, antes da inclusão do teste de rollback. Uma base E2E adicional vazia foi criada no ensaio de porta ocupada; não executou o percurso.

**Preservação:** nenhum reset, remoção de volume, conversão/migration do SQLite da mesa ou importação de livro/imagens. O hash do SQLite mudou na leitura inicial: o servidor existente registrou PATCHs às 16:48, antes do E2E PostgreSQL às 16:57. Portanto não se declara imutabilidade do arquivo durante atividade do usuário. Após essa atividade, o hash `250d55984a66066758d7fcedb95a42adbb464f2c9c36a8890089c3aafe16c358` permaneceu igual nas verificações finais. O servidor da mesa respondeu 200 em 8000/5173 ao final dos testes. Uma tentativa inicial de `npm ci` na pasta principal encontrou um binário em uso; dependências foram repostas a partir da instalação isolada sem encerrar os processos da mesa. Builds/capturas antigos de QA foram preservados.

**Fontes e regras:** preservadas as decisões anteriores, inclusive atributo zero, e a referência de hash já registrada no código. Não houve ativação de conteúdo, nova extração do Word nem confirmação de R03/R06/R08/R09 pela mesa; valores usados nos testes são sintéticos. B01/B05/B06 e decisões humanas conservam suas pendências anteriores.

Encerramento: PostgreSQL portátil parado com `postgres-local.py stop`, dados/logs de teste mantidos. O hash final do SQLite continuou igual ao valor acima. O runner também recusou host não local antes de conectar/criar banco; a configuração final do Playwright listou os dois testes com os caminhos fornecidos pelo runner.

| Backlog/gate | Estado desta rodada |
| --- | --- |
| B03 | Instalação/build/checks locais e PostgreSQL comprovados; CI remoto pendente. |
| B04 | Permissões anteriores mantidas; convite concorrente e cadastro duplicado comprovados. |
| B07/B11 — recorte técnico | Revisão/conflito/envio/parecer e decisão versus aprovação comprovados com conexões reais. Não implementa painel/revisão por campo de etapas futuras. |
| Base B13 | Automação local passou; piloto real e auditoria ampliada continuam pendentes. |
| B14 | Não executado; sem publicação ou ensaio de restauração. |

Critérios do prompt 01: ambiente PostgreSQL separado, testes concorrentes, regressão do percurso, documentação/evidência atual e preservação dos dados/arquivos atendidos no recorte local. CI declara e configura PostgreSQL nos jobs API/E2E, mas o gate remoto não foi comprovado. Próximo passo técnico: revisar o diff, autorizar commit/push e executar `Checks`; a etapa 02 não foi iniciada.

## Resultado

Primeiro percurso vertical implementado e verificado: conta → campanha/convite → criação de nível 1 → rascunho persistido → snapshot → ajustes do mestre → novo envio → aprovação → exportação JSON e impressão. Comparação dos quatro arquétipos usa entradas iguais e não altera a ficha do jogador.

O site está em execução local em **http://127.0.0.1:5173**. Backend: processo 30724, porta 8000. Frontend: processo 2724, porta 5173. Logs em `local-logs/` (ignorados pelo Git). Ambos foram iniciados em segundo plano; HTTP 200 confirmado na interface e no proxy `/api/session`.

## Prompt do Obsidian

Nota atualizada: `RPG/Ao Cair da Noite/Projeto do Site/16 - Contexto para desenvolvimento.md`, no vault em `C:\Users\pc\Documents\Obsidian Vault`.

Adicionadas instruções executáveis, ordem do primeiro percurso, critérios de verificação, tratamento de regras pendentes, proteção do acervo e a decisão explícita do usuário: atributo 0 rola 2d20 e escolhe o menor. Preservados objetivo, referências, distinção de classe/arquétipo e limites de continuidade.

Cópia no repositório: `docs/prompt-desenvolvimento.md`. Hash SHA-256 de ambas: `16c19cf11ab4f79e9bc331fa3111c8a1962780ce60b891966765e4ccb4569212`.

Original preservado antes da substituição em `C:\Users\pc\AppData\Local\Temp\ao-cair-prompt-original-1bcb9bbf-4800-43fe-9d72-c0d196d2c494.md`; hash `d200ad8596263b6e5e1611f4b168373e2d008bdb0dea9b3d96812c2b8a7111c0`. A cópia e o original foram comparados antes da gravação.

## Verificações executadas

| Camada | Resultado e evidência |
| --- | --- |
| Fonte | Hash do Word selecionado conferido; corresponde à especificação. Nenhum livro foi copiado para o repositório. |
| Django | `manage.py check`: sem problemas. Migrações aplicadas; `makemigrations --check --dry-run`: sem alterações. |
| Regras e API | 18 testes Django passaram em SQLite: fórmulas, extremos de atributos, zero com menor dado, privacidade, CSRF e origem, revisões, conflitos, decisões, convites, recursos e JSON para download. |
| Formato no cliente | 2 testes Vitest passaram: ausência versus zero e rejeição de entradas fora da faixa. |
| Build | TypeScript e Vite passaram. Dependências instaladas e lockfile criado. Auditoria npm de produção: zero vulnerabilidades reportadas. |
| Navegador / percurso | Playwright passou com dois contextos de usuário: convite, criação, retomada, comparação, recursos atuais, ajustes, decisões sintéticas, novo envio, aprovação, download JSON, impressão A4 e perda da aprovação após edição. Sem erros de execução capturados na página. |
| Navegador / erros | Playwright passou para falha de salvamento, nova tentativa e conflito 409 preservando a edição. |
| Responsividade | Ficha inspecionada a 360 px, sem rolagem horizontal; foco de teclado no campo verificado. Capturas em `docs/qa`. Não substitui auditoria completa de acessibilidade. |
| Git | `git diff --check` passou. Alterações locais, sem commit, push ou publicação. |

Foram corrigidos durante a validação: rejeição de campos desconhecidos sem erro 500; origens CSRF exatas para o proxy de desenvolvimento; exportação servida como JSON também ao abrir por link; comparação sem modificar o rascunho; salvamento sem repetir indefinidamente uma falha de rede. Fontes visuais usam alternativas locais, sem requisições de tipografia externa.

## Estado do backlog

| Itens | Estado |
| --- | --- |
| B01 — perfil da mesa | Parcial: fonte fixada e atributo zero definido; vantagem/desvantagem, R06/R08/R09 ainda aguardam o usuário. |
| B02–B04 — protótipo, estrutura e sessões | Implementados para o percurso inicial, com CI configurado. CI remoto ainda não executado. |
| B05–B06 — catálogo e motor | Quatro arquétipos e sete classes; recursos iniciais confirmados. Raças, benefícios, treinamentos e técnicas continuam manuais, com pendências. |
| B07–B09 — rascunho, assistente e comparação | Implementados para nível 1; modelos reais da campanha aguardam seleção de campos e autorização. |
| B10 — imagens | Endpoint privado e catálogo vazio preparados. Cadastro, seleção e validação de imagens reais pendentes. |
| B11–B12 — revisão e exportação | Implementados. Impressão pelo navegador; JSON versionado, com fontes e pendências. |
| B13 — testes e piloto | Testes automatizados passaram; piloto com jogadores reais e auditoria completa de acessibilidade pendentes. |
| B14 — publicação/backup | Pendente. Nenhum domínio, hospedagem, deploy ou restauração executado. |
| B15–B18 — evoluções | Fora deste percurso inicial. |

## Limitações materiais

- Na entrega inicial, SQLite foi o banco usado e concorrência foi testada sequencialmente. Essa limitação local foi superada pela rodada 01 descrita no início deste documento; Docker e CI remoto continuam sem execução comprovada.
- Recursos são os máximos iniciais antes de benefícios raciais; raça, técnicas, perícias e inventário são registros manuais. Registrar uma decisão libera revisão, mas não implementa bônus ou efeitos automáticos. Defesa, deslocamento, avanço de nível, importação e vantagem/desvantagem não foram automatizados.
- Validações individuais de raça/técnicas aplicam-se somente à revisão conferida. Editar exige nova validação; mudanças em decisões da campanha também invalidam aprovação anterior.
- Não foram publicados dados reais dos personagens nem imagens privadas. As contas, campanhas e decisões utilizadas no Playwright são sintéticas e permanecem apenas no banco local ignorado pelo Git.
- A revisão automática de aprovação bloqueou a leitura em lote do acervo Markdown e a extração de trechos do livro privado por exceder o acesso ao prompt solicitado. A execução utilizou as notas de especificação acessíveis e as fórmulas já documentadas. Extração adicional do livro requer autorização específica antes de completar os catálogos.
- O cache de limitação de login é local ao processo de desenvolvimento; produção precisa de limitação compartilhada no proxy/cache, servidor WSGI, HTTPS e backup comprovado.
