<template>
  <div class="space-y-6">
    <!-- Cabeçalho e Aviso Institucional -->
    <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <div class="flex items-center gap-2.5">
          <ArrowUpTrayIcon class="h-7 w-7 text-teal-700 shrink-0" />
          <h1 class="text-2xl font-bold text-slate-800 tracking-tight">
            Importação e Higienização (Forms × AGHU)
          </h1>
        </div>
        <p class="text-sm text-slate-600 mt-1">
          Valide planilhas exportadas do Google Forms contra o espelho somente-leitura do AGHU antes de liberar solicitações para a fila priorizada.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button variant="default" type="button" @click="irParaFila()">
          <template #icon>
            <ArrowRightIcon class="h-4 w-4" />
          </template>
          Abrir Fila Priorizada
        </Button>
      </div>
    </div>

    <!-- Banner de Leitura Passiva -->
    <div
      class="flex items-start gap-3 rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900"
      role="status"
    >
      <ShieldCheckIcon class="h-5 w-5 text-sky-700 shrink-0 mt-0.5" />
      <p class="leading-relaxed">
        <strong>Leitura passiva somente-leitura:</strong> o arquivo original do Google Forms nunca é modificado; o cruzamento com o AGHU bloqueia duplicidades automaticamente e encaminha divergências ou códigos não localizados para Busca Ativa.
      </p>
    </div>

    <!-- Zona de Upload CSV / XLSX + Simulação Rápida -->
    <Card>
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <!-- Dropzone -->
        <div class="lg:col-span-8 flex flex-col">
          <div
            :class="[
              'flex-1 rounded-xl border-2 border-dashed p-6 text-center transition-[border-color,background-color] duration-200 flex flex-col items-center justify-center gap-3',
              arrastando
                ? 'border-teal-600 bg-teal-50/60'
                : arquivoSelecionado
                  ? 'border-emerald-300 bg-emerald-50/40'
                  : 'border-stone-300 bg-stone-50/70 hover:border-teal-500/70 hover:bg-stone-50',
              erroUploadShake ? 't-shake border-red-400 bg-red-50/40' : '',
            ]"
            @dragover.prevent="arrastando = true"
            @dragleave.prevent="arrastando = false"
            @drop.prevent="aoSoltarArquivo"
          >
            <input
              ref="inputArquivoRef"
              type="file"
              accept=".csv,.xlsx,.xls"
              class="sr-only"
              @change="aoSelecionarArquivo"
            />

            <div
              :class="[
                'flex h-12 w-12 items-center justify-center rounded-full border',
                arquivoSelecionado
                  ? 'border-emerald-200 bg-emerald-100 text-emerald-700'
                  : 'border-stone-200 bg-white text-teal-700',
              ]"
            >
              <DocumentArrowUpIcon class="h-6 w-6" />
            </div>

            <div v-if="!arquivoSelecionado" class="space-y-1">
              <p class="text-sm font-semibold text-slate-800">
                Arraste a planilha do Google Forms (.csv, .xlsx ou .xls) para esta área
              </p>
              <p class="text-xs text-slate-500">
                Colunas reconhecidas: Solicitação, Prontuário, Paciente, Telefone, Município, TFD, Exame e Data de Retorno.
              </p>
            </div>

            <div v-else class="space-y-1">
              <p class="text-sm font-bold text-slate-800 flex items-center justify-center gap-2">
                <DocumentTextIcon class="h-4 w-4 text-emerald-700 shrink-0" />
                <span>{{ arquivoSelecionado.name }}</span>
              </p>
              <p class="text-xs text-slate-500 tabular-nums">
                {{ formatarTamanhoArquivo(arquivoSelecionado.size) }} • Pronto para cruzamento Forms × AGHU
              </p>
            </div>

            <div class="flex flex-wrap items-center justify-center gap-2.5 pt-1">
              <button
                type="button"
                class="px-3.5 py-2 text-xs font-semibold rounded-md border border-stone-300 bg-white text-slate-700 hover:bg-stone-100 transition-colors cursor-pointer"
                :disabled="processando"
                @click="abrirSeletorArquivo"
              >
                {{ arquivoSelecionado ? 'Trocar Arquivo' : 'Selecionar Arquivo do Computador' }}
              </button>

              <Button
                v-if="arquivoSelecionado"
                variant="primary"
                type="button"
                :loading="processando"
                @click="processarArquivoSelecionado"
              >
                <template #icon>
                  <ArrowUpTrayIcon class="h-4 w-4" />
                </template>
                Processar Planilha
              </Button>

              <button
                v-if="arquivoSelecionado && !processando"
                type="button"
                class="px-2.5 py-2 text-xs font-semibold text-slate-500 hover:text-red-700 transition-colors cursor-pointer"
                @click="limparArquivoSelecionado"
              >
                Limpar
              </button>
            </div>

            <p v-if="erroArquivoMsg" class="text-xs font-semibold text-red-700 pt-1">
              {{ erroArquivoMsg }}
            </p>
          </div>
        </div>

        <!-- Ação Rápida de Demonstração (1 clique) -->
        <div
          class="lg:col-span-4 rounded-xl border border-stone-200 bg-stone-50/70 p-5 flex flex-col justify-between gap-4"
        >
          <div class="space-y-2">
            <span
              class="inline-flex items-center rounded-md border border-teal-200 bg-teal-50 px-2 py-0.5 text-xs font-semibold text-teal-800"
            >
              Modo Demonstração (HC-UFPE)
            </span>
            <h2 class="text-base font-bold text-slate-800">
              Simular Lote do Google Forms
            </h2>
            <p class="text-xs text-slate-600 leading-relaxed">
              Executa o motor de higienização com o lote sintético realista (10 solicitações contendo casos válidos, duplicidades barradas, divergência de exame, código não encontrado e exame já realizado).
            </p>
          </div>

          <div class="space-y-2.5">
            <Button
              variant="primary"
              type="button"
              class="w-full"
              :loading="processando"
              @click="simularLoteDemonstracao"
            >
              <template #icon>
                <PlayIcon class="h-4 w-4" />
              </template>
              Simular Lote de Demonstração
            </Button>
            <p class="text-[11px] text-slate-500 text-center">
              Insere automaticamente os itens elegíveis na Fila Priorizada.
            </p>
          </div>
        </div>
      </div>

      <!-- Etapas de Processamento Visual -->
      <div
        v-if="processando"
        class="mt-5 rounded-lg border border-stone-200 bg-stone-50 px-4 py-3.5 space-y-3"
        aria-live="polite"
      >
        <div class="flex items-center justify-between text-xs font-semibold text-slate-700">
          <span>Processando higienização Forms × AGHU...</span>
          <span class="tabular-nums text-teal-700">{{ Math.min(etapaProcessamento * 34, 100) }}%</span>
        </div>

        <div class="h-1.5 w-full overflow-hidden rounded-full bg-stone-200">
          <div
            class="h-full rounded-full bg-teal-600 transition-[width] duration-300 ease-out"
            :style="{ width: `${Math.min(etapaProcessamento * 34, 100)}%` }"
          ></div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
          <div
            v-for="(rotulo, idx) in ETAPAS_PROCESSAMENTO"
            :key="rotulo"
            :class="[
              'flex items-center gap-2 rounded-md border px-2.5 py-1.5 transition-colors duration-150',
              etapaProcessamento > idx
                ? 'border-emerald-200 bg-emerald-50 text-emerald-800 font-semibold'
                : etapaProcessamento === idx
                  ? 'border-teal-200 bg-teal-50 text-teal-800 font-semibold'
                  : 'border-stone-200 bg-white text-slate-400',
            ]"
          >
            <CheckCircleIcon v-if="etapaProcessamento > idx" class="h-4 w-4 text-emerald-600 shrink-0" />
            <ClockIcon v-else class="h-4 w-4 shrink-0" />
            <span>{{ rotulo }}</span>
          </div>
        </div>
      </div>
    </Card>

    <!-- Resumo da Higienização (5 KPI Cards com stagger 40ms e tabular-nums) -->
    <section v-if="loteAtual" class="space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h2 class="text-lg font-bold text-slate-800">
            Resumo da Higienização
          </h2>
          <p class="text-xs text-slate-500 mt-0.5">
            Lote <span class="font-mono font-semibold text-slate-700">#{{ loteAtual.id }}</span>
            • <span class="font-medium text-slate-700">{{ loteAtual.nomeArquivo }}</span>
            • Importado em <span class="tabular-nums">{{ formatarDataHora(loteAtual.importadoEm) }}</span>
            por <span class="font-mono text-slate-700">{{ loteAtual.usuarioImportador }}</span>
          </p>
        </div>

        <span
          class="inline-flex items-center gap-1.5 self-start sm:self-auto rounded-md border border-stone-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 tabular-nums"
        >
          Taxa de aproveitamento:
          <strong class="text-emerald-700">{{ taxaAproveitamento }}%</strong>
        </span>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 t-stagger">
        <!-- 1. Total Lidas -->
        <button
          type="button"
          :class="[
            't-kpi-card t-stagger-item text-left rounded-xl border bg-white p-4 shadow-paper cursor-pointer',
            filtroStatus === 'TODAS' ? 'border-teal-600 ring-1 ring-teal-600/20' : 'border-stone-200',
          ]"
          @click="selecionarFiltroStatus('TODAS')"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">Total Lidas</span>
            <DocumentTextIcon class="h-4 w-4 text-slate-400" />
          </div>
          <p
            :class="[
              'mt-2 text-2xl font-bold text-slate-800 tabular-nums t-subtle-number',
              animandoKpis ? 'is-animating' : '',
            ]"
          >
            {{ loteAtual.totalLinhas }}
          </p>
          <p class="mt-1 text-xs text-slate-500">Linhas lidas da planilha</p>
        </button>

        <!-- 2. Válidas -->
        <button
          type="button"
          :class="[
            't-kpi-card t-stagger-item text-left rounded-xl border bg-white p-4 shadow-paper cursor-pointer',
            filtroStatus === 'VALIDA' ? 'border-emerald-600 ring-1 ring-emerald-600/20' : 'border-stone-200',
          ]"
          @click="selecionarFiltroStatus('VALIDA')"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wide text-emerald-700">Válidas</span>
            <CheckCircleIcon class="h-4 w-4 text-emerald-600" />
          </div>
          <p
            :class="[
              'mt-2 text-2xl font-bold text-emerald-800 tabular-nums t-subtle-number',
              animandoKpis ? 'is-animating' : '',
            ]"
          >
            {{ loteAtual.totalValidas }}
          </p>
          <p class="mt-1 text-xs text-slate-500">Liberadas para a fila</p>
        </button>

        <!-- 3. Duplicadas -->
        <button
          type="button"
          :class="[
            't-kpi-card t-stagger-item text-left rounded-xl border bg-white p-4 shadow-paper cursor-pointer',
            filtroStatus === 'DUPLICADA' ? 'border-slate-600 ring-1 ring-slate-600/20' : 'border-stone-200',
          ]"
          @click="selecionarFiltroStatus('DUPLICADA')"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wide text-slate-600">Duplicadas</span>
            <DocumentDuplicateIcon class="h-4 w-4 text-slate-500" />
          </div>
          <p
            :class="[
              'mt-2 text-2xl font-bold text-slate-800 tabular-nums t-subtle-number',
              animandoKpis ? 'is-animating' : '',
            ]"
          >
            {{ loteAtual.totalDuplicadas }}
          </p>
          <p class="mt-1 text-xs text-slate-500">Reenvios barrados</p>
        </button>

        <!-- 4. Divergentes -->
        <button
          type="button"
          :class="[
            't-kpi-card t-stagger-item text-left rounded-xl border bg-white p-4 shadow-paper cursor-pointer',
            filtroStatus === 'DIVERGENCIA_EXAME' ? 'border-amber-600 ring-1 ring-amber-600/20' : 'border-stone-200',
          ]"
          @click="selecionarFiltroStatus('DIVERGENCIA_EXAME')"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wide text-amber-700">Divergentes</span>
            <ExclamationTriangleIcon class="h-4 w-4 text-amber-600" />
          </div>
          <p
            :class="[
              'mt-2 text-2xl font-bold text-amber-800 tabular-nums t-subtle-number',
              animandoKpis ? 'is-animating' : '',
            ]"
          >
            {{ loteAtual.totalDivergencias }}
          </p>
          <p class="mt-1 text-xs text-slate-500">Exame Forms ≠ AGHU</p>
        </button>

        <!-- 5. Não Encontradas / Já Realizadas -->
        <button
          type="button"
          :class="[
            't-kpi-card t-stagger-item text-left rounded-xl border bg-white p-4 shadow-paper cursor-pointer',
            filtroStatus === 'NAO_ENCONTRADA' ? 'border-red-600 ring-1 ring-red-600/20' : 'border-stone-200',
          ]"
          @click="selecionarFiltroStatus('NAO_ENCONTRADA')"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold uppercase tracking-wide text-red-700">Não Encontradas</span>
            <XCircleIcon class="h-4 w-4 text-red-600" />
          </div>
          <p
            :class="[
              'mt-2 text-2xl font-bold text-red-800 tabular-nums t-subtle-number',
              animandoKpis ? 'is-animating' : '',
            ]"
          >
            {{ loteAtual.totalNaoEncontradas }}
          </p>
          <p class="mt-1 text-xs text-slate-500 tabular-nums">
            <span v-if="loteAtual.totalJaRealizadas > 0">
              + {{ loteAtual.totalJaRealizadas }} já realizada{{ loteAtual.totalJaRealizadas === 1 ? '' : 's' }}
            </span>
            <span v-else>Encaminhar à Busca Ativa</span>
          </p>
        </button>
      </div>

      <!-- Relatório Detalhado por Linha Higienizada -->
      <Card>
        <div class="space-y-4">
          <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 border-b border-stone-200 pb-4">
            <div>
              <h3 class="text-base font-bold text-slate-800">
                Relatório Detalhado por Linha Higienizada
              </h3>
              <p class="text-xs text-slate-500 mt-0.5 tabular-nums">
                Exibindo {{ linhasFiltradas.length }} de {{ loteAtual.linhasPreview.length }} linhas pré-visualizadas neste lote.
              </p>
            </div>

            <!-- Abas deslizantes de filtro por status -->
            <div class="overflow-x-auto pb-0.5">
              <div
                ref="tabsFiltroContainerRef"
                class="t-tabs"
                role="tablist"
                aria-label="Filtrar linhas por classificação de higienização"
              >
                <span ref="tabsFiltroPillRef" class="t-tabs-pill" aria-hidden="true"></span>
                <button
                  v-for="tab in ABAS_FILTRO"
                  :key="tab.valor"
                  :ref="(el) => registrarRefAbaFiltro(tab.valor, el)"
                  type="button"
                  role="tab"
                  class="t-tab flex items-center gap-1.5"
                  :aria-selected="filtroStatus === tab.valor"
                  @click="selecionarFiltroStatus(tab.valor)"
                >
                  <span>{{ tab.label }}</span>
                  <span
                    class="rounded-full bg-stone-200/80 px-1.5 py-0.5 text-[11px] font-bold text-slate-700 tabular-nums"
                  >
                    {{ contagemPorStatus[tab.valor] }}
                  </span>
                </button>
              </div>
            </div>
          </div>

          <div v-if="linhasFiltradas.length === 0" class="py-10 text-center space-y-1">
            <p class="text-sm font-semibold text-slate-700">
              Nenhuma linha encontrada com o filtro selecionado.
            </p>
            <p class="text-xs text-slate-500">
              Selecione "Todas" ou escolha outra classificação para inspecionar o lote.
            </p>
          </div>

          <div v-else class="overflow-x-auto">
            <table class="w-full text-left text-sm text-slate-700">
              <thead class="border-b border-stone-200 bg-stone-50 text-xs font-semibold uppercase text-slate-500">
                <tr>
                  <th class="py-3 px-3 w-14 text-center">Linha</th>
                  <th class="py-3 px-3">Solicitação</th>
                  <th class="py-3 px-3">Paciente & Prontuário</th>
                  <th class="py-3 px-3">Exame (Forms × AGHU)</th>
                  <th class="py-3 px-3">Classificação</th>
                  <th class="py-3 px-3">Detalhe da Higienização</th>
                  <th class="py-3 px-3 text-right">Ação</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-stone-100">
                <tr
                  v-for="linha in linhasFiltradas"
                  :key="`${loteAtual.id}-${linha.linhaNumero}-${linha.codigoSolicitacaoInformado}`"
                  class="hover:bg-stone-50/80 transition-colors duration-150"
                >
                  <td class="py-3 px-3 text-center font-mono text-xs font-semibold text-slate-500 tabular-nums">
                    #{{ linha.linhaNumero }}
                  </td>

                  <td class="py-3 px-3 align-top">
                    <span class="font-mono text-xs font-bold text-slate-800 tabular-nums">
                      {{ linha.codigoSolicitacaoInformado }}
                    </span>
                    <p v-if="linha.dataRetornoMedico" class="text-[11px] text-slate-500 mt-0.5 tabular-nums">
                      Retorno: {{ formatarDataCurta(linha.dataRetornoMedico) }}
                    </p>
                  </td>

                  <td class="py-3 px-3 align-top">
                    <p class="font-semibold text-slate-800 leading-snug">
                      {{ linha.nomePaciente }}
                    </p>
                    <div class="mt-1 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
                      <span
                        v-if="linha.prontuario"
                        class="font-mono text-[11px] rounded bg-stone-100 border border-stone-200 px-1.5 py-0.5 text-slate-700 tabular-nums"
                      >
                        Pront. {{ linha.prontuario }}
                      </span>
                      <span
                        v-else
                        class="text-[11px] rounded bg-amber-50 border border-amber-200 px-1.5 py-0.5 text-amber-800 font-medium"
                      >
                        Sem prontuário
                      </span>

                      <span v-if="linha.municipio" class="text-[11px] text-slate-600">
                        {{ linha.municipio }}
                      </span>

                      <span
                        :class="classeRegiao(linha.regiaoGeografica)"
                        class="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase"
                      >
                        {{ rotuloRegiao(linha.regiaoGeografica) }}
                      </span>

                      <span
                        v-if="linha.utilizaTfd"
                        class="rounded border border-sky-200 bg-sky-50 px-1.5 py-0.5 text-[10px] font-bold text-sky-800"
                      >
                        TFD
                      </span>
                    </div>
                  </td>

                  <td class="py-3 px-3 align-top max-w-xs">
                    <div class="space-y-1">
                      <p class="text-xs text-slate-600">
                        <span class="font-semibold text-slate-500">Forms:</span>
                        {{ linha.exameInformadoForms }}
                      </p>
                      <div v-if="linha.codigoExameAghu" class="flex flex-wrap items-center gap-1.5">
                        <span class="text-xs font-semibold text-slate-500">AGHU:</span>
                        <span
                          :class="[
                            'font-mono text-xs font-bold rounded px-1.5 py-0.5 border',
                            linha.statusHigienizacao === 'DIVERGENCIA_EXAME'
                              ? 'border-amber-300 bg-amber-50 text-amber-900'
                              : 'border-teal-200 bg-teal-50 text-teal-800',
                          ]"
                        >
                          {{ linha.codigoExameAghu }}
                        </span>
                        <span class="text-xs text-slate-700 truncate max-w-[200px]" :title="linha.nomeExameAghu || ''">
                          {{ linha.nomeExameAghu }}
                        </span>
                      </div>
                      <p v-else class="text-xs font-medium text-red-700">
                        AGHU: Pedido não localizado
                      </p>
                      <p v-if="linha.unidadeSolicitante" class="text-[11px] text-slate-500">
                        {{ linha.unidadeSolicitante }}
                      </p>
                    </div>
                  </td>

                  <td class="py-3 px-3 align-top whitespace-nowrap">
                    <span
                      :class="classeStatusHigienizacao(linha.statusHigienizacao)"
                      class="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-bold"
                    >
                      {{ rotuloStatusHigienizacao(linha.statusHigienizacao) }}
                    </span>
                  </td>

                  <td class="py-3 px-3 align-top text-xs text-slate-600 leading-relaxed max-w-sm">
                    {{ linha.detalheHigienizacao }}
                  </td>

                  <td class="py-3 px-3 align-top text-right whitespace-nowrap">
                    <button
                      v-if="
                        linha.statusHigienizacao === 'NAO_ENCONTRADA' ||
                        linha.statusHigienizacao === 'DIVERGENCIA_EXAME'
                      "
                      type="button"
                      class="inline-flex items-center gap-1 rounded-md border border-amber-300 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-900 hover:bg-amber-100 transition-colors cursor-pointer"
                      @click="abrirNaFila(linha)"
                    >
                      <MagnifyingGlassIcon class="h-3.5 w-3.5" />
                      Buscar no AGHU
                    </button>

                    <button
                      v-else-if="linha.statusHigienizacao === 'VALIDA'"
                      type="button"
                      class="inline-flex items-center gap-1 rounded-md border border-stone-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-stone-100 transition-colors cursor-pointer"
                      @click="abrirNaFila(linha)"
                    >
                      Abrir na Fila
                      <ArrowRightIcon class="h-3.5 w-3.5" />
                    </button>

                    <span v-else class="text-xs text-slate-400">Barrado</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Card>
    </section>

    <!-- Histórico de Importações Anteriores -->
    <Card>
      <div class="space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-stone-200 pb-3">
          <div>
            <h2 class="text-base font-bold text-slate-800">
              Histórico de Importações Anteriores
            </h2>
            <p class="text-xs text-slate-500 mt-0.5">
              Clique em um lote para carregar o resumo e inspecionar o relatório detalhado acima.
            </p>
          </div>
          <span class="text-xs font-semibold text-slate-500 tabular-nums">
            {{ examesStore.historicoImportacoes.length }} lotes registrados
          </span>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-slate-700">
            <thead class="border-b border-stone-200 bg-stone-50 text-xs font-semibold uppercase text-slate-500">
              <tr>
                <th class="py-3 px-3">Lote / Arquivo</th>
                <th class="py-3 px-3">Data / Hora</th>
                <th class="py-3 px-3">Responsável</th>
                <th class="py-3 px-3 text-right">Lidas</th>
                <th class="py-3 px-3 text-right">Válidas</th>
                <th class="py-3 px-3 text-right">Duplicadas</th>
                <th class="py-3 px-3 text-right">Divergentes</th>
                <th class="py-3 px-3 text-right">Não Enc.</th>
                <th class="py-3 px-3 text-right">Ação</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-100">
              <tr
                v-for="imp in examesStore.historicoImportacoes"
                :key="imp.id"
                :class="[
                  'cursor-pointer transition-colors duration-150',
                  loteAtual?.id === imp.id
                    ? 'bg-teal-50/70'
                    : 'hover:bg-stone-50/80',
                ]"
                @click="inspecionarImportacao(imp.id)"
              >
                <td class="py-3 px-3">
                  <div class="flex items-center gap-2">
                    <span class="font-mono text-xs font-bold text-slate-500 tabular-nums">#{{ imp.id }}</span>
                    <span class="font-semibold text-slate-800">{{ imp.nomeArquivo }}</span>
                    <span
                      v-if="loteAtual?.id === imp.id"
                      class="rounded border border-teal-200 bg-teal-50 px-1.5 py-0.5 text-[10px] font-bold text-teal-800"
                    >
                      Em exibição
                    </span>
                  </div>
                </td>
                <td class="py-3 px-3 text-xs text-slate-600 tabular-nums whitespace-nowrap">
                  {{ formatarDataHora(imp.importadoEm) }}
                </td>
                <td class="py-3 px-3 font-mono text-xs text-slate-600">
                  {{ imp.usuarioImportador }}
                </td>
                <td class="py-3 px-3 text-right font-semibold text-slate-800 tabular-nums">
                  {{ imp.totalLinhas }}
                </td>
                <td class="py-3 px-3 text-right font-semibold text-emerald-700 tabular-nums">
                  {{ imp.totalValidas }}
                </td>
                <td class="py-3 px-3 text-right text-slate-600 tabular-nums">
                  {{ imp.totalDuplicadas }}
                </td>
                <td class="py-3 px-3 text-right text-amber-700 font-semibold tabular-nums">
                  {{ imp.totalDivergencias }}
                </td>
                <td class="py-3 px-3 text-right text-red-700 font-semibold tabular-nums">
                  {{ imp.totalNaoEncontradas }}
                </td>
                <td class="py-3 px-3 text-right whitespace-nowrap">
                  <button
                    type="button"
                    class="rounded-md border border-stone-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-stone-100 transition-colors cursor-pointer"
                    @click.stop="inspecionarImportacao(imp.id)"
                  >
                    Inspecionar Relatório
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import {
  ArrowRightIcon,
  ArrowUpTrayIcon,
  CheckCircleIcon,
  ClockIcon,
  DocumentArrowUpIcon,
  DocumentDuplicateIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  PlayIcon,
  ShieldCheckIcon,
  XCircleIcon,
} from '@heroicons/vue/24/outline';
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import type { ComponentPublicInstance } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'vue-toastification';
import Button from '../components/Button.vue';
import Card from '../components/Card.vue';
import { useAuthStore } from '../stores/auth';
import { useExamesStore } from '../stores/exames';
import type {
  ILinhaHigienizadaPreview,
  RegiaoGeografica,
  StatusHigienizacao,
} from '../types/exames';

