## Why

A Central de Marcação precisa importar a planilha do Google Forms pela interface e ver, linha a linha, o resultado da higienização `Forms × AGHU`; a gestão precisa editar os pesos de prioridade, as regras por exame e a matriz de incompatibilidades sem depender de mudança de código. A Fase 3 do `SPEC.md` pede isso em duas tasks do Murilo:

- **TASK-014:** `ImportacaoForms.vue` (upload CSV/XLSX + relatório de higienização/duplicidades/divergências e histórico).
- **TASK-015:** `RegrasConfiguracao.vue` (3 abas editáveis: Pesos de Prioridade, Regras por Exame e Matriz de Incompatibilidades).

Requisitos atendidos: RF003 (exibição), RF009 e CARE-RF003 (relatório de higienização).

## What Changes

- `frontend/src/stores/regras.ts`: troca o CRUD local (mock) por chamadas a `/api/regras/*`, mantendo a mesma interface da store (`prioridadesAtivas`, `salvarPrioridade`, `alternarAtivo*`, `remover*` etc.) para que a fila e o dashboard prototipados continuem funcionando. Os dados de exemplo ficam só até a primeira carga do backend (`carregarRegras()`); erros do backend (`detail` em texto ou lista `422` do Pydantic, `403` do RBAC) viram a mensagem exibida.
- `frontend/src/views/RegrasConfiguracao.vue`: carrega as regras do servidor ao abrir, troca "Restaurar Padrão Seed" (que só existia no mock) por "Recarregar do Servidor" e trata erros de pausar/ativar e remover.
- `frontend/src/types/exames.ts`: tipos do relatório de importação (`IImportacaoResumo`, `IItemImportacao`, `IRelatorioImportacao`) espelhando `src/schemas/importacoes.py`.
- `frontend/src/stores/importacoes.ts`: upload `multipart/form-data` (`POST /api/importacoes/forms`), histórico (`GET /api/importacoes`) e relatório (`GET /api/importacoes/{id}`).
- `frontend/src/views/ImportacaoForms.vue`: substitui a simulação por upload real: arrastar/selecionar arquivo com validação de extensão e tamanho (5 MB, mesmo limite do backend), contadores por status, colunas reconhecidas/ignoradas, filtro por resultado, tabela das linhas com observação e histórico de lotes.
- `frontend/public/modelo_planilha_forms.csv`: planilha de exemplo com os cabeçalhos do Forms e casos válido, duplicado, divergente e não encontrado no AGHU mock.

## Capabilities

### New Capabilities
- `frontend-importacao-regras`: telas de importação do Forms e de regras configuráveis da fila.

### Modified Capabilities
(nenhuma — os contratos `/api/importacoes` e `/api/regras` são consumidos sem mudança)

## Dependências

- **TASK-006/007 (Eduardo) — já na `master` (PR #3):** endpoints `/api/regras/*` e `/api/importacoes/*`.
- **Protótipo do frontend (Komata) — já na `master` (PR #4):** layout, rotas, menu e a tela de regras usada como base.

## Fora de escopo

- Mudanças no backend, nos interceptadores do Axios ou na autenticação.
- Fila e dashboard (continuam com os dados de exemplo do protótipo).
- Dashboard e reorganização da navegação (TASK-016).
- Testes automatizados de frontend (o projeto não tem runner no `frontend/`); a validação é `npm run build` e o fluxo manual no navegador.

## Impact

- Novos: `frontend/src/stores/importacoes.ts`, `frontend/public/modelo_planilha_forms.csv`.
- Alterados: `frontend/src/stores/regras.ts`, `frontend/src/types/exames.ts`, `frontend/src/views/ImportacaoForms.vue`, `frontend/src/views/RegrasConfiguracao.vue`.
- A fila (`FilaExames.vue`) e o dashboard seguem mockados; ligá-los à API é das TASK-013 e TASK-016.
