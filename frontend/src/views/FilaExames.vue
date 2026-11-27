<template>
  <div class="space-y-6">
    <!-- Cabeçalho Operacional -->
    <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-800 tracking-tight">
          Fila Priorizada de Exames
        </h1>
        <p class="text-sm text-slate-600 mt-0.5">
          Ordenação clínica determinística (Score de Prioridade e data de solicitação), alertas de preparo/conflitos e controle de confirmação 24h.
        </p>
      </div>
      <div class="flex items-center gap-2 text-xs text-slate-600">
        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white border border-stone-200 shadow-paper tabular-nums">
          <CheckCircleIcon class="h-4 w-4 text-emerald-700" />
          Confirmados AGHU: <strong class="text-slate-800">{{ resumoOperacional.confirmados }}</strong>
        </span>
      </div>
    </div>

    <!-- KPIs Rápidos do Turno -->
    <section
      aria-label="Indicadores operacionais do turno"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 t-stagger"
    >
      <button
        type="button"
        @click="aplicarAtalhoKpi('NA_FILA')"
        :class="[
          't-kpi-card t-stagger-item text-left bg-white rounded-lg p-4 border shadow-paper cursor-pointer',
          filtros.statusOperacional === 'NA_FILA' && !filtros.apenas24hVencidos
            ? 'border-teal-600 ring-1 ring-teal-600/20'
            : 'border-stone-200/80',
        ]"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Na Fila (Válidos)
          </span>
          <ClipboardDocumentListIcon class="h-5 w-5 text-teal-700" />
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span
            class="t-subtle-number text-2xl font-bold text-slate-800 tabular-nums"
            :class="{ 'is-animating': animandoKpis }"
          >
            {{ resumoOperacional.naFila }}
          </span>
          <span class="text-xs text-slate-500">elegíveis para vaga</span>
        </div>
      </button>

      <button
        type="button"
        @click="aplicarAtalhoKpi('AGUARDANDO_24H')"
        :class="[
          't-kpi-card t-stagger-item text-left bg-white rounded-lg p-4 border shadow-paper cursor-pointer',
          filtros.statusOperacional === 'AGUARDANDO_CONFIRMACAO_24H' && !filtros.apenas24hVencidos
            ? 'border-amber-500 ring-1 ring-amber-500/20'
            : 'border-stone-200/80',
        ]"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Em Confirmação 24h
          </span>
          <ClockIcon class="h-5 w-5 text-amber-700" />
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span
            class="t-subtle-number text-2xl font-bold text-slate-800 tabular-nums"
            :class="{ 'is-animating': animandoKpis }"
          >
            {{ resumoOperacional.aguardando24h }}
          </span>
          <span class="text-xs text-slate-500">aguardando retorno</span>
        </div>
      </button>

      <button
        type="button"
        @click="aplicarAtalhoKpi('VENCIDOS_24H')"
        :class="[
          't-kpi-card t-stagger-item text-left rounded-lg p-4 border shadow-paper cursor-pointer',
          resumoOperacional.vencidos24h > 0
            ? 'bg-red-50/50 border-red-200'
            : 'bg-white border-stone-200/80',
          filtros.apenas24hVencidos ? 'ring-2 ring-red-500/30 border-red-400' : '',
        ]"
      >
        <div class="flex items-center justify-between">
          <span
            :class="resumoOperacional.vencidos24h > 0 ? 'text-red-800' : 'text-slate-500'"
            class="text-xs font-semibold uppercase tracking-wide"
          >
            Prazo 24h Vencido
          </span>
          <ExclamationTriangleIcon
            :class="resumoOperacional.vencidos24h > 0 ? 'text-red-700' : 'text-slate-400'"
            class="h-5 w-5"
          />
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span
            :class="[
              't-subtle-number text-2xl font-bold tabular-nums',
              resumoOperacional.vencidos24h > 0 ? 'text-red-800' : 'text-slate-800',
              { 'is-animating': animandoKpis },
            ]"
          >
            {{ resumoOperacional.vencidos24h }}
          </span>
          <span
            :class="resumoOperacional.vencidos24h > 0 ? 'text-red-700' : 'text-slate-500'"
            class="text-xs"
          >
            {{ filtros.apenas24hVencidos ? 'filtro ativo (clique p/ sair)' : 'liberar vaga urgente' }}
          </span>
        </div>
      </button>

      <button
        type="button"
        @click="aplicarAtalhoKpi('EXCECOES')"
        :class="[
          't-kpi-card t-stagger-item text-left bg-white rounded-lg p-4 border shadow-paper cursor-pointer',
          filtros.statusHigienizacao === 'NAO_ENCONTRADA' || filtros.statusHigienizacao === 'DIVERGENCIA_EXAME'
            ? 'border-amber-500 ring-1 ring-amber-500/20'
            : 'border-stone-200/80',
        ]"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Exceções Higienização
          </span>
          <DocumentMagnifyingGlassIcon class="h-5 w-5 text-sky-700" />
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span
            class="t-subtle-number text-2xl font-bold text-slate-800 tabular-nums"
            :class="{ 'is-animating': animandoKpis }"
          >
            {{ resumoOperacional.excecoesHigienizacao }}
          </span>
          <span class="text-xs text-slate-500">busca ativa AGHU</span>
        </div>
      </button>
    </section>

    <!-- Barra de Filtros & Filtro Geográfico de Urgência -->
    <Card>
      <div class="space-y-4">
        <!-- Destaque: Filtro Geográfico de Urgência ("Vaga de Última Hora") -->
        <div class="flex flex-col gap-3 pb-4 border-b border-stone-200/80">
          <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
            <div class="flex flex-wrap items-center gap-3">
              <div class="flex items-center gap-1.5 text-sm font-semibold text-slate-800">
                <MapPinIcon class="h-4 w-4 text-teal-700 shrink-0" />
                <span>Filtro Geográfico de Urgência:</span>
              </div>

              <!-- Abas deslizantes (.t-tabs) para Região -->
              <div
                ref="regiaoTabsRef"
                role="tablist"
                aria-label="Filtro geográfico de urgência"
                class="t-tabs"
              >
                <div ref="regiaoPillRef" class="t-tabs-pill" aria-hidden="true"></div>
                <button
                  v-for="(opcao, idx) in OPCOES_REGIAO"
                  :key="opcao.value"
                  :ref="(el) => registrarTabRegiaoRef(el, idx)"
                  type="button"
                  role="tab"
                  :aria-selected="filtros.regiao === opcao.value"
                  class="t-tab"
                  @click="selecionarRegiao(opcao.value)"
                >
                  {{ opcao.label }}
                </button>
              </div>
            </div>

            <!-- Toggles Rápidos (TFD, Alertas/Conflitos, 24h Vencidos) -->
            <div class="flex flex-wrap items-center gap-2">
              <button
                type="button"
                @click="alternarFiltroBooleano('apenasTfd')"
                :aria-pressed="filtros.apenasTfd"
                :class="
                  filtros.apenasTfd
                    ? 'bg-sky-50 text-sky-900 border-sky-300 font-semibold'
                    : 'bg-white text-slate-700 border-stone-300 hover:bg-stone-50'
                "
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs transition-colors cursor-pointer"
              >
                <span
                  :class="filtros.apenasTfd ? 'bg-sky-600' : 'bg-stone-300'"
                  class="h-2 w-2 rounded-full"
                ></span>
                Somente TFD
              </button>

              <button
                type="button"
                @click="alternarFiltroBooleano('apenasComAlertas')"
                :aria-pressed="filtros.apenasComAlertas"
                :class="
                  filtros.apenasComAlertas
                    ? 'bg-amber-50 text-amber-900 border-amber-300 font-semibold'
                    : 'bg-white text-slate-700 border-stone-300 hover:bg-stone-50'
                "
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs transition-colors cursor-pointer"
              >
                <ExclamationTriangleIcon class="h-3.5 w-3.5" />
                Apenas com alertas/conflitos
              </button>

              <button
                type="button"
                @click="alternarFiltroBooleano('apenas24hVencidos')"
                :aria-pressed="filtros.apenas24hVencidos"
                :class="
                  filtros.apenas24hVencidos
                    ? 'bg-red-50 text-red-900 border-red-300 font-semibold'
                    : 'bg-white text-slate-700 border-stone-300 hover:bg-stone-50'
                "
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs transition-colors cursor-pointer"
              >
                <ClockIcon class="h-3.5 w-3.5" />
                24h Vencidos
              </button>
            </div>
          </div>

          <p class="inline-flex items-center gap-1.5 text-xs text-slate-600 bg-stone-50 border border-stone-200/80 rounded-md px-3 py-1.5 w-fit">
            <InformationCircleIcon class="h-4 w-4 text-teal-700 shrink-0" />
            <span>
              <strong>Filtro operacional para encaixe rápido:</strong> seleciona pacientes por proximidade/TFD sem alterar o Score de Prioridade Clínica nem a ordem relativa dos elegíveis.
            </span>
          </p>
        </div>

        <!-- Linha de Filtros Textuais e Selects -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-3 items-end">
          <div class="lg:col-span-4">
            <label for="filtro-busca-fila" class="form-label text-xs font-semibold text-slate-700">
              Busca Rápida (Prontuário, Paciente ou Solicitação)
            </label>
            <div class="relative">
              <span class="form-control-icon text-slate-400">
                <MagnifyingGlassIcon class="h-4 w-4" />
              </span>
              <input
                id="filtro-busca-fila"
                :value="filtros.busca"
                type="text"
                placeholder="Ex: 1114567, 890001 ou nome..."
                class="form-control pl-9 pr-8 text-sm text-slate-800"
                @input="aoDigitarBusca"
              />
              <button
                v-if="filtros.busca"
                type="button"
                aria-label="Limpar busca"
                class="absolute inset-y-0 right-0 pr-2.5 flex items-center text-slate-400 hover:text-slate-700 cursor-pointer"
                @click="examesStore.definirFiltros({ busca: '' })"
              >
                <XMarkIcon class="h-4 w-4" />
              </button>
            </div>
          </div>

          <div class="lg:col-span-3">
            <label for="filtro-exame-fila" class="form-label text-xs font-semibold text-slate-700">
              Exame
            </label>
            <select
              id="filtro-exame-fila"
              :value="filtros.codigoExame"
              class="form-control text-sm text-slate-800"
              @change="aoSelecionarExame"
            >
              <option value="">Todos os exames</option>
              <option
                v-for="ex in examesStore.examesDisponiveis"
                :key="ex.codigo"
                :value="ex.codigo"
              >
                {{ ex.codigo }} — {{ ex.nome }}
              </option>
            </select>
          </div>

          <div class="lg:col-span-3">
            <label for="filtro-status-op-fila" class="form-label text-xs font-semibold text-slate-700">
              Status Operacional
            </label>
            <select
              id="filtro-status-op-fila"
              :value="filtros.statusOperacional"
              class="form-control text-sm text-slate-800"
              @change="aoSelecionarStatusOperacional"
            >
              <option value="TODOS">Todos os status</option>
              <option value="NA_FILA">Na Fila</option>
              <option value="AGUARDANDO_CONFIRMACAO_24H">Aguardando Confirmação 24h</option>
              <option value="CONFIRMADO_AGENDADO_AGHU">Confirmado / Agendado AGHU</option>
              <option value="SEM_RESPOSTA_24H">Sem Resposta 24h</option>
              <option value="CANCELADO">Cancelado</option>
            </select>
          </div>

          <div class="lg:col-span-2">
            <label for="filtro-hig-fila" class="form-label text-xs font-semibold text-slate-700">
              Higienização
            </label>
            <select
              id="filtro-hig-fila"
              :value="filtros.statusHigienizacao"
              class="form-control text-sm text-slate-800"
              @change="aoSelecionarStatusHigienizacao"
            >
              <option value="TODOS">Todas</option>
              <option value="VALIDA">Válida (AGHU)</option>
              <option value="NAO_ENCONTRADA">Não Encontrada</option>
              <option value="DIVERGENCIA_EXAME">Divergência Exame</option>
              <option value="DUPLICADA">Duplicada</option>
              <option value="JA_REALIZADA">Já Realizada</option>
            </select>
          </div>
        </div>

        <!-- Rodapé da Barra de Filtros -->
        <div class="flex flex-wrap items-center justify-between gap-2 pt-1 text-xs text-slate-600">
          <div class="flex items-center gap-2 tabular-nums">
            <FunnelIcon class="h-3.5 w-3.5 text-slate-400" />
            <span>
              Exibindo <strong class="text-slate-800">{{ filaFiltrada.length }}</strong> de
              <strong class="text-slate-800">{{ examesStore.itensEnriquecidos.length }}</strong>
              solicitações na fila
            </span>
          </div>

          <button
            v-if="possuiFiltroAtivo"
            type="button"
            class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md border border-stone-300 bg-white hover:bg-stone-50 text-slate-700 font-medium transition-colors cursor-pointer"
            @click="limparTodosFiltros"
          >
            <XMarkIcon class="h-3.5 w-3.5" />
            Limpar Filtros
          </button>
        </div>
      </div>
    </Card>

    <!-- Tabela Clínica Semântica -->
    <Card>
      <template #header>
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-stone-200/80 pb-3">
          <div>
            <h2 class="text-base font-bold text-slate-800">
              Solicitações Ordenadas por Prioridade Clínica
            </h2>
            <p class="text-xs text-slate-500">
              Identificação exclusiva por Prontuário + Solicitação AGHU (LGPD). Passe o cursor no score para ver o detalhamento dos pesos.
            </p>
          </div>
        </div>
      </template>

      <div v-if="filaFiltrada.length > 0" class="overflow-x-auto -mx-6 px-6">
        <table class="w-full min-w-[1040px] text-left text-sm text-slate-700">
          <thead class="bg-stone-50 text-[11px] uppercase tracking-wider font-semibold text-slate-500 border-y border-stone-200">
            <tr>
              <th class="py-3 px-3 w-36">Posição / Score</th>
              <th class="py-3 px-3">Paciente &amp; Prontuário</th>
              <th class="py-3 px-3">Município / TFD</th>
              <th class="py-3 px-3">Exame &amp; Solicitação AGHU</th>
              <th class="py-3 px-3">Alertas Clínicos</th>
              <th class="py-3 px-3 w-44">Status &amp; Prazo 24h</th>
              <th class="py-3 px-3 text-right w-56">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-100">
            <tr
              v-for="(item, indice) in filaFiltrada"
              :key="item.id"
              :class="[
                'hover:bg-stone-50/70 transition-colors align-top',
                ehPrazo24hVencido(item) ? 'bg-red-50/30' : '',
              ]"
            >
              <!-- 1. Posição & Score + Tooltip (.t-tt) -->
              <td class="py-3.5 px-3">
                <div class="flex items-start gap-2">
                  <span class="text-xs font-semibold text-slate-400 tabular-nums pt-1 w-6 shrink-0">
                    #{{ indice + 1 }}
                  </span>
                  <div class="space-y-1">
                    <div class="t-tt-group">
                      <button
                        type="button"
                        :class="classeBadgeScore(item.scorePrioridade)"
                        class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-xs font-bold tabular-nums cursor-help"
                        @click="abrirModalDetalhes(item)"
                      >
                        <span>{{ item.scorePrioridade }} pts</span>
                        <InformationCircleIcon class="h-3.5 w-3.5 opacity-80" />
                      </button>

                      <!-- Tooltip de Justificativa do Score (.t-tt) -->
                      <div class="t-tt t-tt-hover min-w-[230px] max-w-[290px]" role="tooltip">
                        <span class="text-[11px] font-bold uppercase tracking-wide text-slate-500 mb-1">
                          Composição do Score ({{ item.scorePrioridade }} pts)
                        </span>
                        <ul
                          v-if="item.motivosPrioridade.length > 0"
                          class="space-y-0.5 text-xs text-slate-700"
                        >
                          <li
                            v-for="motivo in item.motivosPrioridade"
                            :key="motivo"
                            class="flex items-center gap-1.5"
                          >
                            <span class="h-1.5 w-1.5 rounded-full bg-teal-600 shrink-0"></span>
                            <span>{{ motivo }}</span>
                          </li>
                        </ul>
                        <span v-else class="text-xs text-slate-500">
                          Sem critérios adicionais aplicados.
                        </span>
                      </div>
                    </div>

                    <p
                      v-if="item.motivosPrioridade.length > 0"
                      class="text-[11px] text-slate-500 leading-tight max-w-[140px]"
                    >
                      {{ item.motivosPrioridade[0] }}
                      <span v-if="item.motivosPrioridade.length > 1" class="text-slate-400">
                        +{{ item.motivosPrioridade.length - 1 }}
                      </span>
                    </p>
                  </div>
                </div>
              </td>

              <!-- 2. Paciente & Prontuário (NUNCA CPF) -->
              <td class="py-3.5 px-3">
                <div class="space-y-1">
                  <p class="font-semibold text-slate-800 leading-snug">
                    {{ item.nomePaciente }}
                  </p>
                  <div class="flex flex-wrap items-center gap-1.5">
                    <span
                      v-if="item.prontuario"
                      class="inline-flex items-center px-1.5 py-0.5 rounded bg-stone-100 border border-stone-200 text-slate-700 font-mono text-xs tabular-nums"
                    >
                      Pront. {{ item.prontuario }}
                    </span>
                    <span
                      v-else
                      class="inline-flex items-center px-1.5 py-0.5 rounded bg-amber-50 border border-amber-200 text-amber-800 text-[11px] font-medium"
                    >
                      Sem prontuário no AGHU
                    </span>
                    <span
                      v-if="item.flagHemodialise"
                      class="inline-flex items-center px-1.5 py-0.5 rounded bg-red-50 border border-red-200 text-red-800 text-[10px] font-semibold"
                    >
                      Hemodiálise
                    </span>
                    <span
                      v-if="item.flagDiabeticoJejum"
                      class="inline-flex items-center px-1.5 py-0.5 rounded bg-amber-50 border border-amber-200 text-amber-800 text-[10px] font-semibold"
                    >
                      Diabético
                    </span>
                  </div>
                  <p v-if="item.telefoneContato" class="text-xs text-slate-500 tabular-nums flex items-center gap-1">
                    <PhoneIcon class="h-3 w-3 text-slate-400 shrink-0" />
                    {{ item.telefoneContato }}
                  </p>
                </div>
              </td>

              <!-- 3. Município / Região / TFD -->
              <td class="py-3.5 px-3">
                <div class="space-y-1">
                  <p class="text-sm font-medium text-slate-800">
                    {{ item.municipio || 'Não informado' }}
                  </p>
                  <div class="flex flex-wrap items-center gap-1">
                    <span
                      :class="classeBadgeRegiao(item.regiaoGeografica)"
                      class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold"
                    >
                      {{ rotuloRegiao(item.regiaoGeografica) }}
                    </span>
                    <span
                      v-if="item.utilizaTfd"
                      class="inline-flex items-center px-2 py-0.5 rounded bg-sky-50 text-sky-800 border border-sky-200 text-[11px] font-bold"
                    >
                      TFD
                    </span>
                  </div>
                </div>
              </td>

              <!-- 4. Exame & Solicitação AGHU -->
              <td class="py-3.5 px-3">
                <div class="space-y-1">
                  <div class="flex flex-wrap items-center gap-1.5">
                    <span class="font-mono text-xs font-semibold text-slate-700 tabular-nums bg-stone-100 border border-stone-200 px-1.5 py-0.5 rounded">
                      #{{ item.codigoSolicitacao }}
                    </span>
                    <span
                      v-if="item.codigoExame"
                      class="font-mono text-xs font-bold text-teal-800 bg-teal-50 border border-teal-200 px-1.5 py-0.5 rounded"
                    >
                      {{ item.codigoExame }}
                    </span>
                  </div>

                  <p class="text-sm font-medium text-slate-800 leading-snug">
                    {{ item.nomeExame || item.exameInformadoForms || 'Exame pendente de vínculo AGHU' }}
                  </p>

                  <p class="text-xs text-slate-500">
                    {{ item.unidadeSolicitante || 'Unidade não vinculada' }}
                  </p>

                  <div class="flex flex-wrap items-center gap-1.5">
                    <span
                      v-if="item.dataRetornoMedico"
                      :class="retornoProximo(item.dataRetornoMedico) ? 'text-amber-800 bg-amber-50 border-amber-200 font-semibold' : 'text-slate-600 bg-stone-50 border-stone-200'"
                      class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[11px] tabular-nums"
                    >
                      <CalendarIcon class="h-3 w-3" />
                      Retorno: {{ formatarDataCurta(item.dataRetornoMedico) }}
                    </span>

                    <span
                      v-if="item.statusHigienizacao !== 'VALIDA'"
                      :class="classeBadgeHigienizacao(item.statusHigienizacao)"
                      class="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-semibold"
                    >
                      {{ rotuloHigienizacao(item.statusHigienizacao) }}
                    </span>
                  </div>
                </div>
              </td>

              <!-- 5. Alertas Clínicos -->
              <td class="py-3.5 px-3">
                <div class="space-y-1.5 max-w-[230px]">
                  <div v-if="item.alertas.length > 0" class="flex flex-wrap gap-1">
                    <button
                      v-for="(alerta, aIdx) in item.alertas"
                      :key="`${alerta.tipo}-${aIdx}`"
                      type="button"
                      :title="alerta.mensagem"
                      :class="classeBadgeAlerta(alerta.severidade)"
                      class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold cursor-pointer text-left"
                      @click="abrirModalDetalhes(item)"
                    >
                      <ExclamationTriangleIcon
                        v-if="alerta.severidade === 'ALTA'"
                        class="h-3 w-3 shrink-0"
                      />
                      <ExclamationCircleIcon
                        v-else-if="alerta.severidade === 'MEDIA'"
                        class="h-3 w-3 shrink-0"
                      />
                      <InformationCircleIcon v-else class="h-3 w-3 shrink-0" />
                      <span>{{ rotuloAlerta(alerta.tipo) }}</span>
                    </button>
                  </div>
                  <span v-else class="text-xs text-slate-400">Sem alertas clínicos</span>

                  <button
                    v-if="item.outrosExames && item.outrosExames.length > 0"
                    type="button"
                    class="block text-[11px] font-medium text-teal-800 hover:text-teal-900 underline decoration-teal-300 cursor-pointer tabular-nums"
                    @click="abrirModalDetalhes(item)"
                  >
                    +{{ item.outrosExames.length }} outro(s) exame(s) no prontuário
                  </button>
                </div>
              </td>

              <!-- 6. Status & Prazo 24h -->
              <td class="py-3.5 px-3">
                <div class="space-y-1.5">
                  <span
                    :class="classeBadgeStatusOperacional(item.statusOperacional)"
                    class="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-semibold"
                  >
                    {{ rotuloStatusOperacional(item.statusOperacional) }}
                  </span>

                  <div
                    v-if="item.statusOperacional === 'AGUARDANDO_CONFIRMACAO_24H' && item.prazoConfirmacaoEm"
                    class="text-xs tabular-nums"
                  >
                    <p
                      :class="ehPrazo24hVencido(item) ? 'text-red-700 font-bold' : 'text-amber-700 font-semibold'"
                    >
                      {{ formatarTempo24h(item.prazoConfirmacaoEm) }}
                    </p>
                    <p class="text-[11px] text-slate-500">
                      Limite: {{ formatarDataHoraCurta(item.prazoConfirmacaoEm) }}
                    </p>
                  </div>

                  <div
                    v-else-if="item.statusOperacional === 'CONFIRMADO_AGENDADO_AGHU' && item.dataAgendadaAghu"
                    class="text-xs text-emerald-800 tabular-nums"
                  >
                    <p class="font-medium">AGHU: {{ formatarDataHoraCurta(item.dataAgendadaAghu) }}</p>
                    <p class="text-[11px] text-slate-500">
                      {{ item.preparoOrientado ? 'Preparo orientado' : 'Preparo pendente' }}
                    </p>
                  </div>
                </div>
              </td>

              <!-- 7. Ações Contextuais (Verbo + Objeto) -->
              <td class="py-3.5 px-3 text-right">
                <div class="flex flex-col items-end gap-1.5">
                  <div class="flex flex-wrap justify-end gap-1.5">
                    <!-- Exceção de higienização -> Busca Ativa AGHU -->
                    <Button
                      v-if="precisaBuscaAghu(item)"
                      variant="warning"
                      class="!py-1 !px-2.5 !text-xs font-semibold"
                      @click="abrirModalBuscaAghu(item)"
                    >
                      Buscar no AGHU
                    </Button>

                    <!-- Na Fila Válida -> Iniciar 24h -->
                    <Button
                      v-else-if="item.statusOperacional === 'NA_FILA'"
                      variant="primary"
                      class="!py-1 !px-2.5 !text-xs font-semibold"
                      @click="abrirModalStatus(item, 'AGUARDANDO_CONFIRMACAO_24H')"
                    >
                      Iniciar 24h
                    </Button>

                    <!-- Aguardando 24h -> Confirmar AGHU / Liberar Vaga -->
                    <template v-else-if="item.statusOperacional === 'AGUARDANDO_CONFIRMACAO_24H'">
                      <Button
                        variant="success"
                        class="!py-1 !px-2.5 !text-xs font-semibold"
                        @click="abrirModalStatus(item, 'CONFIRMADO_AGENDADO_AGHU')"
                      >
                        Confirmar AGHU
                      </Button>
                      <button
                        type="button"
                        class="px-2.5 py-1 rounded border border-red-200 bg-red-50 hover:bg-red-100 text-red-800 text-xs font-semibold transition-colors cursor-pointer"
                        @click="abrirModalStatus(item, 'SEM_RESPOSTA_24H')"
                      >
                        Liberar Vaga
                      </button>
                    </template>

                    <!-- Demais status -> Atualizar Status -->
                    <button
                      v-else
                      type="button"
                      class="px-2.5 py-1 rounded border border-stone-300 bg-white hover:bg-stone-50 text-slate-700 text-xs font-semibold transition-colors cursor-pointer"
                      @click="abrirModalStatus(item)"
                    >
                      Atualizar Status
                    </button>
                  </div>

                  <div class="flex flex-wrap justify-end gap-1.5">
                    <button
                      v-if="!precisaBuscaAghu(item)"
                      type="button"
                      class="px-2 py-1 rounded border border-stone-200 bg-white hover:bg-stone-50 text-slate-600 text-[11px] font-medium transition-colors cursor-pointer"
                      @click="abrirModalBuscaAghu(item)"
                    >
                      Vincular AGHU
                    </button>
                    <button
                      v-if="item.statusOperacional === 'NA_FILA' && !precisaBuscaAghu(item)"
                      type="button"
                      class="px-2 py-1 rounded border border-stone-200 bg-white hover:bg-stone-50 text-slate-600 text-[11px] font-medium transition-colors cursor-pointer"
                      @click="abrirModalStatus(item)"
                    >
                      Status 24h
                    </button>
                    <button
                      type="button"
                      class="px-2 py-1 rounded border border-stone-200 bg-stone-50 hover:bg-stone-100 text-slate-700 text-[11px] font-semibold transition-colors cursor-pointer"
                      @click="abrirModalDetalhes(item)"
                    >
                      Ver Detalhes
                    </button>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Estado vazio para filtros sem resultado -->
      <div v-else class="py-12 text-center space-y-3">
        <MagnifyingGlassIcon class="h-10 w-10 text-stone-300 mx-auto" />
        <div class="space-y-1">
          <p class="text-sm font-semibold text-slate-700">
            Nenhuma solicitação corresponde aos filtros selecionados.
          </p>
          <p class="text-xs text-slate-500">
            Ajuste a região geográfica, o exame ou limpe os filtros para visualizar a fila completa.
          </p>
        </div>
        <button
          type="button"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-stone-300 bg-white hover:bg-stone-50 text-xs font-semibold text-slate-700 cursor-pointer"
          @click="limparTodosFiltros"
        >
          <ArrowPathIcon class="h-3.5 w-3.5" />
          Limpar Filtros
        </button>
      </div>
    </Card>

    <!-- MODAL 1: Atualizar Status 24h / Efetivação AGHU -->
    <Modal :show="showStatusModal" @close="fecharStatusModal">
      <template #header>Atualizar Status Operacional</template>

      <div
        v-if="itemStatusAtual"
        :class="['t-modal space-y-4', showStatusModal ? 'is-open' : 'is-closing']"
      >
        <div class="p-3 bg-stone-50 border border-stone-200 rounded-lg text-xs space-y-1">
          <div class="flex items-center justify-between gap-2">
            <span class="font-bold text-slate-800 text-sm">{{ itemStatusAtual.nomePaciente }}</span>
            <span class="font-mono tabular-nums text-slate-600">
              #{{ itemStatusAtual.codigoSolicitacao }}
            </span>
          </div>
          <p class="text-slate-600">
            Prontuário:
            <strong class="font-mono tabular-nums">{{ itemStatusAtual.prontuario || 'Não vinculado' }}</strong>
            • Exame:
            <strong>{{ itemStatusAtual.codigoExame || '—' }}</strong>
            ({{ itemStatusAtual.nomeExame || itemStatusAtual.exameInformadoForms || 'A definir' }})
          </p>
          <p v-if="itemStatusAtual.telefoneContato" class="text-slate-600 tabular-nums">
            Telefone / WhatsApp: <strong>{{ itemStatusAtual.telefoneContato }}</strong>
          </p>
        </div>

        <form id="form-status-24h" class="space-y-4" @submit.prevent="salvarStatusOperacional">
          <div>
            <label for="status-operacional-select" class="form-label text-xs font-semibold text-slate-700">
              Novo Status Operacional
            </label>
            <select
              id="status-operacional-select"
              v-model="statusForm.statusOperacional"
              class="form-control text-sm text-slate-800"
            >
              <option value="NA_FILA">Na Fila (Aguardando vaga)</option>
              <option value="AGUARDANDO_CONFIRMACAO_24H">Aguardando Confirmação 24h</option>
              <option value="CONFIRMADO_AGENDADO_AGHU">Confirmado / Agendado no AGHU</option>
              <option value="SEM_RESPOSTA_24H">Sem Resposta 24h (Liberar vaga)</option>
              <option value="CANCELADO">Cancelado</option>
            </select>
          </div>

          <div
            v-if="statusForm.statusOperacional === 'AGUARDANDO_CONFIRMACAO_24H'"
            class="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-1"
          >
            <p class="font-semibold">Abertura do prazo de 24 horas</p>
            <p>
              Ao salvar, o sistema registra o início do contato agora e define o prazo máximo de confirmação para 24h à frente.
            </p>
          </div>

          <div
            v-if="statusForm.statusOperacional === 'CONFIRMADO_AGENDADO_AGHU'"
            class="space-y-3 p-3 rounded-lg bg-emerald-50/70 border border-emerald-200"
          >
            <div>
              <label for="data-agendada-aghu" class="form-label text-xs font-semibold text-slate-700">
                Data e Hora Efetivadas no AGHU *
              </label>
              <input
                id="data-agendada-aghu"
                v-model="statusForm.dataAgendadaAghu"
                type="datetime-local"
                :class="['form-control text-sm text-slate-800 tabular-nums', { 't-shake border-red-400': erroDataStatusShake }]"
              />
              <p v-if="erroDataStatusMensagem" class="text-xs text-red-700 mt-1 font-medium">
                {{ erroDataStatusMensagem }}
              </p>
            </div>

            <label class="flex items-start gap-2 text-xs text-slate-700 cursor-pointer">
              <input
                v-model="statusForm.preparoOrientado"
                type="checkbox"
                class="mt-0.5 rounded border-stone-300 text-teal-700 focus:ring-teal-600"
              />
              <span>
                Confirmo que o agendamento já foi lançado no AGHU e o preparo clínico foi orientado ao paciente.
              </span>
            </label>
          </div>

          <div
            v-if="statusForm.statusOperacional === 'SEM_RESPOSTA_24H'"
            class="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-900"
          >
            O paciente será marcado como <strong>Sem Resposta 24h</strong> e a vaga ficará disponível para o próximo item elegível da fila.
          </div>

          <div>
            <label for="status-observacoes" class="form-label text-xs font-semibold text-slate-700">
              Observações do Contato / Registro
            </label>
            <textarea
              id="status-observacoes"
              v-model="statusForm.observacoes"
              rows="3"
              placeholder="Registre tentativa de contato, confirmação de WhatsApp, orientação de jejum ou motivo..."
              class="form-control text-sm text-slate-800"
            ></textarea>
          </div>

          <p class="text-[11px] text-slate-500">
            Registro interno da Central: este fluxo não realiza gravação automática no banco do AGHU.
          </p>
        </form>
      </div>

      <template #footer>
        <button
          type="button"
          class="px-4 py-2 rounded border border-stone-300 bg-white hover:bg-stone-50 text-sm font-semibold text-slate-700 transition-colors cursor-pointer"
          @click="fecharStatusModal"
        >
          Cancelar
        </button>
        <Button
          type="submit"
          form="form-status-24h"
          variant="primary"
          :loading="examesStore.carregando"
        >
          Salvar Status
        </Button>
      </template>
    </Modal>

    <!-- MODAL 2: Busca Ativa por Prontuário no Espelho AGHU -->
    <Modal :show="showAghuModal" @close="fecharAghuModal">
      <template #header>Busca Ativa no Espelho AGHU</template>

      <div
        v-if="itemAghuAtual"
        :class="['t-modal space-y-4', showAghuModal ? 'is-open' : 'is-closing']"
      >
        <div class="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 space-y-1">
          <div class="flex items-center justify-between gap-2">
            <span class="font-bold text-slate-800">{{ itemAghuAtual.nomePaciente }}</span>
            <span class="font-mono tabular-nums">Forms #{{ itemAghuAtual.codigoSolicitacao }}</span>
          </div>
          <p>
            Exame informado:
            <strong>{{ itemAghuAtual.exameInformadoForms || itemAghuAtual.nomeExame || 'Não informado' }}</strong>
            • Status:
            <strong>{{ rotuloHigienizacao(itemAghuAtual.statusHigienizacao) }}</strong>
          </p>
          <p class="text-[11px] text-amber-800">
            Consulta somente-leitura ao espelho AGHU para localizar e vincular o pedido oficial.
          </p>
        </div>

        <form class="grid grid-cols-1 sm:grid-cols-3 gap-2.5" @submit.prevent="executarBuscaAghu">
          <div>
            <label for="busca-aghu-prontuario" class="form-label text-xs font-semibold text-slate-700">
              Prontuário
            </label>
            <input
              id="busca-aghu-prontuario"
              v-model="aghuBuscaForm.prontuario"
              type="text"
              placeholder="Ex: 1213344"
              class="form-control font-mono text-xs tabular-nums text-slate-800"
            />
          </div>
          <div>
            <label for="busca-aghu-solic" class="form-label text-xs font-semibold text-slate-700">
              Nº Solicitação
            </label>
            <input
              id="busca-aghu-solic"
              v-model="aghuBuscaForm.codigoSolicitacao"
              type="text"
              placeholder="Ex: 890022"
              class="form-control font-mono text-xs tabular-nums text-slate-800"
            />
          </div>
          <div>
            <label for="busca-aghu-nome" class="form-label text-xs font-semibold text-slate-700">
              Nome do Paciente
            </label>
            <input
              id="busca-aghu-nome"
              v-model="aghuBuscaForm.nome"
              type="text"
              placeholder="Parte do nome"
              class="form-control text-xs text-slate-800"
            />
          </div>
          <div class="sm:col-span-3 flex justify-end">
            <Button
              type="submit"
              variant="info"
              :loading="examesStore.buscandoAghu"
              class="!py-1.5 !px-3 !text-xs"
            >
              <template #icon>
                <MagnifyingGlassIcon class="h-4 w-4" />
              </template>
              Pesquisar no AGHU
            </Button>
          </div>
        </form>

        <div class="space-y-2 max-h-64 overflow-y-auto pr-1">
          <div v-if="examesStore.buscandoAghu" class="py-6 text-center text-xs text-slate-500">
            Consultando espelho somente-leitura do AGHU...
          </div>

          <div
            v-else-if="resultadosAghu.length === 0"
            class="p-4 text-center rounded-lg border border-stone-200 bg-stone-50 text-xs text-slate-600"
          >
            Nenhuma solicitação encontrada no AGHU com os parâmetros informados. Tente buscar apenas pelo prontuário ou nome.
          </div>

          <div
            v-for="reg in resultadosAghu"
            :key="`${reg.codigoSolicitacao}-${reg.codigoExame}`"
            class="p-3 rounded-lg border border-stone-200 bg-white hover:border-teal-300 transition-colors space-y-2"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="space-y-0.5">
                <div class="flex flex-wrap items-center gap-1.5">
                  <span class="font-mono text-xs font-bold text-slate-800 tabular-nums bg-stone-100 px-1.5 py-0.5 rounded">
                    #{{ reg.codigoSolicitacao }}
                  </span>
                  <span class="font-mono text-xs font-bold text-teal-800 bg-teal-50 border border-teal-200 px-1.5 py-0.5 rounded">
                    {{ reg.codigoExame }}
                  </span>
                  <span class="text-xs font-semibold text-slate-800">
                    {{ reg.nomeExame }}
                  </span>
                </div>
                <p class="text-xs text-slate-600">
                  {{ reg.nome }} • Prontuário:
                  <span class="font-mono tabular-nums font-semibold">{{ reg.prontuario || 'N/I' }}</span>
                </p>
                <p class="text-[11px] text-slate-500">
                  {{ reg.unidadeSolicitante }} • Solicitante: {{ reg.nomeFuncionario }} • {{ formatarDataCurta(reg.dataSolicitacao) }}
                </p>
              </div>

              <Button
                type="button"
                variant="primary"
                :loading="examesStore.carregando"
                class="!py-1 !px-2.5 !text-xs shrink-0"
                @click="vincularPedidoAghu(reg)"
              >
                Vincular
              </Button>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <button
          type="button"
          class="px-4 py-2 rounded border border-stone-300 bg-white hover:bg-stone-50 text-sm font-semibold text-slate-700 transition-colors cursor-pointer"
          @click="fecharAghuModal"
        >
          Fechar
        </button>
      </template>
    </Modal>

    <!-- MODAL 3: Detalhes Clínicos, Score, Preparo e Outros Exames do Prontuário -->
    <Modal :show="showDetalhesModal" @close="fecharDetalhesModal">
      <template #header>Detalhes Clínicos da Solicitação</template>

      <div
        v-if="itemDetalhesAtual"
        :class="['t-modal space-y-4 max-h-[70vh] overflow-y-auto pr-1', showDetalhesModal ? 'is-open' : 'is-closing']"
      >
        <!-- Resumo do Paciente e Pedido -->
        <div class="p-3.5 rounded-lg bg-stone-50 border border-stone-200 space-y-2 text-xs">
          <div class="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p class="text-sm font-bold text-slate-800">{{ itemDetalhesAtual.nomePaciente }}</p>
              <p class="text-slate-600 mt-0.5">
                Prontuário:
                <strong class="font-mono tabular-nums">{{ itemDetalhesAtual.prontuario || 'Não vinculado' }}</strong>
                • Solicitação:
                <strong class="font-mono tabular-nums">#{{ itemDetalhesAtual.codigoSolicitacao }}</strong>
              </p>
            </div>
            <span
              :class="classeBadgeScore(itemDetalhesAtual.scorePrioridade)"
              class="px-2.5 py-1 rounded-md text-xs font-bold tabular-nums"
            >
              {{ itemDetalhesAtual.scorePrioridade }} pts
            </span>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-stone-200/80 text-slate-600">
            <div>
              <span class="text-slate-400 block">Exame</span>
              <strong class="text-slate-800">
                {{ itemDetalhesAtual.codigoExame || '—' }} — {{ itemDetalhesAtual.nomeExame || itemDetalhesAtual.exameInformadoForms || 'Pendente' }}
              </strong>
            </div>
            <div>
              <span class="text-slate-400 block">Localidade / TFD</span>
              <strong class="text-slate-800">
                {{ itemDetalhesAtual.municipio || 'Não informado' }} ({{ rotuloRegiao(itemDetalhesAtual.regiaoGeografica) }})
                <span v-if="itemDetalhesAtual.utilizaTfd" class="text-sky-700">• TFD</span>
              </strong>
            </div>
            <div>
              <span class="text-slate-400 block">Unidade / Solicitante</span>
              <strong class="text-slate-800">
                {{ itemDetalhesAtual.unidadeSolicitante || 'N/I' }}
                <span v-if="itemDetalhesAtual.medicoSolicitante"> — {{ itemDetalhesAtual.medicoSolicitante }}</span>
              </strong>
            </div>
            <div>
              <span class="text-slate-400 block">Retorno Médico / Solicitação</span>
              <strong class="text-slate-800 tabular-nums">
                Retorno: {{ itemDetalhesAtual.dataRetornoMedico ? formatarDataCurta(itemDetalhesAtual.dataRetornoMedico) : 'Não informado' }}
              </strong>
            </div>
          </div>
        </div>

        <!-- Justificativa Completa do Score -->
        <div class="space-y-1.5">
          <h3 class="text-xs font-bold uppercase tracking-wide text-slate-500">
            Justificativa do Score de Prioridade
          </h3>
          <ul
            v-if="itemDetalhesAtual.motivosPrioridade.length > 0"
            class="space-y-1 text-xs text-slate-700 bg-white border border-stone-200 rounded-lg p-3"
          >
            <li
              v-for="motivo in itemDetalhesAtual.motivosPrioridade"
              :key="motivo"
              class="flex items-center gap-2"
            >
              <CheckCircleIcon class="h-4 w-4 text-teal-700 shrink-0" />
              <span>{{ motivo }}</span>
            </li>
          </ul>
          <p v-else class="text-xs text-slate-500">
            Nenhum critério de pontuação aplicado pelas regras ativas.
          </p>
        </div>

        <!-- Alertas Clínicos -->
        <div class="space-y-1.5">
          <h3 class="text-xs font-bold uppercase tracking-wide text-slate-500">
            Alertas Clínicos e Conflitos ({{ itemDetalhesAtual.alertas.length }})
          </h3>
          <div v-if="itemDetalhesAtual.alertas.length > 0" class="space-y-1.5">
            <div
              v-for="(alerta, idx) in itemDetalhesAtual.alertas"
              :key="`${alerta.tipo}-${idx}`"
              :class="classeBadgeAlerta(alerta.severidade)"
              class="p-2.5 rounded-lg text-xs space-y-0.5"
            >
              <p class="font-bold">{{ rotuloAlerta(alerta.tipo) }} ({{ alerta.severidade }})</p>
              <p class="leading-relaxed">{{ alerta.mensagem }}</p>
            </div>
          </div>
          <p v-else class="text-xs text-slate-500 bg-stone-50 border border-stone-200 rounded-lg p-3">
            Nenhum alerta clínico ou incompatibilidade detectada no momento.
          </p>
        </div>

        <!-- Orientações de Preparo -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between gap-2">
            <h3 class="text-xs font-bold uppercase tracking-wide text-slate-500">
              Orientações de Preparo
            </h3>
            <button
              v-if="itemDetalhesAtual.orientacoesPreparo"
              type="button"
              class="inline-flex items-center gap-1 px-2 py-1 rounded border border-stone-300 bg-white hover:bg-stone-50 text-[11px] font-semibold text-slate-700 cursor-pointer"
              @click="copiarPreparo(itemDetalhesAtual)"
            >
              <ClipboardDocumentIcon class="h-3.5 w-3.5 text-teal-700" />
              Copiar Preparo
            </button>
          </div>
          <div class="p-3 rounded-lg bg-sky-50/60 border border-sky-200 text-xs text-slate-700 leading-relaxed">
            {{ itemDetalhesAtual.orientacoesPreparo || 'Nenhuma orientação específica cadastrada para este exame.' }}
          </div>
        </div>

        <!-- Outros Exames do Mesmo Prontuário -->
        <div class="space-y-1.5">
          <h3 class="text-xs font-bold uppercase tracking-wide text-slate-500">
            Outros Exames do Mesmo Prontuário ({{ itemDetalhesAtual.outrosExames?.length ?? 0 }})
          </h3>
          <div
            v-if="itemDetalhesAtual.outrosExames && itemDetalhesAtual.outrosExames.length > 0"
            class="space-y-1.5"
          >
            <div
              v-for="(outro, idx) in itemDetalhesAtual.outrosExames"
              :key="`${outro.codigoSolicitacao}-${outro.codigoExame}-${idx}`"
              class="p-2.5 rounded-lg border border-stone-200 bg-white flex items-center justify-between gap-2 text-xs"
            >
              <div>
                <p class="font-semibold text-slate-800">
                  <span class="font-mono text-teal-800">{{ outro.codigoExame || '—' }}</span>
                  — {{ outro.nomeExame || 'Exame' }}
                </p>
                <p class="text-[11px] text-slate-500 tabular-nums">
                  Solicitação #{{ outro.codigoSolicitacao || '—' }}
                  <span v-if="outro.dataAgendada">
                    • Agendado: {{ formatarDataHoraCurta(outro.dataAgendada) }}
                  </span>
                </p>
              </div>
              <span
                :class="outro.origem === 'FILA' ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-stone-100 text-slate-700 border-stone-200'"
                class="px-2 py-0.5 rounded border text-[10px] font-bold shrink-0"
              >
                {{ outro.origem }}
              </span>
            </div>
          </div>
          <p v-else class="text-xs text-slate-500">
            Nenhum outro exame ativo localizado para este prontuário na fila ou no espelho AGHU.
          </p>
        </div>

        <!-- Observações -->
        <div v-if="itemDetalhesAtual.observacoes" class="space-y-1">
          <h3 class="text-xs font-bold uppercase tracking-wide text-slate-500">Observações</h3>
          <p class="text-xs text-slate-700 bg-stone-50 border border-stone-200 rounded-lg p-3 leading-relaxed">
            {{ itemDetalhesAtual.observacoes }}
          </p>
        </div>
      </div>

      <template #footer>
        <button
          v-if="itemDetalhesAtual && precisaBuscaAghu(itemDetalhesAtual)"
          type="button"
          class="px-3 py-2 rounded border border-amber-300 bg-amber-50 hover:bg-amber-100 text-xs font-semibold text-amber-900 cursor-pointer"
          @click="trocarParaBuscaAghu(itemDetalhesAtual)"
        >
          Buscar no AGHU
        </button>
        <button
          v-if="itemDetalhesAtual"
          type="button"
          class="px-3 py-2 rounded border border-stone-300 bg-white hover:bg-stone-50 text-xs font-semibold text-slate-700 cursor-pointer"
          @click="trocarParaStatus(itemDetalhesAtual)"
        >
          Atualizar Status 24h
        </button>
        <Button type="button" variant="primary" @click="fecharDetalhesModal">
          Fechar
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch, type ComponentPublicInstance } from 'vue';
import { useToast } from 'vue-toastification';
import {
  ArrowPathIcon,
  CalendarIcon,
  CheckCircleIcon,
  ClipboardDocumentIcon,
  ClipboardDocumentListIcon,
  ClockIcon,
  DocumentMagnifyingGlassIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  FunnelIcon,
  InformationCircleIcon,
  MagnifyingGlassIcon,
  MapPinIcon,
  PhoneIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline';
import Button from '../components/Button.vue';
import Card from '../components/Card.vue';
import Modal from '../components/Modal.vue';
import { useExamesStore } from '../stores/exames';
import type {
  IItemFila,
  ISolicitacaoAghu,
  RegiaoGeografica,
  SeveridadeAlerta,
  StatusHigienizacao,
  StatusOperacional,
  TipoAlerta,
} from '../types/exames';

const examesStore = useExamesStore();
const toast = useToast();

const OPCOES_REGIAO: Array<{ value: RegiaoGeografica | 'TODAS'; label: string }> = [
  { value: 'TODAS', label: 'Todas' },
  { value: 'CAPITAL', label: 'Capital' },
  { value: 'RMR', label: 'RMR' },
  { value: 'INTERIOR', label: 'Interior' },
];

const filtros = computed(() => examesStore.filtros);
const filaFiltrada = computed(() => examesStore.filaFiltrada);
const resumoOperacional = computed(() => examesStore.resumoOperacional);

const possuiFiltroAtivo = computed(() => {
  const f = filtros.value;
  return Boolean(
    f.busca.trim() ||
      f.codigoExame ||
      f.unidade ||
      f.statusOperacional !== 'TODOS' ||
      f.statusHigienizacao !== 'TODOS' ||
      f.regiao !== 'TODAS' ||
      f.municipio ||
      f.apenasTfd ||
      f.apenas24hVencidos ||
      f.apenasComAlertas,
  );
});

// Relógio reativo para contagem regressiva de 24h
const agoraMs = ref<number>(Date.now());
let relogioTimer: ReturnType<typeof setInterval> | null = null;

// Animação sutil nos KPIs quando contadores mudam
const animandoKpis = ref(false);
let kpiAnimTimer: ReturnType<typeof setTimeout> | null = null;

watch(
  resumoOperacional,
  () => {
    animandoKpis.value = true;
    if (kpiAnimTimer) {
      clearTimeout(kpiAnimTimer);
    }
    kpiAnimTimer = setTimeout(() => {
      animandoKpis.value = false;
    }, 460);
  },
  { deep: true },
);

// Sliding pill do filtro geográfico (.t-tabs)
const regiaoTabsRef = ref<HTMLElement | null>(null);
const regiaoPillRef = ref<HTMLElement | null>(null);
const regiaoTabEls = ref<Array<HTMLButtonElement | null>>([]);

function registrarTabRegiaoRef(el: Element | ComponentPublicInstance | null, idx: number): void {
  regiaoTabEls.value[idx] = el instanceof HTMLButtonElement ? el : null;
}

function posicionarPilulaRegiao(semTransicao = false): void {
  const pill = regiaoPillRef.value;
  const ativoIdx = OPCOES_REGIAO.findIndex((op) => op.value === filtros.value.regiao);
  const tabEl = regiaoTabEls.value[ativoIdx >= 0 ? ativoIdx : 0];
  if (!pill || !tabEl) {
    return;
  }

  if (semTransicao) {
    pill.style.transition = 'none';
  }
  pill.style.width = `${tabEl.offsetWidth}px`;
  pill.style.transform = `translateX(${tabEl.offsetLeft}px)`;
  if (semTransicao) {
    void pill.offsetWidth;
    pill.style.transition = '';
  }
}

function aoRedimensionar(): void {
  posicionarPilulaRegiao(true);
}

watch(
  () => filtros.value.regiao,
  async () => {
    await nextTick();
    posicionarPilulaRegiao(false);
  },
);

onMounted(async () => {
  relogioTimer = setInterval(() => {
    agoraMs.value = Date.now();
  }, 30000);
  window.addEventListener('resize', aoRedimensionar);
  await nextTick();
  posicionarPilulaRegiao(true);
});

onUnmounted(() => {
  if (relogioTimer) {
    clearInterval(relogioTimer);
  }
  if (kpiAnimTimer) {
    clearTimeout(kpiAnimTimer);
  }
  window.removeEventListener('resize', aoRedimensionar);
});

// Ações da barra de filtros e atalhos KPI
function selecionarRegiao(regiao: RegiaoGeografica | 'TODAS'): void {
  examesStore.definirFiltros({ regiao });
}

function alternarFiltroBooleano(campo: 'apenasTfd' | 'apenas24hVencidos' | 'apenasComAlertas'): void {
  examesStore.definirFiltros({ [campo]: !filtros.value[campo] });
}

function aplicarAtalhoKpi(atalho: 'NA_FILA' | 'AGUARDANDO_24H' | 'VENCIDOS_24H' | 'EXCECOES'): void {
  if (atalho === 'NA_FILA') {
    const jaAtivo =
      filtros.value.statusOperacional === 'NA_FILA' &&
      filtros.value.statusHigienizacao === 'VALIDA' &&
      !filtros.value.apenas24hVencidos;
    examesStore.definirFiltros({
      statusOperacional: jaAtivo ? 'TODOS' : 'NA_FILA',
      statusHigienizacao: jaAtivo ? 'TODOS' : 'VALIDA',
      apenas24hVencidos: false,
    });
    return;
  }
  if (atalho === 'AGUARDANDO_24H') {
    const jaAtivo =
      filtros.value.statusOperacional === 'AGUARDANDO_CONFIRMACAO_24H' &&
      !filtros.value.apenas24hVencidos;
    examesStore.definirFiltros({
      statusOperacional: jaAtivo ? 'TODOS' : 'AGUARDANDO_CONFIRMACAO_24H',
      statusHigienizacao: 'TODOS',
      apenas24hVencidos: false,
    });
    return;
  }
  if (atalho === 'VENCIDOS_24H') {
    examesStore.definirFiltros({
      apenas24hVencidos: !filtros.value.apenas24hVencidos,
      statusOperacional: 'TODOS',
    });
    return;
  }
  const jaEmExcecao = filtros.value.statusHigienizacao === 'NAO_ENCONTRADA';
  examesStore.definirFiltros({
    statusHigienizacao: jaEmExcecao ? 'TODOS' : 'NAO_ENCONTRADA',
    statusOperacional: 'TODOS',
    apenas24hVencidos: false,
  });
}

function aoDigitarBusca(event: Event): void {
  const target = event.target as HTMLInputElement;
  examesStore.definirFiltros({ busca: target.value });
}

function aoSelecionarExame(event: Event): void {
  const target = event.target as HTMLSelectElement;
  examesStore.definirFiltros({ codigoExame: target.value });
}

function aoSelecionarStatusOperacional(event: Event): void {
  const target = event.target as HTMLSelectElement;
  examesStore.definirFiltros({
    statusOperacional: target.value as StatusOperacional | 'TODOS',
  });
}

function aoSelecionarStatusHigienizacao(event: Event): void {
  const target = event.target as HTMLSelectElement;
  examesStore.definirFiltros({
    statusHigienizacao: target.value as StatusHigienizacao | 'TODOS',
  });
}

function limparTodosFiltros(): void {
  examesStore.limparFiltros();
}

// Modal 1: Atualizar Status 24h
const showStatusModal = ref(false);
const statusItemId = ref<number | null>(null);
const erroDataStatusShake = ref(false);
const erroDataStatusMensagem = ref('');

const statusForm = ref<{
  statusOperacional: StatusOperacional;
  dataAgendadaAghu: string;
  preparoOrientado: boolean;
  observacoes: string;
}>({
  statusOperacional: 'AGUARDANDO_CONFIRMACAO_24H',
  dataAgendadaAghu: '',
  preparoOrientado: true,
  observacoes: '',
});

const itemStatusAtual = computed<IItemFila | null>(() =>
  statusItemId.value !== null ? examesStore.obterDetalheItem(statusItemId.value) ?? null : null,
);

function paraDatetimeLocal(iso: string | null | undefined): string {
  if (!iso) {
    return '';
  }
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) {
    return '';
  }
  const ano = data.getFullYear();
  const mes = String(data.getMonth() + 1).padStart(2, '0');
  const dia = String(data.getDate()).padStart(2, '0');
  const hora = String(data.getHours()).padStart(2, '0');
  const min = String(data.getMinutes()).padStart(2, '0');
  return `${ano}-${mes}-${dia}T${hora}:${min}`;
}