type FiltroStatusImportacao = 'TODAS' | StatusHigienizacao;

const ETAPAS_PROCESSAMENTO = [
  '1. Lendo linhas do Forms',
  '2. Cruzando solicitações no AGHU',
  '3. Calculando higienização',
] as const;

const ABAS_FILTRO: Array<{ valor: FiltroStatusImportacao; label: string }> = [
  { valor: 'TODAS', label: 'Todas' },
  { valor: 'VALIDA', label: 'Válidas' },
  { valor: 'DUPLICADA', label: 'Duplicadas' },
  { valor: 'DIVERGENCIA_EXAME', label: 'Divergentes' },
  { valor: 'NAO_ENCONTRADA', label: 'Não Encontradas' },
  { valor: 'JA_REALIZADA', label: 'Já Realizadas' },
];

const examesStore = useExamesStore();
const authStore = useAuthStore();
const router = useRouter();
const toast = useToast();

const inputArquivoRef = ref<HTMLInputElement | null>(null);
const arquivoSelecionado = ref<File | null>(null);
const arrastando = ref(false);
const processando = ref(false);
const etapaProcessamento = ref(0);
const erroArquivoMsg = ref('');
const erroUploadShake = ref(false);
const animandoKpis = ref(false);

const filtroStatus = ref<FiltroStatusImportacao>('TODAS');
const tabsFiltroContainerRef = ref<HTMLElement | null>(null);
const tabsFiltroPillRef = ref<HTMLElement | null>(null);
const abasFiltroRefs = new Map<FiltroStatusImportacao, HTMLElement>();

