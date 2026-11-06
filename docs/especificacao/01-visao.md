# Documento de Visão

## 1. Problema e Oportunidade

- **O Problema**: O recebimento de pedidos de exames ocorre via Google Forms sem qualquer validação prévia de dados com o sistema central. Isso gera um volume massivo de informações incorretas, obrigando a equipe a triar visualmente todos os pedidos em planilhas improvisadas.
- **Impacto**: Ocorre uma enorme sobrecarga de trabalho, pois a equipe perde horas buscando números de solicitação inexistentes no sistema legado (AGHU). Além disso, há uma grave subotimização das filas e perda de vagas urgentes por depender exclusivamente de pessoas para aplicar regras de prioridade clínica e restrições logísticas de distância (tempo de deslocamento do paciente).
- **Solução Proposta**: Um Portal Web que substitui os formulários e planilhas atuais. O sistema cruza e valida os dados inseridos pelos pacientes de forma instantânea através do banco de dados de leitura do AGHU, apresentando à equipe da Central de Marcação um painel com a fila de espera já filtrada, validada e automaticamente organizada por prioridade clínica e viabilidade geográfica.

## 2. Partes Interessadas (Stakeholders)

- **Usuários Finais**: Equipe da Central de Marcação de Exames (operadores que farão a gestão da fila e o agendamento final no AGHU).
- **Patrocinadores**: Gestão Médica, Coordenação Superior do Hospital das Clínicas (HC-UFPE) e Setor de TI (SETISD).
- **Pacientes / Usuários**: Cidadãos que necessitam enviar seus pedidos de exames médicos de forma digital e acompanhar o status do agendamento.

## 3. Escopo do Produto

- **Funcionalidades principais**:
  - Portal web de entrada para os pacientes com validação em tempo real do número de solicitação junto ao banco de dados do AGHU.
  - Painel de gestão (Dashboard) para a equipe alterar os status (Aguardando, Agendado, Cancelado) e visualizar indicadores.
  - Mecanismo de sincronização apenas de leitura para extrair dados do AGHU para o banco de dados local.
- **Limites do projeto**: O sistema **não** fará a gravação, alteração ou agendamento direto no banco de dados do AGHU (impedimento de escrita arquitetural). O ato final de confirmar o exame continuará sendo executado manualmente por um funcionário na tela do sistema legado. O sistema também não fará a gestão de filas externas do SUS.

## 4. Metas e Objetivos de Negócio

- **Erradicação de Dados Inválidos**: Reduzir o índice de pedidos que chegam à equipe com chaves ou números de solicitação incorretos.
- **Redução do Tempo de Espera**: Diminuir o tempo médio de espera por especialidade através de um preenchimento mais ágil das vagas ociosas ou de desistências de última hora.
- **Otimização Logística**: Impedir o agendamento de vagas de urgência (para o dia seguinte) a pacientes cujo município de residência impossibilite a chegada em tempo útil ao hospital, diminuindo as taxas de falta.
- **Rastreabilidade e Governança**: Substituir o rastreio visual e informal ("pintar a linha de verde" no Excel) por um histórico digital inviolável que contabiliza o fluxo de trabalho diário da equipe de marcação.