function abrirModalStatus(item: IItemFila, statusSugerido?: StatusOperacional): void {
  statusItemId.value = item.id;
  erroDataStatusShake.value = false;
  erroDataStatusMensagem.value = '';
  statusForm.value = {
    statusOperacional: statusSugerido ?? item.statusOperacional,
    dataAgendadaAghu: paraDatetimeLocal(item.dataAgendadaAghu),
    preparoOrientado: item.preparoOrientado,
    observacoes: item.observacoes ?? '',
  };
  showStatusModal.value = true;
}

function fecharStatusModal(): void {
  showStatusModal.value = false;
  erroDataStatusShake.value = false;
  erroDataStatusMensagem.value = '';
}

function acionarShakeDataStatus(mensagem: string): void {
  erroDataStatusMensagem.value = mensagem;
  erroDataStatusShake.value = false;
  requestAnimationFrame(() => {
    erroDataStatusShake.value = true;
  });
}

async function salvarStatusOperacional(): Promise<void> {
  if (!itemStatusAtual.value) {
    return;
  }

  erroDataStatusMensagem.value = '';

  if (
    statusForm.value.statusOperacional === 'CONFIRMADO_AGENDADO_AGHU' &&
    !statusForm.value.dataAgendadaAghu
  ) {
    acionarShakeDataStatus('Informe a data e hora agendadas no AGHU para confirmar.');
    return;
  }

  try {
    const dataIso =
      statusForm.value.statusOperacional === 'CONFIRMADO_AGENDADO_AGHU' &&
      statusForm.value.dataAgendadaAghu
        ? new Date(statusForm.value.dataAgendadaAghu).toISOString()
        : null;

    const atualizado = await examesStore.atualizarStatusOperacional(itemStatusAtual.value.id, {
      statusOperacional: statusForm.value.statusOperacional,
      dataAgendadaAghu: dataIso,
      preparoOrientado: statusForm.value.preparoOrientado,
      observacoes: statusForm.value.observacoes.trim() || null,
    });

    toast.success(
      `Status de ${atualizado.nomePaciente} atualizado para "${rotuloStatusOperacional(atualizado.statusOperacional)}".`,
    );
    fecharStatusModal();
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Não foi possível atualizar o status.';
    toast.error(msg);
  }
}