const loteAtual = computed(() => examesStore.ultimaImportacao);

const taxaAproveitamento = computed(() => {
  const lote = loteAtual.value;
  if (!lote || lote.totalLinhas === 0) {
    return 0;
  }
  return Math.round((lote.totalValidas / lote.totalLinhas) * 100);
});

const contagemPorStatus = computed<Record<FiltroStatusImportacao, number>>(() => {
  const linhas = loteAtual.value?.linhasPreview ?? [];
  return {
    TODAS: linhas.length,
    VALIDA: linhas.filter((l) => l.statusHigienizacao === 'VALIDA').length,
    DUPLICADA: linhas.filter((l) => l.statusHigienizacao === 'DUPLICADA').length,
    DIVERGENCIA_EXAME: linhas.filter((l) => l.statusHigienizacao === 'DIVERGENCIA_EXAME').length,
    NAO_ENCONTRADA: linhas.filter((l) => l.statusHigienizacao === 'NAO_ENCONTRADA').length,
    JA_REALIZADA: linhas.filter((l) => l.statusHigienizacao === 'JA_REALIZADA').length,
  };
});

const linhasFiltradas = computed<ILinhaHigienizadaPreview[]>(() => {
  const linhas = loteAtual.value?.linhasPreview ?? [];
  if (filtroStatus.value === 'TODAS') {
    return linhas;
  }
  return linhas.filter((linha) => linha.statusHigienizacao === filtroStatus.value);
});

