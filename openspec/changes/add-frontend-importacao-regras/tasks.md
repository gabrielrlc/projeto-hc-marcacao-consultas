## 1. Camada de dados

- [x] 1.1 Acrescentar em `frontend/src/types/exames.ts` os tipos do relatório de importação e os campos opcionais de `/api/regras`
- [x] 1.2 Criar `frontend/src/stores/importacoes.ts` (upload, histórico e relatório)
- [x] 1.3 Trocar a implementação mock de `stores/regras.ts` por `/api/regras/*`, mantendo a interface
- [x] 1.4 Ler erros `422` (lista do Pydantic) e `403` nas mensagens das stores

## 2. Importação do Forms (TASK-014)

- [x] 2.1 Refazer `ImportacaoForms.vue` sobre a API: upload por arrastar/selecionar com validação de extensão e tamanho
- [x] 2.2 Relatório: contadores por status, colunas reconhecidas/ignoradas, filtro por resultado e tabela das linhas
- [x] 2.3 Histórico de lotes com abertura do relatório de cada importação
- [x] 2.4 Planilha de exemplo em `frontend/public/modelo_planilha_forms.csv`

## 3. Regras configuráveis (TASK-015)

- [x] 3.1 Carregar as três abas de `RegrasConfiguracao.vue` do servidor ao abrir
- [x] 3.2 Criar/editar, pausar/ativar e remover persistindo via API, com mensagens de erro
- [x] 3.3 Trocar "Restaurar Padrão Seed" por "Recarregar do Servidor"

## 4. Verificação

- [x] 4.1 Rodar `npm run build` em `frontend/` sem erros
- [x] 4.2 Validar no navegador (login `admin`/`admin`, seed `python -m src.resources.seed_exames`): importar a planilha de exemplo (7 válidas, 1 duplicada, 1 divergente, 1 não encontrada), abrir o histórico, criar/pausar/remover regras e conferir as mensagens de validação
- [x] 4.3 Rodar `uv run python -m pytest -q` e confirmar todos os testes passando
- [x] 4.4 Rodar `python audit_framework.py .` e confirmar 100% nos 11 pilares