// Modal 2: Busca Ativa no Espelho AGHU
const showAghuModal = ref(false);
const aghuItemId = ref<number | null>(null);
const resultadosAghu = ref<ISolicitacaoAghu[]>([]);
const aghuBuscaForm = ref({
  prontuario: '',
  codigoSolicitacao: '',
  nome: '',
});

const itemAghuAtual = computed<IItemFila | null>(() =>
  aghuItemId.value !== null ? examesStore.obterDetalheItem(aghuItemId.value) ?? null : null,
);

async function executarBuscaAghu(): Promise<void> {
  try {
    resultadosAghu.value = await examesStore.buscarNoAghu({
      prontuario: aghuBuscaForm.value.prontuario,
      codigoSolicitacao: aghuBuscaForm.value.codigoSolicitacao,
      nome: aghuBuscaForm.value.nome,
    });
  } catch {
    toast.error('Falha ao consultar o espelho AGHU.');
  }
}

async function abrirModalBuscaAghu(item: IItemFila): Promise<void> {
  aghuItemId.value = item.id;
  aghuBuscaForm.value = {
    prontuario: item.prontuario ?? '',
    codigoSolicitacao: '',
    nome: item.prontuario ? '' : item.nomePaciente,
  };
  showAghuModal.value = true;
  await executarBuscaAghu();
}