function registrarRefAbaFiltro(
  chave: FiltroStatusImportacao,
  el: Element | ComponentPublicInstance | null,
): void {
  if (el instanceof HTMLElement) {
    abasFiltroRefs.set(chave, el);
  } else {
    abasFiltroRefs.delete(chave);
  }
}

function posicionarPilulaFiltro(semTransicao = false): void {
  const pill = tabsFiltroPillRef.value;
  const activeBtn = abasFiltroRefs.get(filtroStatus.value);
  if (!pill || !activeBtn) {
    return;
  }

  if (semTransicao) {
    pill.style.transition = 'none';
  }

  pill.style.width = `${activeBtn.offsetWidth}px`;
  pill.style.transform = `translateX(${activeBtn.offsetLeft}px)`;

  if (semTransicao) {
    void pill.offsetWidth;
    pill.style.transition = '';
  }
}

function aoRedimensionar(): void {
  posicionarPilulaFiltro(true);
}

function dispararAnimacaoKpis(): void {
  animandoKpis.value = false;
  requestAnimationFrame(() => {
    animandoKpis.value = true;
    setTimeout(() => {
      animandoKpis.value = false;
    }, 480);
  });
}

function dispararShakeErro(mensagem: string): void {
  erroArquivoMsg.value = mensagem;
  erroUploadShake.value = false;
  requestAnimationFrame(() => {
    erroUploadShake.value = true;
    setTimeout(() => {
      erroUploadShake.value = false;
    }, 320);
  });
}

