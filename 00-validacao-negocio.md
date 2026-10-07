# Portal de Agendamento e Triagem de Exames — Documento de Validação e Especificação de Negócio

> **Padrão Oficial SETISD / HC-UFPE (HU Brasil) — Fase 0 (Alinhamento de Negócio)**  
> **Público-alvo:** Profissionais das áreas envolvidas e Equipe de TI.  
> **Objetivo:** Descrever o processo de trabalho em **linguagem pura de negócio** (sem jargões técnicos de programação ou banco de dados) para validação, alinhamento de expectativas e tomada de decisão antes de qualquer codificação.

---

## 1. Identificação do Projeto e Contexto Institucional

| Campo                              | Descrição                                                                                                                                                                                  |
| :--------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Nome do Sistema**                | Portal de Agendamento e Triagem de Exames                                                                                                                                                  |
| **Área Solicitante / Cliente**     | Central de Marcação de Exames / HC-UFPE                                                                                                                                                    |
| **Instância Superior Competente**  | Superintendência do HC-UFPE / SETISD                                                                                                                                                       |
| **Líder Técnico (SETISD)**         | Tiago Ferrão                                                                                                                                                                               |
| **Objetivo Estratégico HU Brasil** | Modernizar o fluxo de atendimento ao paciente, mitigando filas, otimizando o preenchimento de vagas ociosas e garantindo a rastreabilidade e priorização clínica no agendamento de exames. |

---

## 2. O Problema que Queremos Resolver

> **Objetivo:** Dizer com clareza qual é o problema real de trabalho. Sem rodeios: o que hoje está quebrado, ineficiente ou gerando risco para o hospital?

- **A Dor Central:**  
  O recebimento de pedidos de exames ocorre via Google Forms sem validação prévia, gerando um volume massivo de dados incorretos que a equipe precisa triar visualmente em planilhas, resultando em lentidão, filas subotimizadas e dependência da memória humana para priorização clínica e logística.

- **Por que isso não pode continuar (Impactos Reais):**
  - **Sobrecarga de Trabalho:** A equipe perde horas tentando localizar solicitações no AGHU porque os pacientes frequentemente digitam informações erradas no formulário (como o número de celular no lugar do número do exame).
  - **Falta de Visibilidade e Subotimização:** A gestão não consegue cruzar dados rapidamente. Vagas urgentes (ex: desistências para o dia seguinte) acabam sendo perdidas ou alocadas para pacientes que moram muito longe (ex: no município de Pesqueira) e não têm tempo hábil de deslocamento.
  - **Risco de Falha Humana na Prioridade:** Regras clínicas complexas (como a prioridade máxima para pacientes da Nefrologia em hemodiálise) dependem inteiramente da atenção e do conhecimento prévio do atendente ao olhar a planilha.

---

## 3. Como o Processo Funciona Hoje (A Rotina Atual)

> **Objetivo:** Mapear a realidade crua de como as equipes se viram no dia a dia para realizar essa tarefa hoje.

- **Meios Utilizados Hoje:**  
  Google Forms (para os pacientes enviarem pedidos), Planilhas do Google Drive (para controle da fila) e o sistema legado AGHU (para a efetivação final do agendamento).

- **A Rotina Prática de Trabalho:**
  1. **Início:** O paciente sai da consulta com o ticket de solicitação impresso pelo AGHU e acessa um link do Google Forms para pedir a marcação.
  2. **Preenchimento:** O paciente digita seus dados e o "número da solicitação",sujeito a errar, e anexa uma foto do pedido.
  3. **Conferência (O Gargalo):** A equipe da Central de Marcação abre a planilha gerada pelo Forms, copia o número digitado pelo paciente e cola na tela de agendamento do AGHU. Muitas vezes, o sistema retorna "Solicitação não encontrada".
  4. **Entrega e Arquivo:** Quando a solicitação está correta e a vaga é encontrada, a atendente agenda no AGHU, volta para a planilha do Drive e altera a cor da linha correspondente para "verde" (indicando que foi resolvido). Não há histórico automatizado ou rastreabilidade de fila.

---

## 4. O Que a Nova Solução Deve Entregar (Resultado Esperado)

> **Objetivo:** Definir com clareza o que a solução digital deve trazer para eliminar a dor do processo atual.