function fecharAghuModal(): void {
  showAghuModal.value = false;
}

async function vincularPedidoAghu(reg: ISolicitacaoAghu): Promise<void> {
  if (!itemAghuAtual.value) {
    return;
  }
  try {
    const atualizado = await examesStore.vincularSolicitacaoAghu(itemAghuAtual.value.id, {
      codigoSolicitacao: reg.codigoSolicitacao,
      codigoExame: reg.codigoExame,
    });
    toast.success(
      `Solicitação #${atualizado.codigoSolicitacao} (${atualizado.codigoExame}) vinculada ao paciente ${atualizado.nomePaciente}.`,
    );
    fecharAghuModal();
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Falha ao vincular solicitação do AGHU.';
    toast.error(msg);
  }
}

// Modal 3: Detalhes Clínicos
const showDetalhesModal = ref(false);
const detalhesItemId = ref<number | null>(null);

const itemDetalhesAtual = computed<IItemFila | null>(() =>
  detalhesItemId.value !== null ? examesStore.obterDetalheItem(detalhesItemId.value) ?? null : null,
);

function abrirModalDetalhes(item: IItemFila): void {
  detalhesItemId.value = item.id;
  showDetalhesModal.value = true;
}

function fecharDetalhesModal(): void {
  showDetalhesModal.value = false;
}