function validarExtensaoArquivo(file: File): boolean {
  return /\.(csv|xlsx|xls)$/i.test(file.name);
}

function abrirSeletorArquivo(): void {
  inputArquivoRef.value?.click();
}

function aoSelecionarArquivo(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) {
    return;
  }
  if (!validarExtensaoArquivo(file)) {
    dispararShakeErro('Formato não suportado. Envie uma planilha .csv, .xlsx ou .xls do Google Forms.');
    input.value = '';
    return;
  }
  erroArquivoMsg.value = '';
  arquivoSelecionado.value = file;
}

function aoSoltarArquivo(event: DragEvent): void {
  arrastando.value = false;
  const file = event.dataTransfer?.files?.[0];
  if (!file) {
    return;
  }
  if (!validarExtensaoArquivo(file)) {
    dispararShakeErro('Formato não suportado. Arraste um arquivo .csv, .xlsx ou .xls.');
    return;
  }
  erroArquivoMsg.value = '';
  arquivoSelecionado.value = file;
}

function limparArquivoSelecionado(): void {
  arquivoSelecionado.value = null;
  erroArquivoMsg.value = '';
  if (inputArquivoRef.value) {
    inputArquivoRef.value.value = '';
  }
}

function aguardarMs(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

async function executarImportacao(arquivo: File | null): Promise<void> {
  if (processando.value) {
    return;
  }

  processando.value = true;
  erroArquivoMsg.value = '';
  etapaProcessamento.value = 1;

  try {
    await aguardarMs(140);
    etapaProcessamento.value = 2;

    const usuario = authStore.user?.username || 'marcador.central';
    const lote = await examesStore.processarUploadForms(arquivo, usuario);

    etapaProcessamento.value = 3;
    await aguardarMs(140);

    filtroStatus.value = 'TODAS';
    limparArquivoSelecionado();
    dispararAnimacaoKpis();

    await nextTick();
    posicionarPilulaFiltro(true);

    toast.success(
      `Higienização concluída (${lote.nomeArquivo}): ${lote.totalValidas} válidas, ${lote.totalDuplicadas} duplicadas barradas e ${lote.totalDivergencias + lote.totalNaoEncontradas} para revisão.`,
    );
  } catch (err) {
    const mensagem = err instanceof Error ? err.message : 'Falha ao processar a planilha do Forms.';
    dispararShakeErro(mensagem);
    toast.error(mensagem);
  } finally {
    processando.value = false;
    etapaProcessamento.value = 0;
  }
}

async function processarArquivoSelecionado(): Promise<void> {
  if (!arquivoSelecionado.value) {
    dispararShakeErro('Selecione uma planilha .csv, .xlsx ou .xls antes de processar.');
    return;
  }
  await executarImportacao(arquivoSelecionado.value);
}

async function simularLoteDemonstracao(): Promise<void> {
  await executarImportacao(null);
}

function selecionarFiltroStatus(status: FiltroStatusImportacao): void {
  filtroStatus.value = status;
}

function inspecionarImportacao(id: number): void {
  examesStore.selecionarImportacao(id);
  filtroStatus.value = 'TODAS';
  dispararAnimacaoKpis();
  nextTick(() => {
    posicionarPilulaFiltro(true);
  });
}

function irParaFila(): void {
  router.push('/fila');
}

function abrirNaFila(linha: ILinhaHigienizadaPreview): void {
  examesStore.limparFiltros();
  examesStore.definirFiltros({
    busca: linha.codigoSolicitacaoInformado,
    statusHigienizacao: linha.statusHigienizacao,
  });
  router.push('/fila');
}

function formatarTamanhoArquivo(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatarDataHora(iso: string): string {
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) {
    return iso;
  }
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(data);
}

function formatarDataCurta(valor: string): string {
  const limpo = valor.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(limpo)) {
    const [ano, mes, dia] = limpo.split('-');
    return `${dia}/${mes}/${ano}`;
  }
  const data = new Date(limpo);
  if (Number.isNaN(data.getTime())) {
    return valor;
  }
  return new Intl.DateTimeFormat('pt-BR').format(data);
}

