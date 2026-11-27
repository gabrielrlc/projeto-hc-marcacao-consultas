## Context

As telas consomem o backend da TASK-006/007 e partem do protótipo do frontend já na `master`, em que a fila, o dashboard e as regras usam dados de exemplo e a store `regras.ts` é lida pela store `exames.ts` para calcular os scores mockados.

## Decisions

- **Interface da store `regras.ts` preservada:** só a implementação muda para a API, então a fila e o dashboard prototipados continuam funcionando sem alteração. Os dados de exemplo valem só até `carregarRegras()`.

- **Store própria para importação** (`stores/importacoes.ts`) em vez de estender `exames.ts`: a fila e a importação têm ciclos de vida diferentes e a tela de importação não precisa da paginação da fila.
- **Upload com `Content-Type` indefinido:** o `api.ts` define `application/json` por padrão; no upload o cabeçalho é removido para o navegador montar o `multipart/form-data` com boundary, sem mexer nos interceptadores.
- **Relatório sempre vindo do backend:** os contadores exibidos são os `contadores` da API; a tela só filtra as linhas já devolvidas. Ao abrir, carrega o histórico e o relatório do lote mais recente.
- **Pausar/ativar = `PUT` com `ativo` invertido** (corpo completo, como pede o schema `*Update`); remover = `DELETE` (soft delete no backend, a linha some da lista).
- **Código identificador:** o backend ignora `codigo`/`codigoExame` no `PUT` (são imutáveis no schema `*Update`).
- **Validação dupla:** a tela barra par de exame consigo mesmo, `INTERVALO_MINIMO` sem dias e peso fora de 0–1000; erros `422`/`400`/`409` do backend aparecem no modal pela mensagem `detail`.

## Risks / Trade-offs

- O histórico (`ImportacaoResumoOut`) só traz `totalErros` agregado; o detalhamento por status aparece ao abrir o relatório do lote.
- Perfis sem permissão (`CONSULTA` nas regras, por exemplo) recebem `403` e a tela mostra a mensagem de permissão.