function trocarParaBuscaAghu(item: IItemFila): void {
  fecharDetalhesModal();
  void abrirModalBuscaAghu(item);
}

function trocarParaStatus(item: IItemFila): void {
  fecharDetalhesModal();
  abrirModalStatus(item);
}

async function copiarPreparo(item: IItemFila): Promise<void> {
  if (!item.orientacoesPreparo) {
    return;
  }
  const texto = `HC-UFPE — Orientações para ${item.nomeExame || item.codigoExame || 'Exame'} (#${item.codigoSolicitacao}): ${item.orientacoesPreparo}`;
  try {
    await navigator.clipboard.writeText(texto);
    toast.success('Orientações de preparo copiadas para envio.');
  } catch {
    toast.warning('Não foi possível acessar a área de transferência do navegador.');
  }
}

// Helpers visuais e formatação clínica
function precisaBuscaAghu(item: IItemFila): boolean {
  return (
    item.statusHigienizacao === 'NAO_ENCONTRADA' ||
    item.statusHigienizacao === 'DIVERGENCIA_EXAME'
  );
}

function ehPrazo24hVencido(item: IItemFila): boolean {
  if (item.statusOperacional !== 'AGUARDANDO_CONFIRMACAO_24H' || !item.prazoConfirmacaoEm) {
    return false;
  }
  const prazo = new Date(item.prazoConfirmacaoEm).getTime();
  return !Number.isNaN(prazo) && prazo < agoraMs.value;
}