function rotuloStatusHigienizacao(status: StatusHigienizacao): string {
  switch (status) {
    case 'VALIDA':
      return 'Válida';
    case 'DUPLICADA':
      return 'Duplicada';
    case 'DIVERGENCIA_EXAME':
      return 'Divergência';
    case 'NAO_ENCONTRADA':
      return 'Não Encontrada';
    case 'JA_REALIZADA':
      return 'Já Realizada';
  }
}

function classeStatusHigienizacao(status: StatusHigienizacao): string {
  switch (status) {
    case 'VALIDA':
      return 'bg-emerald-50 text-emerald-800 border border-emerald-200';
    case 'DUPLICADA':
      return 'bg-stone-100 text-stone-700 border border-stone-200';
    case 'DIVERGENCIA_EXAME':
      return 'bg-amber-50 text-amber-800 border border-amber-200';
    case 'NAO_ENCONTRADA':
      return 'bg-red-50 text-red-800 border border-red-200';
    case 'JA_REALIZADA':
      return 'bg-sky-50 text-sky-800 border border-sky-200';
  }
}

function rotuloRegiao(regiao: RegiaoGeografica): string {
  switch (regiao) {
    case 'CAPITAL':
      return 'Capital';
    case 'RMR':
      return 'RMR';
    case 'INTERIOR':
      return 'Interior';
    case 'NAO_INFORMADO':
      return 'N/I';
  }
}

function classeRegiao(regiao: RegiaoGeografica): string {
  switch (regiao) {
    case 'CAPITAL':
      return 'bg-teal-50 text-teal-800 border border-teal-200';
    case 'RMR':
      return 'bg-sky-50 text-sky-800 border border-sky-200';
    case 'INTERIOR':
      return 'bg-amber-50 text-amber-800 border border-amber-200';
    case 'NAO_INFORMADO':
      return 'bg-stone-100 text-stone-700 border border-stone-200';
  }
}

watch(filtroStatus, async () => {
  await nextTick();
  posicionarPilulaFiltro(false);
});

watch(
  () => loteAtual.value?.id,
  async () => {
    await nextTick();
    posicionarPilulaFiltro(true);
  },
);

onMounted(async () => {
  await nextTick();
  posicionarPilulaFiltro(true);
  window.addEventListener('resize', aoRedimensionar);
});

onUnmounted(() => {
  window.removeEventListener('resize', aoRedimensionar);
});
</script>