- **A Proposta de Valor:** Substituir as planilhas e formulários improvisados por um Portal que cruza e valida os dados instantaneamente com o AGHU, apresentando para a equipe uma fila de espera já mastigada, limpa e organizada por prioridade clínica e logística.
- **Ganhos Práticos Imediatos:**
  - Fim das consultas frustradas no AGHU por números de solicitação inválidos.
  - Organização automática da fila baseada em regras reais (clínica, município, idade).
  - Substituição do controle visual ("pintar linha de verde") por um painel de status (Aguardando, Agendado, Cancelado).
  - Alerta automático que impede o agendamento simultâneo de exames conflitantes para o mesmo paciente.

---

## 5. Como Será o Trabalho no Novo Sistema (O Novo Fluxo)

> **Objetivo:** Explicar em linguagem direta como o usuário vai interagir com o sistema, resolvendo a dor do processo manual de ponta a ponta.

- **1. Os dados já vêm prontos (e certos):** Ao acessar o novo portal, o paciente digita o número da sua solicitação. O sistema confere na mesma hora com o banco de dados oficial do hospital. Se não existir, ele não consegue enviar. Se existir, o sistema já puxa o nome, a especialidade e o município sozinhos.
- **2. Priorização Automática:** A solicitação cai na tela da Central de Marcação não mais como uma linha cronológica solta, mas já ranqueada. O sistema identifica automaticamente, por exemplo, que aquele pedido veio da "Nefrologia" e o joga para o topo da fila de ultrassonografia urinária.
- **3. Sugestão Inteligente de Vagas:** Se uma vaga for aberta para a manhã seguinte, o sistema oculta da fila os pacientes de municípios distantes (como Pesqueira ou Sirinhaém) e exibe apenas aqueles da Região Metropolitana com tempo hábil de chegada.
- **4. Informação pronta e disponível:** A equipe realiza o agendamento no AGHU e, com um clique no novo portal, muda o status do paciente para "Agendado", finalizando o fluxo com total rastreabilidade.

---

## 6. Quem Participa do Processo (Atores: Como Faz Hoje vs. Como Fará no Sistema)

| Ator / Perfil no Hospital                            | O que faz HOJE (Rotina Manual)                                                                                                 | O que passará a fazer no NOVO SISTEMA                                                                                       | O que NÃO poderá fazer                                                                                                     |
| :--------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------- |
| **Central de Marcação** _(Ex: Maíra, Larissa, Tati)_ | Fica alternando entre Excel e AGHU. Copia números, testa um por um, e muda a cor da linha da planilha para avisar que agendou. | Acessa um painel único com a fila de pedidos já validada e organizada por prioridade. Confirma o agendamento com um clique. | Não poderá agendar automaticamente no AGHU por dentro do portal satélite (limitação técnica da sede em Brasília)[cite: 1]. |
| **Paciente / Usuário**                               | Preenche Google Forms manualmente, muitas vezes errando o número do pedido e enviando dados inúteis.                           | Digita seu código no Portal Web e vê seus dados serem carregados automaticamente para confirmação.                          | Não envia pedidos com códigos inválidos ou inventados.                                                                     |
| **Gestão / Coordenação Superior**                    | Não tem visão de gargalos. Depende de perguntar para a equipe quantas vagas sobraram e qual o tamanho da fila no Forms.        | Acompanha um painel que mostra o tamanho exato da fila validada por exame, tempo de espera médio e capacidade ociosa.       | Não preenche nem altera a ordem clínica da fila manualmente.                                                               |

---

## 7. Regras de Negócio Inegociáveis (RNs)

- **RN-01 (Validação Obrigatória na Entrada):** O sistema impede que qualquer paciente entre na fila de espera sem que o seu "Número de Solicitação" seja positivamente validado e encontrado na base de leitura do AGHU no momento exato do cadastro.
- **RN-02 (Soberania do AGHU):** Como o banco oficial do hospital bloqueia qualquer operação de inserção externa[cite: 1], a gravação final do agendamento sempre ocorrerá diretamente no AGHU pelo funcionário. O sistema atua como organizador prévio e espelho[cite: 1].
- **RN-03 (Fila de Prioridade Dinâmica):** A ordem de atendimento não será apenas cronológica (quem pediu primeiro). Pacientes sinalizados com prioridades específicas (como nefrologia para vias urinárias) ultrapassam automaticamente solicitações ambulatoriais de rotina.
- **RN-04 (Trava de Deslocamento - Logística):** Consultas ou exames agendados em caráter de urgência para o dia seguinte não poderão ser atribuídos a pacientes cujo CEP/Município cadastrado impeça o deslocamento em tempo hábil até as dependências do HC.
- **RN-05 (Impedimento de Conflitos):** O sistema deve analisar exames que não podem ser feitos no mesmo dia ou momento pelo mesmo paciente, emitindo um alerta de choque de horário para o atendente.