function formatarTempo24h(prazoIso: string): string {
  const prazo = new Date(prazoIso).getTime();
  if (Number.isNaN(prazo)) {
    return 'Prazo indisponível';
  }
  const diffMs = prazo - agoraMs.value;
  if (diffMs <= 0) {
    const absMin = Math.floor(Math.abs(diffMs) / 60000);
    const horas = Math.floor(absMin / 60);
    const mins = absMin % 60;
    return horas > 0
      ? `Vencido há ${horas}h ${String(mins).padStart(2, '0')}m`
      : `Vencido há ${mins}m`;
  }
  const totalMin = Math.ceil(diffMs / 60000);
  const horas = Math.floor(totalMin / 60);
  const mins = totalMin % 60;
  return `Restam ${horas}h ${String(mins).padStart(2, '0')}m`;
}

function retornoProximo(dataRetorno: string): boolean {
  const data = new Date(`${dataRetorno.slice(0, 10)}T00:00:00`);
  if (Number.isNaN(data.getTime())) {
    return false;
  }
  const dias = Math.round((data.getTime() - agoraMs.value) / (24 * 60 * 60 * 1000));
  return dias <= 15;
}

function formatarDataCurta(valor: string | null | undefined): string {
  if (!valor) {
    return '—';
  }
  const limpo = valor.trim();
  const data = /^\d{4}-\d{2}-\d{2}$/.test(limpo)
    ? new Date(`${limpo}T00:00:00`)
    : new Date(limpo);
  if (Number.isNaN(data.getTime())) {
    return valor;
  }
  const d = String(data.getDate()).padStart(2, '0');
  const m = String(data.getMonth() + 1).padStart(2, '0');
  const a = data.getFullYear();
  return `${d}/${m}/${a}`;
}

