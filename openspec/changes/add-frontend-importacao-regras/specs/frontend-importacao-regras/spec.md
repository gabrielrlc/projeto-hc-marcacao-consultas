## Purpose

Define as telas de importação da planilha do Google Forms (`/importacao`) e de regras configuráveis da fila (`/regras`).

Verificação: o projeto não tem runner de testes de frontend; os cenários são verificados por `npm run build` (`vue-tsc`) e pelo fluxo manual no navegador contra o backend real.

## ADDED Requirements

### Requirement: Upload da planilha do Forms
A rota `/importacao` SHALL exigir autenticação e aceitar um arquivo `.csv` ou `.xlsx` de até 5 MB, enviado como `multipart/form-data` no campo `arquivo` para `POST /api/importacoes/forms`. Arquivos com outra extensão, vazios ou maiores que o limite MUST NOT ser enviados.

#### Scenario: Extensão inválida
- **WHEN** o usuário seleciona um `.pdf`
- **THEN** a tela mostra "Formato não suportado" e nenhuma requisição é feita

#### Scenario: Erro do backend
- **WHEN** o backend responde `400` com `{"detail": "..."}` (planilha sem a coluna da solicitação, por exemplo)
- **THEN** a tela exibe exatamente essa mensagem

### Requirement: Relatório de higienização
Após a importação, a tela SHALL exibir o total de linhas, os `contadores` por status de higienização (`VALIDA`, `DUPLICADA`, `DIVERGENCIA_EXAME`, `NAO_ENCONTRADA`, `JA_REALIZADA`), as colunas reconhecidas e ignoradas e a tabela das linhas com a observação de cada exceção, filtrável por status.

#### Scenario: Planilha de exemplo
- **WHEN** o usuário importa `modelo_planilha_forms.csv` com o AGHU mock
- **THEN** o relatório mostra 10 linhas: 7 válidas, 1 duplicada, 1 divergência de exame e 1 não encontrada

### Requirement: Histórico de importações
A tela SHALL listar os lotes de `GET /api/importacoes` e abrir o relatório de qualquer lote por `GET /api/importacoes/{id}`.

#### Scenario: Reabrir um lote
- **WHEN** o usuário clica em "Ver relatório" de um lote anterior
- **THEN** o relatório desse lote substitui o exibido

### Requirement: Regras configuráveis em três abas
A rota `/regras` SHALL exigir autenticação e exibir as abas Pesos de Prioridade, Regras por Exame e Matriz de Incompatibilidades, cada uma permitindo criar, editar, pausar/ativar (`PUT` com `ativo` invertido) e remover (`DELETE`, exclusão lógica) via `/api/regras/*`. O código identificador MUST NOT ser editável após a criação.

#### Scenario: Pausar critério
- **WHEN** o gestor clica em "Pausar" num critério ativo
- **THEN** a API recebe `PUT /api/regras/prioridades/{id}` com `ativo: false` e a linha passa a mostrar "Pausada"

#### Scenario: Par inválido
- **WHEN** o gestor tenta salvar uma incompatibilidade com o mesmo exame dos dois lados
- **THEN** o modal mostra "O exame conflitante deve ser diferente do exame de origem." e nada é enviado

#### Scenario: Perfil sem permissão
- **WHEN** um usuário `CONSULTA` tenta salvar uma regra e o backend responde `403`
- **THEN** o modal mostra a mensagem de permissão
