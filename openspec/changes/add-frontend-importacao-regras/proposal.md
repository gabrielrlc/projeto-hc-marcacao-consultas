## Why

A Central de Marcação precisa importar a planilha do Google Forms pela interface e ver, linha a linha, o resultado da higienização `Forms × AGHU`; a gestão precisa editar os pesos de prioridade, as regras por exame e a matriz de incompatibilidades sem depender de mudança de código. A Fase 3 do `SPEC.md` pede isso em duas tasks do Murilo:

- **TASK-014:** `ImportacaoForms.vue` (upload CSV/XLSX + relatório de higienização/duplicidades/divergências e histórico).
- **TASK-015:** `RegrasConfiguracao.vue` (3 abas editáveis: Pesos de Prioridade, Regras por Exame e Matriz de Incompatibilidades).

Requisitos atendidos: RF003 (exibição), RF009 e CARE-RF003 (relatório de higienização).

## What Changes

- `frontend/src/types/exames.ts`: tipos do relatório de importação (`IImportacaoResumo`, `IItemImportacao`, `IRelatorioImportacao`) espelhando `src/schemas/importacoes.py`, e os campos opcionais `descricao`/`updatedAt` devolvidos por `/api/regras`.
- `frontend/src/stores/importacoes.ts`: upload `multipart/form-data` (`POST /api/importacoes/forms`), histórico (`GET /api/importacoes`) e relatório (`GET /api/importacoes/{id}`), usando o helper `executar` da TASK-012.
- `frontend/src/views/ImportacaoForms.vue`: arrastar/selecionar arquivo, validação de extensão e tamanho (5 MB, mesmo limite do backend), contadores por status, colunas reconhecidas/ignoradas, filtro por resultado, tabela das linhas com observação e histórico de lotes.
- `frontend/src/views/RegrasConfiguracao.vue`: três abas sobre a store `regras.ts` da TASK-012 (listar, criar, editar, pausar/ativar e exclusão lógica), com as mesmas validações do Pydantic antes do envio.
- `frontend/public/modelo_planilha_forms.csv`: planilha de exemplo com os cabeçalhos do Forms e casos válidos, duplicado, divergente e não encontrado no AGHU mock.
- `frontend/src/services/requisicao.ts`: `mensagemErro` passa a ler também a lista de erros `422` do Pydantic e o `403` do RBAC.
- Rotas `/importacao` e `/regras` (`requiresAuth`) e links no menu lateral.

## Capabilities

### New Capabilities
- `frontend-importacao-regras`: telas de importação do Forms e de regras configuráveis da fila.

### Modified Capabilities
(nenhuma — os contratos `/api/importacoes` e `/api/regras` são consumidos sem mudança)

## Dependências

- **TASK-012/013 (Pedro) — branch `feat/task-012-013-frontend-fila`:** tipos, `requisicao.ts` e `stores/regras.ts`.
- **TASK-006/007 (Eduardo) — PR #3 (`feat/fase-2-regras-importacao`):** endpoints `/api/regras/*` e `/api/importacoes/*`.

## Fora de escopo

- Mudanças no backend, nos interceptadores do Axios ou na autenticação.
- Dashboard e reorganização da navegação (TASK-016).
- Testes automatizados de frontend (o projeto não tem runner no `frontend/`); a validação é `npm run build` e o fluxo manual no navegador.

## Impact

- Novos: `frontend/src/stores/importacoes.ts`, `frontend/src/views/ImportacaoForms.vue`, `frontend/src/views/RegrasConfiguracao.vue`, `frontend/public/modelo_planilha_forms.csv`.
- Alterados: `frontend/src/types/exames.ts`, `frontend/src/services/requisicao.ts`, `frontend/src/router/index.ts`, `frontend/src/layouts/DefaultLayout.vue`.