function formatarDataHoraCurta(valor: string | null | undefined): string {
  if (!valor) {
    return '—';
  }
  const data = new Date(valor);
  if (Number.isNaN(data.getTime())) {
    return valor;
  }
  const hh = String(data.getHours()).padStart(2, '0');
  const mm = String(data.getMinutes()).padStart(2, '0');
  return `${formatarDataCurta(valor)} ${hh}:${mm}`;
}

function classeBadgeScore(score: number): string {
  if (score >= 100) {
    return 'bg-red-50 text-red-800 border border-red-200';
  }
  if (score >= 40) {
    return 'bg-teal-50 text-teal-800 border border-teal-200';
  }
  return 'bg-stone-100 text-stone-700 border border-stone-200';
}

function rotuloRegiao(regiao: RegiaoGeografica): string {
  switch (regiao) {
    case 'CAPITAL':
      return 'Capital';
    case 'RMR':
      return 'RMR';
    case 'INTERIOR':
      return 'Interior';
    default:
      return 'Não info.';
  }
}

function classeBadgeRegiao(regiao: RegiaoGeografica): string {
  switch (regiao) {
    case 'CAPITAL':
      return 'bg-emerald-50 text-emerald-800 border border-emerald-200';
    case 'RMR':
      return 'bg-sky-50 text-sky-800 border border-sky-200';
    case 'INTERIOR':
      return 'bg-amber-50 text-amber-800 border border-amber-200';
    default:
      return 'bg-stone-100 text-stone-700 border border-stone-200';
  }
}