---

## 8. Painel de Gestão e Indicadores Estratégicos (KPIs)

O sistema deve disponibilizar um painel gerencial em tempo real com os seguintes indicadores de negócio:

1. **Taxa de Rejeição e Validação:** Volume de tentativas de agendamentos inválidos que o sistema barrou automaticamente (evitando retrabalho da equipe).
2. **Tempo Médio na Fila por Especialidade:** Mapeamento de quais tipos de exame (ex: Ultrassonografia Urinária vs. Mamografia) possuem os maiores gargalos e tempos de espera.
3. **Mapeamento Geográfico de Ociosidade:** Visualização da correlação entre abstenções/desistências e o município de origem do paciente, permitindo melhorar os critérios de tempo de deslocamento.

---

## 9. Matriz de Pontos de Decisão (Gabinete / Gestão do Negócio)

> _Itens que dependem de confirmação dos gestores do hospital antes da conclusão:_

|   #   | Ponto a Decidir                                                                                                                                                 | Impacto no Processo                                                                                                  | Quem deve decidir?                  | Status / Definição |
| :---: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------- | :---------------------------------- | :----------------- |
| **1** | **Pesos de Prioridade Clínica:** Quais são os pesos numéricos oficiais para classificar prioridades (ex: Nefrologia vale peso 10, Retorno Ambulatorial vale 2)? | Define a matemática do algoritmo que ordenará a fila de pacientes de forma automática.                               | Gestão Médica / Central de Marcação | 🟡 Em definição    |
| **2** | **Raio de Deslocamento:** Qual a distância máxima em quilômetros (ou municípios de corte) para ser elegível a uma vaga de "amanhã cedo"?                        | Impede que a equipe perca tempo ligando para pacientes que não conseguirão chegar a tempo no hospital.               | Gestão Central / Regulação Interna  | 🟡 Em definição    |
| **3** | **Integração de Notificações:** O status de "Agendado" no painel da equipe deverá disparar automaticamente um aviso (WhatsApp/SMS) para o paciente?             | Determina a necessidade de contratar e integrar serviços de mensageria externa ao banco local da aplicação satélite. | TI (SETISD) / Diretoria             | 🟡 Em definição    |

---

---

# 📘 GUIA METODOLÓGICO: COMO ESTE DOCUMENTO SE INTERLIGA AOS DEMAIS ARQUIVOS DO PROJETO

> **Apresentação Executiva para a Chefia:**  
> Esta seção explica a lógica de engenharia e governança adotada pelo SETISD para conectar as necessidades de negócio da ponta à construção do software.

### A Linha do Tempo: A Separação entre "Fase de Negócio" e "Fase de Engenharia"

Em qualquer projeto de software hospitalar existem dois mundos que precisam se comunicar com perfeição:

1. **O Mundo do Negócio (Chefias, Áreas Solicitantes, Governança, Direção):** Não devem ser expostos a termos técnicos de TI (bancos de dados, endpoints, JSON, status HTTP, docker, etc.). Eles precisam discutir _processos, dores reais, prazos, responsabilidades e regras_.
2. **O Mundo da Engenharia (Desenvolvedores e Testes):** Precisam de tabelas relacionais, tipos de dados estritos, rotas de API seguras e casos de uso testáveis.

Este documento (`00-validacao-negocio.md`) funciona como a **Ponte Oficial** entre esses dois mundos:

```text
               ┌────────────────────────────────────────────────────────┐
               │         00-VALIDAÇÃO E FLUXO DE NEGÓCIO (ESTE ARQUIVO) │
FASE 1         │   Linguagem humana, fluxos e regras reais de negócio.  │
(Negócio)      │   Validado e assinado pelas Chefias e Direção do HC.   │
               └───────────────────────────┬────────────────────────────┘
                                           │
                 ┌─────────────────────────┴─────────────────────────┐
                 ▼ (Uma vez aprovado, a TI desdobra tecnicamente)    ▼
               ┌────────────────────────────────────────────────────────┐
FASE 2         │            ARTEFATOS DE ESPECIFICAÇÃO TÉCNICA          │
(Engenharia)   │   01-visao.md  →  02-requisitos.md  →  03-casos-uso.md │
               │   04-modelo-dados.md  →  05-interfaces  →  SPEC.md     │
               └────────────────────────────────────────────────────────┘
```
