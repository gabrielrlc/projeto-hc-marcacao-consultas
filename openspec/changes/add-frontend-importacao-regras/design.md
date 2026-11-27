## Context

As telas consomem o backend do PR #3 (TASK-006/007) e reaproveitam a camada de dados da TASK-012: `services/requisicao.ts` (loading/erro) e `stores/regras.ts` (CRUD genérico por recurso `prioridades`, `exames`, `incompatibilidades`).

## Decisions

- **Store própria para importação** (`stores/importacoes.ts`) em vez de estender `exames.ts`: a fila e a importação têm ciclos de vida diferentes e a tela de importação não precisa da paginação da fila.
- **Upload com `Content-Type` indefinido:** o `api.ts` define `application/json` por padrão; no upload o cabeçalho é removido para o navegador montar o `multipart/form-data` com boundary, sem mexer nos interceptadores.
- **Relatório sempre vindo do backend:** os contadores exibidos são os `contadores` da API; a tela só filtra as linhas já devolvidas. Ao abrir, carrega o histórico e o relatório do lote mais recente.
- **Pausar/ativar = `PUT` com `ativo` invertido** (corpo completo, como pede o schema `*Update`); remover = `DELETE` (soft delete no backend, a linha some da lista).
- **Código identificador imutável na edição:** `codigo` (prioridade) e `codigoExame` (regra de exame) ficam bloqueados no formulário de edição, como no schema do backend.
- **Validação dupla:** a tela barra par de exame consigo mesmo, `INTERVALO_MINIMO` sem dias e peso fora de 0–1000; erros `422`/`400`/`409` do backend aparecem no modal pela mensagem `detail`.

## Risks / Trade-offs

- O histórico (`ImportacaoResumoOut`) só traz `totalErros` agregado; o detalhamento por status aparece ao abrir o relatório do lote.
- Perfis sem permissão (`CONSULTA` nas regras, por exemplo) recebem `403` e a tela mostra a mensagem de permissão.
