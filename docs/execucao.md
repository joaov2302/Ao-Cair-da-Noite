# Execução em 08/10/2026

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

- SQLite foi o banco realmente usado nesta máquina. O Docker não estava ativo; PostgreSQL está configurado no compose/CI, sem validação local ou remota nesta execução. Controle de revisão foi testado sequencialmente; concorrência real deve ser verificada em PostgreSQL.
- Recursos são os máximos iniciais antes de benefícios raciais; raça, técnicas, perícias e inventário são registros manuais. Registrar uma decisão libera revisão, mas não implementa bônus ou efeitos automáticos. Defesa, deslocamento, avanço de nível, importação e vantagem/desvantagem não foram automatizados.
- Validações individuais de raça/técnicas aplicam-se somente à revisão conferida. Editar exige nova validação; mudanças em decisões da campanha também invalidam aprovação anterior.
- Não foram publicados dados reais dos personagens nem imagens privadas. As contas, campanhas e decisões utilizadas no Playwright são sintéticas e permanecem apenas no banco local ignorado pelo Git.
- A revisão automática de aprovação bloqueou a leitura em lote do acervo Markdown e a extração de trechos do livro privado por exceder o acesso ao prompt solicitado. A execução utilizou as notas de especificação acessíveis e as fórmulas já documentadas. Extração adicional do livro requer autorização específica antes de completar os catálogos.
- O cache de limitação de login é local ao processo de desenvolvimento; produção precisa de limitação compartilhada no proxy/cache, servidor WSGI, HTTPS e backup comprovado.