function rotuloStatusOperacional(status: StatusOperacional): string {
  switch (status) {
    case 'NA_FILA':
      return 'Na Fila';
    case 'AGUARDANDO_CONFIRMACAO_24H':
      return 'Aguardando 24h';
    case 'CONFIRMADO_AGENDADO_AGHU':
      return 'Confirmado AGHU';
    case 'SEM_RESPOSTA_24H':
      return 'Sem Resposta 24h';
    case 'CANCELADO':
      return 'Cancelado';
  }
}

function classeBadgeStatusOperacional(status: StatusOperacional): string {
  switch (status) {
    case 'NA_FILA':
      return 'bg-stone-100 text-slate-700 border border-stone-200';
    case 'AGUARDANDO_CONFIRMACAO_24H':
      return 'bg-amber-50 text-amber-800 border border-amber-200';
    case 'CONFIRMADO_AGENDADO_AGHU':
      return 'bg-emerald-50 text-emerald-800 border border-emerald-200';
    case 'SEM_RESPOSTA_24H':
      return 'bg-red-50 text-red-800 border border-red-200';
    case 'CANCELADO':
      return 'bg-stone-100 text-stone-500 border border-stone-200';
  }
}

function rotuloHigienizacao(status: StatusHigienizacao): string {
  switch (status) {
    case 'VALIDA':
      return 'Válida';
    case 'DUPLICADA':
      return 'Duplicada';
    case 'DIVERGENCIA_EXAME':
      return 'Divergência AGHU';
    case 'NAO_ENCONTRADA':
      return 'Não Encontrada AGHU';
    case 'JA_REALIZADA':
      return 'Já Realizada';
  }
}

function classeBadgeHigienizacao(status: StatusHigienizacao): string {
  switch (status) {
    case 'VALIDA':
      return 'bg-emerald-50 text-emerald-800 border border-emerald-200';
    case 'DIVERGENCIA_EXAME':
    case 'NAO_ENCONTRADA':
      return 'bg-amber-50 text-amber-800 border border-amber-200';
    case 'DUPLICADA':
      return 'bg-red-50 text-red-800 border border-red-200';
    case 'JA_REALIZADA':
      return 'bg-stone-100 text-stone-700 border border-stone-200';
  }
}

function rotuloAlerta(tipo: TipoAlerta): string {
  switch (tipo) {
    case 'INCOMPATIBILIDADE':
      return 'Conflito Exame';
    case 'JANELA_RETORNO':
      return 'Janela Retorno';
    case 'ANTECEDENCIA_PREPARO':
      return 'Preparo';
    case 'JEJUM_CLINICO':
      return 'Jejum';
    case 'IDADE_MAMOGRAFIA':
      return 'Faixa Etária';
    case 'PRAZO_24H_VENCIDO':
      return '24h Vencido';
    case 'DUPLICIDADE':
      return 'Duplicidade';
  }
}

function classeBadgeAlerta(severidade: SeveridadeAlerta): string {
  switch (severidade) {
    case 'ALTA':
      return 'bg-red-50 text-red-800 border border-red-200';
    case 'MEDIA':
      return 'bg-amber-50 text-amber-800 border border-amber-200';
    case 'INFO':
      return 'bg-sky-50 text-sky-800 border border-sky-200';
  }
}
</script>
