<template>
  <div class="space-y-6">
    <!-- Cabeçalho de Governança -->
    <div class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <div class="flex items-center gap-2.5">
          <AdjustmentsHorizontalIcon class="h-7 w-7 text-teal-700 shrink-0" />
          <h1 class="text-2xl font-bold text-slate-800 tracking-tight">
            Parâmetros Clínicos e Regras de Triagem
          </h1>
        </div>
        <p class="text-sm text-slate-600 mt-1">
          Configure pesos de prioridade clínica, regras operacionais por exame e a matriz de incompatibilidades da Central de Marcação.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2.5">
        <button
          type="button"
          class="inline-flex items-center gap-1.5 rounded-md border border-stone-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-stone-100 transition-colors cursor-pointer"
          :disabled="regrasStore.carregando"
          @click="recarregarDoServidor"
        >
          <ArrowPathIcon class="h-4 w-4 text-slate-500" />
          Recarregar do Servidor
        </button>

        <Button variant="default" type="button" @click="router.push('/fila')">
          <template #icon>
            <ArrowRightIcon class="h-4 w-4" />
          </template>
          Ver Impacto na Fila
        </Button>
      </div>
    </div>

    <!-- Aviso de Governança / Auditoria -->
    <div
      class="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
      role="status"
    >
      <ShieldCheckIcon class="h-5 w-5 text-amber-700 shrink-0 mt-0.5" />
      <p class="leading-relaxed">
        <strong>Governança e Auditoria:</strong> alterações entram em vigor imediatamente no recálculo de scores e alertas da Fila de Exames e são auditadas na categoria <span class="font-mono text-xs font-bold">CONFIGURACAO</span> com exclusão lógica (Soft Delete).
      </p>
    </div>

    <!-- Navegação em 3 Abas com Pílula Deslizante (.t-tabs) -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <div class="overflow-x-auto pb-0.5">
        <div
          ref="tabsContainerRef"
          class="t-tabs"
          role="tablist"
          aria-label="Seções de regras clínicas"
        >
          <span ref="tabsPillRef" class="t-tabs-pill" aria-hidden="true"></span>
          <button
            v-for="aba in ABAS_REGRAS"
            :key="aba.id"
            :ref="(el) => registrarRefAba(aba.id, el)"
            type="button"
            role="tab"
            class="t-tab flex items-center gap-2"
            :aria-selected="abaAtiva === aba.id"
            @click="abaAtiva = aba.id"
          >
            <span>{{ aba.label }}</span>
            <span
              class="rounded-full bg-stone-200/80 px-1.5 py-0.5 text-[11px] font-bold text-slate-700 tabular-nums"
            >
              {{ contagemAba[aba.id] }}
            </span>
          </button>
        </div>
      </div>

      <div>
        <Button
          v-if="abaAtiva === 'prioridades'"
          variant="primary"
          type="button"
          @click="abrirModalPrioridade()"
        >
          <template #icon>
            <PlusIcon class="h-4 w-4" />
          </template>
          Novo Critério de Prioridade
        </Button>

        <Button
          v-else-if="abaAtiva === 'exames'"
          variant="primary"
          type="button"
          @click="abrirModalExame()"
        >
          <template #icon>
            <PlusIcon class="h-4 w-4" />
          </template>
          Nova Regra de Exame
        </Button>

        <Button
          v-else
          variant="primary"
          type="button"
          @click="abrirModalIncompatibilidade()"
        >
          <template #icon>
            <PlusIcon class="h-4 w-4" />
          </template>
          Novo Par Incompatível
        </Button>
      </div>
    </div>

    <!-- ABA 1: PESOS DE PRIORIDADE -->
    <Card v-if="abaAtiva === 'prioridades'">
      <div class="space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-stone-200 pb-3">
          <div>
            <h2 class="text-base font-bold text-slate-800">
              1. Pesos de Prioridade Clínica
            </h2>
            <p class="text-xs text-slate-500 mt-0.5">
              Ordenados por peso decrescente. O motor aplica o maior peso de grupo clínico somado aos bônus ativos (retorno próximo e afinidade).
            </p>
          </div>
          <span class="text-xs font-semibold text-slate-500 tabular-nums">
            Maior peso ativo: <strong class="text-teal-800">{{ maiorPesoPrioridade }} pts</strong>
          </span>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-slate-700">
            <thead class="border-b border-stone-200 bg-stone-50 text-xs font-semibold uppercase text-slate-500">
              <tr>
                <th class="py-3 px-3">Código</th>
                <th class="py-3 px-3">Critério & Descrição</th>
                <th class="py-3 px-3">Tipo</th>
                <th class="py-3 px-3">Termos de Match</th>
                <th class="py-3 px-3 w-48">Peso Clínico</th>
                <th class="py-3 px-3 text-center">Ativo</th>
                <th class="py-3 px-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-100">
              <tr
                v-for="regra in regrasStore.prioridadesAtivas"
                :key="regra.id"
                :class="[
                  'transition-colors duration-150',
                  regra.ativo ? 'hover:bg-stone-50/80' : 'bg-stone-50/50 text-slate-400',
                ]"
              >
                <td class="py-3 px-3 align-top">
                  <span class="font-mono text-xs font-bold text-slate-700">
                    {{ regra.codigo }}
                  </span>
                </td>

                <td class="py-3 px-3 align-top max-w-xs">
                  <p :class="['font-semibold', regra.ativo ? 'text-slate-800' : 'text-slate-500 line-through']">
                    {{ regra.nome }}
                  </p>
                  <p v-if="regra.descricao" class="text-xs text-slate-500 mt-0.5 leading-relaxed">
                    {{ regra.descricao }}
                  </p>
                </td>

                <td class="py-3 px-3 align-top whitespace-nowrap">
                  <span
                    :class="classeTipoCriterio(regra.tipoCriterio)"
                    class="inline-flex rounded-md px-2 py-0.5 text-[11px] font-bold"
                  >
                    {{ rotuloTipoCriterio(regra.tipoCriterio) }}
                  </span>
                </td>

                <td class="py-3 px-3 align-top">
                  <span class="font-mono text-xs rounded border border-stone-200 bg-stone-50 px-2 py-0.5 text-slate-700 inline-block">
                    {{ regra.valorMatch }}
                  </span>
                </td>

                <td class="py-3 px-3 align-top">
                  <div class="space-y-1.5">
                    <div class="flex items-center justify-between text-xs">
                      <span
                        :class="[
                          'font-bold tabular-nums',
                          regra.ativo ? 'text-slate-800' : 'text-slate-400',
                        ]"
                      >
                        +{{ regra.peso }} pts
                      </span>
                      <span class="text-[11px] text-slate-400 tabular-nums">
                        {{ percentualPeso(regra.peso) }}%
                      </span>
                    </div>
                    <div class="h-1.5 w-full overflow-hidden rounded-full bg-stone-200">
                      <div
                        :class="[
                          'h-full rounded-full transition-[width] duration-300 ease-out',
                          regra.ativo ? 'bg-teal-600' : 'bg-stone-400',
                        ]"
                        :style="{ width: `${percentualPeso(regra.peso)}%` }"
                      ></div>
                    </div>
                  </div>
                </td>

                <td class="py-3 px-3 align-top text-center">
                  <button
                    type="button"
                    role="switch"
                    :aria-checked="regra.ativo"
                    :aria-label="`Alternar status da regra ${regra.nome}`"
                    :disabled="regrasStore.carregando"
                    :class="[
                      'relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors duration-150 cursor-pointer focus:outline-none focus:ring-2 focus:ring-teal-600/30',
                      regra.ativo ? 'bg-emerald-600' : 'bg-stone-300',
                    ]"
                    @click="alternarPrioridade(regra)"
                  >
                    <span
                      :class="[
                        'inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform duration-150',
                        regra.ativo ? 'translate-x-[18px]' : 'translate-x-1',
                      ]"
                    ></span>
                  </button>
                </td>

                <td class="py-3 px-3 align-top text-right whitespace-nowrap space-x-1.5">
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 rounded-md border border-stone-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-stone-100 transition-colors cursor-pointer"
                    @click="abrirModalPrioridade(regra)"
                  >
                    <PencilSquareIcon class="h-3.5 w-3.5" />
                    Editar
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 rounded-md border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700 hover:bg-red-100 transition-colors cursor-pointer"
                    @click="solicitarRemocao('prioridade', regra.id, `${regra.codigo} (${regra.nome})`)"
                  >
                    <TrashIcon class="h-3.5 w-3.5" />
                    Remover
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Card>

    <!-- ABA 2: REGRAS POR EXAME -->
    <Card v-else-if="abaAtiva === 'exames'">
      <div class="space-y-4">
        <div class="border-b border-stone-200 pb-3">
          <h2 class="text-base font-bold text-slate-800">
            2. Regras Operacionais e Clínicas por Exame
          </h2>
          <p class="text-xs text-slate-500 mt-0.5">
            Define antecedência mínima de preparo, janela máxima antes do retorno médico, exigência de jejum, prioridade matutina para diabéticos e alerta etário.
          </p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-slate-700">
            <thead class="border-b border-stone-200 bg-stone-50 text-xs font-semibold uppercase text-slate-500">
              <tr>
                <th class="py-3 px-3">Sigla AGHU</th>
                <th class="py-3 px-3">Exame & Unidade Executora</th>
                <th class="py-3 px-3">Parâmetros Clínicos</th>
                <th class="py-3 px-3">Orientações de Preparo</th>
                <th class="py-3 px-3 text-center">Ativo</th>
                <th class="py-3 px-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-100">
              <tr
                v-for="exame in regrasStore.examesAtivos"
                :key="exame.id"
                :class="[
                  'transition-colors duration-150',
                  exame.ativo ? 'hover:bg-stone-50/80' : 'bg-stone-50/50 text-slate-400',
                ]"
              >
                <td class="py-3 px-3 align-top">
                  <span
                    class="font-mono text-xs font-bold rounded border border-teal-200 bg-teal-50 px-2 py-0.5 text-teal-800"
                  >
                    {{ exame.codigoExame }}
                  </span>
                </td>

                <td class="py-3 px-3 align-top max-w-xs">
                  <p :class="['font-semibold leading-snug', exame.ativo ? 'text-slate-800' : 'text-slate-500 line-through']">
                    {{ exame.nomeExame }}
                  </p>
                  <p v-if="exame.unidadeExecutora" class="text-xs text-slate-500 mt-0.5">
                    {{ exame.unidadeExecutora }}
                  </p>
                </td>

                <td class="py-3 px-3 align-top">
                  <div class="flex flex-wrap gap-1.5">
                    <span
                      v-if="exame.antecedenciaMinimaDias > 0"
                      class="rounded border border-sky-200 bg-sky-50 px-2 py-0.5 text-[11px] font-semibold text-sky-800 tabular-nums"
                    >
                      Antecedência ≥ {{ exame.antecedenciaMinimaDias }}d
                    </span>
                    <span
                      v-if="exame.janelaRetornoMaxHoras !== null"
                      class="rounded border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-800 tabular-nums"
                    >
                      Retorno ≤ {{ exame.janelaRetornoMaxHoras }}h
                    </span>
                    <span
                      v-if="exame.exigeJejum"
                      class="rounded border border-sky-200 bg-sky-50 px-2 py-0.5 text-[11px] font-semibold text-sky-800"
                    >
                      Exige Jejum
                    </span>
                    <span
                      v-if="exame.priorizarManhaDiabetico"
                      class="rounded border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-800"
                    >
                      Manhã Diabético
                    </span>
                    <span
                      v-if="exame.idadeMinimaAlerta !== null"
                      class="rounded border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-800 tabular-nums"
                    >
                      Idade ≥ {{ exame.idadeMinimaAlerta }}a
                    </span>
                    <span
                      v-if="
                        exame.antecedenciaMinimaDias === 0 &&
                        exame.janelaRetornoMaxHoras === null &&
                        !exame.exigeJejum &&
                        !exame.priorizarManhaDiabetico &&
                        exame.idadeMinimaAlerta === null
                      "
                      class="rounded border border-stone-200 bg-stone-100 px-2 py-0.5 text-[11px] font-medium text-stone-600"
                    >
                      Sem restrição especial
                    </span>
                  </div>
                </td>

                <td class="py-3 px-3 align-top max-w-sm">
                  <p
                    class="text-xs text-slate-600 line-clamp-2 leading-relaxed"
                    :title="exame.orientacoesPreparo || 'Sem orientações registradas'"
                  >
                    {{ exame.orientacoesPreparo || '—' }}
                  </p>
                </td>

                <td class="py-3 px-3 align-top text-center">
                  <button
                    type="button"
                    role="switch"
                    :aria-checked="exame.ativo"
                    :aria-label="`Alternar status do exame ${exame.codigoExame}`"
                    :disabled="regrasStore.carregando"
                    :class="[
                      'relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors duration-150 cursor-pointer focus:outline-none focus:ring-2 focus:ring-teal-600/30',
                      exame.ativo ? 'bg-emerald-600' : 'bg-stone-300',
                    ]"
                    @click="alternarExame(exame)"
                  >
                    <span
                      :class="[
                        'inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform duration-150',
                        exame.ativo ? 'translate-x-[18px]' : 'translate-x-1',
                      ]"
                    ></span>
                  </button>
                </td>

                <td class="py-3 px-3 align-top text-right whitespace-nowrap space-x-1.5">
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 rounded-md border border-stone-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-stone-100 transition-colors cursor-pointer"
                    @click="abrirModalExame(exame)"
                  >
                    <PencilSquareIcon class="h-3.5 w-3.5" />
                    Editar
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 rounded-md border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700 hover:bg-red-100 transition-colors cursor-pointer"
                    @click="solicitarRemocao('exame', exame.id, `${exame.codigoExame} — ${exame.nomeExame}`)"
                  >
                    <TrashIcon class="h-3.5 w-3.5" />
                    Remover
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Card>

    <!-- ABA 3: MATRIZ DE INCOMPATIBILIDADES -->
    <Card v-else>
      <div class="space-y-4">
        <div class="border-b border-stone-200 pb-3">
          <h2 class="text-base font-bold text-slate-800">
            3. Matriz de Incompatibilidades entre Exames
          </h2>
          <p class="text-xs text-slate-500 mt-0.5">
            Pares bidirecionais que disparam alertas automáticos quando um mesmo prontuário possui ambos os exames na fila ou no espelho AGHU.
          </p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-slate-700">
            <thead class="border-b border-stone-200 bg-stone-50 text-xs font-semibold uppercase text-slate-500">
              <tr>
                <th class="py-3 px-3">Par Incompatível</th>
                <th class="py-3 px-3">Tipo de Conflito</th>
                <th class="py-3 px-3 text-center">Intervalo Mín.</th>
                <th class="py-3 px-3">Motivo Clínico</th>
                <th class="py-3 px-3 text-center">Ativo</th>
                <th class="py-3 px-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-100">
              <tr
                v-for="inc in regrasStore.incompatibilidadesAtivas"
                :key="inc.id"
                :class="[
                  'transition-colors duration-150',
                  inc.ativo ? 'hover:bg-stone-50/80' : 'bg-stone-50/50 text-slate-400',
                ]"
              >
                <td class="py-3 px-3 align-top whitespace-nowrap">
                  <div class="flex items-center gap-1.5">
                    <span class="font-mono text-xs font-bold rounded border border-stone-300 bg-white px-2 py-0.5 text-slate-800">
                      {{ inc.codigoExameOrigem }}
                    </span>
                    <span class="text-xs font-bold text-red-600">×</span>
                    <span class="font-mono text-xs font-bold rounded border border-stone-300 bg-white px-2 py-0.5 text-slate-800">
                      {{ inc.codigoExameConflitante }}
                    </span>
                  </div>
                  <p class="text-[11px] text-slate-500 mt-1 max-w-[230px] truncate">
                    {{ obterNomeCurtoExame(inc.codigoExameOrigem) }} × {{ obterNomeCurtoExame(inc.codigoExameConflitante) }}
                  </p>
                </td>

                <td class="py-3 px-3 align-top whitespace-nowrap">
                  <span
                    :class="classeTipoConflito(inc.tipoConflito)"
                    class="inline-flex rounded-md px-2 py-0.5 text-xs font-bold"
                  >
                    {{ rotuloTipoConflito(inc.tipoConflito) }}
                  </span>
                </td>

                <td class="py-3 px-3 align-top text-center whitespace-nowrap">
                  <span class="font-semibold text-slate-800 tabular-nums">
                    {{ inc.intervaloMinimoDias }} {{ inc.intervaloMinimoDias === 1 ? 'dia' : 'dias' }}
                  </span>
                </td>

                <td class="py-3 px-3 align-top text-xs text-slate-600 leading-relaxed max-w-md">
                  {{ inc.motivo }}
                </td>

                <td class="py-3 px-3 align-top text-center">
                  <button
                    type="button"
                    role="switch"
                    :aria-checked="inc.ativo"
                    :aria-label="`Alternar incompatibilidade ${inc.codigoExameOrigem} x ${inc.codigoExameConflitante}`"
                    :disabled="regrasStore.carregando"
                    :class="[
                      'relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors duration-150 cursor-pointer focus:outline-none focus:ring-2 focus:ring-teal-600/30',
                      inc.ativo ? 'bg-emerald-600' : 'bg-stone-300',
                    ]"
                    @click="alternarIncompatibilidade(inc)"
                  >
                    <span
                      :class="[
                        'inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform duration-150',
                        inc.ativo ? 'translate-x-[18px]' : 'translate-x-1',
                      ]"
                    ></span>
                  </button>
                </td>

                <td class="py-3 px-3 align-top text-right whitespace-nowrap space-x-1.5">
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 rounded-md border border-stone-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-stone-100 transition-colors cursor-pointer"
                    @click="abrirModalIncompatibilidade(inc)"
                  >
                    <PencilSquareIcon class="h-3.5 w-3.5" />
                    Editar
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 rounded-md border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700 hover:bg-red-100 transition-colors cursor-pointer"
                    @click="
                      solicitarRemocao(
                        'incompatibilidade',
                        inc.id,
                        `${inc.codigoExameOrigem} × ${inc.codigoExameConflitante}`,
                      )
                    "
                  >
                    <TrashIcon class="h-3.5 w-3.5" />
                    Remover
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Card>

    <!-- MODAL 1: CRIAR / EDITAR CRITÉRIO DE PRIORIDADE -->
    <Modal :show="modalPrioridadeAberto" @close="fecharModalPrioridade">
      <template #header>
        {{ formPrioridade.id ? 'Editar Critério de Prioridade' : 'Novo Critério de Prioridade' }}
      </template>

      <form
        :class="['t-modal space-y-4', modalPrioridadeAberto ? 'is-open' : 'is-closing', erroModalShake ? 't-shake' : '']"
        @submit.prevent="salvarFormularioPrioridade"
      >
        <div
          v-if="erroModalMsg"
          class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-800"
        >
          {{ erroModalMsg }}
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="form-label" for="prio-codigo">Código Único *</label>
            <input
              id="prio-codigo"
              v-model="formPrioridade.codigo"
              type="text"
              required
              placeholder="Ex: CLINICA_CARDIO"
              class="form-control font-mono uppercase text-xs"
            />
          </div>

          <div>
            <label class="form-label" for="prio-peso">Peso (0 a 1000) *</label>
            <input
              id="prio-peso"
              v-model.number="formPrioridade.peso"
              type="number"
              min="0"
              max="1000"
              required
              class="form-control tabular-nums"
            />
          </div>
        </div>

        <div>
          <label class="form-label" for="prio-nome">Nome do Critério *</label>
          <input
            id="prio-nome"
            v-model="formPrioridade.nome"
            type="text"
            required
            placeholder="Ex: Cardiologia Intervencionista"
            class="form-control"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="form-label" for="prio-tipo">Tipo de Critério *</label>
            <select id="prio-tipo" v-model="formPrioridade.tipoCriterio" class="form-control bg-white">
              <option value="CLINICA">Clínica Solicitante</option>
              <option value="GRUPO_CLINICO">Grupo Clínico</option>
              <option value="VULNERAVEL">Grupo Vulnerável</option>
              <option value="RETORNO_PROXIMO">Retorno Médico Próximo</option>
              <option value="AFINIDADE_EXAME">Afinidade Clínica × Exame</option>
            </select>
          </div>

          <div>
            <label class="form-label" for="prio-match">Termos de Match *</label>
            <input
              id="prio-match"
              v-model="formPrioridade.valorMatch"
              type="text"
              required
              :placeholder="placeholderValorMatch"
              class="form-control font-mono uppercase text-xs"
            />
          </div>
        </div>

        <div>
          <label class="form-label" for="prio-desc">Descrição Clínica</label>
          <textarea
            id="prio-desc"
            v-model="formPrioridade.descricao"
            rows="2"
            placeholder="Justificativa assistencial para aplicação deste peso na fila..."
            class="form-control"
          ></textarea>
        </div>

        <label class="flex items-center gap-2 text-sm font-medium text-slate-700 cursor-pointer">
          <input v-model="formPrioridade.ativo" type="checkbox" class="h-4 w-4 rounded border-stone-300 text-teal-700" />
          Regra ativa no motor de priorização
        </label>

        <div class="flex justify-end gap-2.5 border-t border-stone-200 pt-4">
          <Button variant="default" type="button" @click="fecharModalPrioridade">Cancelar</Button>
          <Button variant="primary" type="submit" :loading="regrasStore.carregando">
            {{ formPrioridade.id ? 'Salvar Alterações' : 'Criar Critério' }}
          </Button>
        </div>
      </form>
    </Modal>

    <!-- MODAL 2: CRIAR / EDITAR REGRA POR EXAME -->
    <Modal :show="modalExameAberto" @close="fecharModalExame">
      <template #header>
        {{ formExame.id ? 'Editar Regra de Exame' : 'Nova Regra de Exame' }}
      </template>

      <form
        :class="['t-modal space-y-4', modalExameAberto ? 'is-open' : 'is-closing', erroModalShake ? 't-shake' : '']"
        @submit.prevent="salvarFormularioExame"
      >
        <div
          v-if="erroModalMsg"
          class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-800"
        >
          {{ erroModalMsg }}
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label class="form-label" for="ex-codigo">Sigla AGHU *</label>
            <input
              id="ex-codigo"
              v-model="formExame.codigoExame"
              type="text"
              required
              placeholder="Ex: ECO"
              class="form-control font-mono uppercase text-xs"
            />
          </div>

          <div class="sm:col-span-2">
            <label class="form-label" for="ex-nome">Nome Oficial do Exame *</label>
            <input
              id="ex-nome"
              v-model="formExame.nomeExame"
              type="text"
              required
              placeholder="Ex: ECOCARDIOGRAMA TRANSTORACICO"
              class="form-control"
            />
          </div>
        </div>

        <div>
          <label class="form-label" for="ex-unidade">Unidade Executora</label>
          <input
            id="ex-unidade"
            v-model="formExame.unidadeExecutora"
            type="text"
            placeholder="Ex: UDI: CARDIOLOGIA / METODOS GRAFICOS"
            class="form-control"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label class="form-label" for="ex-ant">Antecedência (dias)</label>
            <input
              id="ex-ant"
              v-model.number="formExame.antecedenciaMinimaDias"
              type="number"
              min="0"
              class="form-control tabular-nums"
            />
          </div>

          <div>
            <label class="form-label" for="ex-janela">Janela Retorno (h)</label>
            <input
              id="ex-janela"
              v-model="formExame.janelaRetornoMaxHoras"
              type="number"
              min="1"
              placeholder="Opcional"
              class="form-control tabular-nums"
            />
          </div>

          <div>
            <label class="form-label" for="ex-idade">Idade Mín. Alerta</label>
            <input
              id="ex-idade"
              v-model="formExame.idadeMinimaAlerta"
              type="number"
              min="1"
              placeholder="Opcional"
              class="form-control tabular-nums"
            />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 rounded-lg border border-stone-200 bg-stone-50 p-3">
          <label class="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
            <input v-model="formExame.exigeJejum" type="checkbox" class="h-4 w-4 rounded border-stone-300 text-teal-700" />
            Exige jejum clínico
          </label>

          <label class="flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
            <input
              v-model="formExame.priorizarManhaDiabetico"
              type="checkbox"
              class="h-4 w-4 rounded border-stone-300 text-teal-700"
            />
            Priorizar manhã p/ diabéticos
          </label>
        </div>

        <div>
          <label class="form-label" for="ex-preparo">Orientações de Preparo</label>
          <textarea
            id="ex-preparo"
            v-model="formExame.orientacoesPreparo"
            rows="3"
            placeholder="Instruções enviadas ao paciente no contato de 24h..."
            class="form-control"
          ></textarea>
        </div>

        <label class="flex items-center gap-2 text-sm font-medium text-slate-700 cursor-pointer">
          <input v-model="formExame.ativo" type="checkbox" class="h-4 w-4 rounded border-stone-300 text-teal-700" />
          Regra ativa na detecção de alertas
        </label>

        <div class="flex justify-end gap-2.5 border-t border-stone-200 pt-4">
          <Button variant="default" type="button" @click="fecharModalExame">Cancelar</Button>
          <Button variant="primary" type="submit" :loading="regrasStore.carregando">
            {{ formExame.id ? 'Salvar Alterações' : 'Criar Regra' }}
          </Button>
        </div>
      </form>
    </Modal>

    <!-- MODAL 3: CRIAR / EDITAR PAR INCOMPATÍVEL -->
    <Modal :show="modalIncompAberto" @close="fecharModalIncompatibilidade">
      <template #header>
        {{ formIncomp.id ? 'Editar Par Incompatível' : 'Novo Par Incompatível' }}
      </template>

      <form
        :class="['t-modal space-y-4', modalIncompAberto ? 'is-open' : 'is-closing', erroModalShake ? 't-shake' : '']"
        @submit.prevent="salvarFormularioIncompatibilidade"
      >
        <div
          v-if="erroModalMsg"
          class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-800"
        >
          {{ erroModalMsg }}
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="form-label" for="inc-origem">Exame Origem *</label>
            <select
              id="inc-origem"
              v-model="formIncomp.codigoExameOrigem"
              required
              class="form-control bg-white font-mono text-xs"
            >
              <option value="" disabled>Selecione o exame...</option>
              <option v-for="ex in opcoesExamesIncomp" :key="`orig-${ex.codigo}`" :value="ex.codigo">
                {{ ex.codigo }} — {{ ex.nome }}
              </option>
            </select>
          </div>

          <div>
            <label class="form-label" for="inc-conflito">Exame Conflitante *</label>
            <select
              id="inc-conflito"
              v-model="formIncomp.codigoExameConflitante"
              required
              class="form-control bg-white font-mono text-xs"
            >
              <option value="" disabled>Selecione o exame...</option>
              <option
                v-for="ex in opcoesExamesIncomp"
                :key="`conf-${ex.codigo}`"
                :value="ex.codigo"
                :disabled="ex.codigo === formIncomp.codigoExameOrigem"
              >
                {{ ex.codigo }} — {{ ex.nome }}
              </option>
            </select>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="form-label" for="inc-tipo">Tipo de Conflito *</label>
            <select id="inc-tipo" v-model="formIncomp.tipoConflito" class="form-control bg-white">
              <option value="MESMO_DIA">Mesmo Dia (não agendar juntos)</option>
              <option value="PREPARO">Conflito de Preparo</option>
              <option value="INTERVALO_MINIMO">Intervalo Mínimo Obrigatório</option>
            </select>
          </div>

          <div>
            <label class="form-label" for="inc-intervalo">Intervalo Mínimo (dias) *</label>
            <input
              id="inc-intervalo"
              v-model.number="formIncomp.intervaloMinimoDias"
              type="number"
              min="0"
              max="90"
              required
              class="form-control tabular-nums"
            />
          </div>
        </div>

        <div>
          <label class="form-label" for="inc-motivo">Motivo Clínico *</label>
          <textarea
            id="inc-motivo"
            v-model="formIncomp.motivo"
            rows="3"
            required
            placeholder="Descreva a interferência clínica ou de preparo entre os dois exames..."
            class="form-control"
          ></textarea>
        </div>

        <label class="flex items-center gap-2 text-sm font-medium text-slate-700 cursor-pointer">
          <input v-model="formIncomp.ativo" type="checkbox" class="h-4 w-4 rounded border-stone-300 text-teal-700" />
          Par ativo na matriz de alertas
        </label>

        <div class="flex justify-end gap-2.5 border-t border-stone-200 pt-4">
          <Button variant="default" type="button" @click="fecharModalIncompatibilidade">Cancelar</Button>
          <Button variant="primary" type="submit" :loading="regrasStore.carregando">
            {{ formIncomp.id ? 'Salvar Alterações' : 'Cadastrar Par' }}
          </Button>
        </div>
      </form>
    </Modal>

    <!-- MODAL 4: CONFIRMAÇÃO DE SOFT DELETE -->
    <Modal :show="modalConfirmarRemocaoAberto" @close="fecharModalRemocao">
      <template #header>Confirmar Exclusão Lógica (Soft Delete)</template>

      <div :class="['t-modal space-y-4', modalConfirmarRemocaoAberto ? 'is-open' : 'is-closing']">
        <p class="text-sm text-slate-700 leading-relaxed">
          Deseja remover a regra
          <strong class="text-slate-900">{{ alvoRemocao?.rotulo }}</strong>?
        </p>
        <p class="rounded-lg border border-stone-200 bg-stone-50 p-3 text-xs text-slate-600">
          O registro será desativado logicamente (<span class="font-mono">deletedAt</span>) para preservação de auditoria e deixará imediatamente de influenciar o cálculo da Fila Priorizada.
        </p>

        <div class="flex justify-end gap-2.5 border-t border-stone-200 pt-4">
          <Button variant="default" type="button" @click="fecharModalRemocao">Cancelar</Button>
          <Button variant="danger" type="button" :loading="regrasStore.carregando" @click="confirmarRemocao">
            Confirmar Remoção
          </Button>
        </div>
      </div>
    </Modal>

  </div>
</template>

<script setup lang="ts">
import {
  AdjustmentsHorizontalIcon,
  ArrowPathIcon,
  ArrowRightIcon,
  PencilSquareIcon,
  PlusIcon,
  ShieldCheckIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline';
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import type { ComponentPublicInstance } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'vue-toastification';
import Button from '../components/Button.vue';
import Card from '../components/Card.vue';
import Modal from '../components/Modal.vue';
import { useRegrasStore } from '../stores/regras';
import type {
  IIncompatibilidadeExame,
  IRegraExame,
  IRegraPrioridade,
  TipoConflitoExame,
  TipoCriterioPrioridade,
} from '../types/exames';

type AbaRegraId = 'prioridades' | 'exames' | 'incompatibilidades';

interface IFormPrioridade {
  id?: number;
  codigo: string;
  nome: string;
  tipoCriterio: TipoCriterioPrioridade;
  valorMatch: string;
  peso: number;
  descricao: string;
  ativo: boolean;
}

interface IFormExame {
  id?: number;
  codigoExame: string;
  nomeExame: string;
  unidadeExecutora: string;
  antecedenciaMinimaDias: number;
  janelaRetornoMaxHoras: string;
  idadeMinimaAlerta: string;
  exigeJejum: boolean;
  priorizarManhaDiabetico: boolean;
  orientacoesPreparo: string;
  ativo: boolean;
}

interface IFormIncompatibilidade {
  id?: number;
  codigoExameOrigem: string;
  codigoExameConflitante: string;
  tipoConflito: TipoConflitoExame;
  intervaloMinimoDias: number;
  motivo: string;
  ativo: boolean;
}

interface IAlvoRemocao {
  tipo: 'prioridade' | 'exame' | 'incompatibilidade';
  id: number;
  rotulo: string;
}

const ABAS_REGRAS: Array<{ id: AbaRegraId; label: string }> = [
  { id: 'prioridades', label: '1. Pesos de Prioridade' },
  { id: 'exames', label: '2. Regras por Exame' },
  { id: 'incompatibilidades', label: '3. Matriz de Incompatibilidades' },
];

const regrasStore = useRegrasStore();
const router = useRouter();
const toast = useToast();

const abaAtiva = ref<AbaRegraId>('prioridades');
const tabsContainerRef = ref<HTMLElement | null>(null);
const tabsPillRef = ref<HTMLElement | null>(null);
const abasRefs = new Map<AbaRegraId, HTMLElement>();

const modalPrioridadeAberto = ref(false);
const modalExameAberto = ref(false);
const modalIncompAberto = ref(false);
const modalConfirmarRemocaoAberto = ref(false);

const erroModalMsg = ref('');
const erroModalShake = ref(false);
const alvoRemocao = ref<IAlvoRemocao | null>(null);

const formPrioridade = ref<IFormPrioridade>(criarFormPrioridadePadrao());
const formExame = ref<IFormExame>(criarFormExamePadrao());
const formIncomp = ref<IFormIncompatibilidade>(criarFormIncompPadrao());

const contagemAba = computed<Record<AbaRegraId, number>>(() => ({
  prioridades: regrasStore.prioridadesAtivas.length,
  exames: regrasStore.examesAtivos.length,
  incompatibilidades: regrasStore.incompatibilidadesAtivas.length,
}));

const maiorPesoPrioridade = computed(() => {
  const ativos = regrasStore.prioridadesAtivas.filter((r) => r.ativo);
  if (ativos.length === 0) {
    return 100;
  }
  return Math.max(100, ...ativos.map((r) => r.peso));
});

const placeholderValorMatch = computed(() => {
  switch (formPrioridade.value.tipoCriterio) {
    case 'RETORNO_PROXIMO':
      return '<=15';
    case 'AFINIDADE_EXAME':
      return 'AFINIDADE_ESPECIALIDADE';
    case 'VULNERAVEL':
      return 'GESTANTE,OBSTETRICIA';
    default:
      return 'ONCOLOGIA';
  }
});

const opcoesExamesIncomp = computed<Array<{ codigo: string; nome: string }>>(() => {
  const mapa = new Map<string, string>();
  for (const regra of regrasStore.examesAtivos) {
    mapa.set(regra.codigoExame, regra.nomeExame);
  }
  if (formIncomp.value.codigoExameOrigem && !mapa.has(formIncomp.value.codigoExameOrigem)) {
    mapa.set(formIncomp.value.codigoExameOrigem, formIncomp.value.codigoExameOrigem);
  }
  if (
    formIncomp.value.codigoExameConflitante &&
    !mapa.has(formIncomp.value.codigoExameConflitante)
  ) {
    mapa.set(formIncomp.value.codigoExameConflitante, formIncomp.value.codigoExameConflitante);
  }
  return Array.from(mapa.entries())
    .map(([codigo, nome]) => ({ codigo, nome }))
    .sort((a, b) => a.codigo.localeCompare(b.codigo));
});

function criarFormPrioridadePadrao(): IFormPrioridade {
  return {
    codigo: '',
    nome: '',
    tipoCriterio: 'CLINICA',
    valorMatch: '',
    peso: 50,
    descricao: '',
    ativo: true,
  };
}

function criarFormExamePadrao(): IFormExame {
  return {
    codigoExame: '',
    nomeExame: '',
    unidadeExecutora: '',
    antecedenciaMinimaDias: 0,
    janelaRetornoMaxHoras: '',
    idadeMinimaAlerta: '',
    exigeJejum: false,
    priorizarManhaDiabetico: false,
    orientacoesPreparo: '',
    ativo: true,
  };
}

function criarFormIncompPadrao(): IFormIncompatibilidade {
  return {
    codigoExameOrigem: '',
    codigoExameConflitante: '',
    tipoConflito: 'MESMO_DIA',
    intervaloMinimoDias: 1,
    motivo: '',
    ativo: true,
  };
}

function registrarRefAba(
  id: AbaRegraId,
  el: Element | ComponentPublicInstance | null,
): void {
  if (el instanceof HTMLElement) {
    abasRefs.set(id, el);
  } else {
    abasRefs.delete(id);
  }
}

function posicionarPilulaAba(semTransicao = false): void {
  const pill = tabsPillRef.value;
  const activeBtn = abasRefs.get(abaAtiva.value);
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
  posicionarPilulaAba(true);
}

function limparErroModal(): void {
  erroModalMsg.value = '';
  erroModalShake.value = false;
}

function dispararErroModal(mensagem: string): void {
  erroModalMsg.value = mensagem;
  erroModalShake.value = false;
  requestAnimationFrame(() => {
    erroModalShake.value = true;
    setTimeout(() => {
      erroModalShake.value = false;
    }, 320);
  });
}

function percentualPeso(peso: number): number {
  if (maiorPesoPrioridade.value <= 0) {
    return 0;
  }
  return Math.min(100, Math.round((peso / maiorPesoPrioridade.value) * 100));
}

function obterNomeCurtoExame(codigo: string): string {
  const encontrado = regrasStore.examesAtivos.find((e) => e.codigoExame === codigo);
  return encontrado?.nomeExame ?? codigo;
}

// ── CRUD Prioridades ────────────────────────────────────────────────────────
function abrirModalPrioridade(regra?: IRegraPrioridade): void {
  limparErroModal();
  if (regra) {
    formPrioridade.value = {
      id: regra.id,
      codigo: regra.codigo,
      nome: regra.nome,
      tipoCriterio: regra.tipoCriterio,
      valorMatch: regra.valorMatch,
      peso: regra.peso,
      descricao: regra.descricao ?? '',
      ativo: regra.ativo,
    };
  } else {
    formPrioridade.value = criarFormPrioridadePadrao();
  }
  modalPrioridadeAberto.value = true;
}

function fecharModalPrioridade(): void {
  modalPrioridadeAberto.value = false;
  limparErroModal();
}

async function salvarFormularioPrioridade(): Promise<void> {
  const f = formPrioridade.value;
  if (!f.codigo.trim() || !f.nome.trim() || !f.valorMatch.trim()) {
    dispararErroModal('Preencha código, nome e termos de match obrigatórios.');
    return;
  }
  if (Number.isNaN(f.peso) || f.peso < 0 || f.peso > 1000) {
    dispararErroModal('O peso clínico deve estar entre 0 e 1000 pontos.');
    return;
  }

  try {
    const salva = await regrasStore.salvarPrioridade({
      id: f.id,
      codigo: f.codigo,
      nome: f.nome,
      tipoCriterio: f.tipoCriterio,
      valorMatch: f.valorMatch,
      peso: f.peso,
      descricao: f.descricao || null,
      ativo: f.ativo,
    });
    fecharModalPrioridade();
    toast.success(
      f.id
        ? `Critério ${salva.codigo} atualizado (+${salva.peso} pts). Fila recalculada.`
        : `Critério ${salva.codigo} criado (+${salva.peso} pts). Fila recalculada.`,
    );
  } catch (err) {
    dispararErroModal(err instanceof Error ? err.message : 'Erro ao salvar critério de prioridade.');
  }
}

async function alternarPrioridade(regra: IRegraPrioridade): Promise<void> {
  const novoEstado = !regra.ativo;
  try {
    await regrasStore.alternarAtivoPrioridade(regra.id);
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'Erro ao alterar a situação da critério.');
    return;
  }
  toast.info(
    `Critério ${regra.codigo} ${novoEstado ? 'ativado' : 'pausado'}. Scores da fila atualizados.`,
  );
}

// ── CRUD Regras por Exame ───────────────────────────────────────────────────
function abrirModalExame(exame?: IRegraExame): void {
  limparErroModal();
  if (exame) {
    formExame.value = {
      id: exame.id,
      codigoExame: exame.codigoExame,
      nomeExame: exame.nomeExame,
      unidadeExecutora: exame.unidadeExecutora ?? '',
      antecedenciaMinimaDias: exame.antecedenciaMinimaDias,
      janelaRetornoMaxHoras:
        exame.janelaRetornoMaxHoras !== null ? String(exame.janelaRetornoMaxHoras) : '',
      idadeMinimaAlerta: exame.idadeMinimaAlerta !== null ? String(exame.idadeMinimaAlerta) : '',
      exigeJejum: exame.exigeJejum,
      priorizarManhaDiabetico: exame.priorizarManhaDiabetico,
      orientacoesPreparo: exame.orientacoesPreparo ?? '',
      ativo: exame.ativo,
    };
  } else {
    formExame.value = criarFormExamePadrao();
  }
  modalExameAberto.value = true;
}

function fecharModalExame(): void {
  modalExameAberto.value = false;
  limparErroModal();
}

function converterInteiroOpcional(valor: string): number | null {
  const limpo = String(valor ?? '').trim();
  if (!limpo) {
    return null;
  }
  const num = Number(limpo);
  return Number.isFinite(num) && num > 0 ? Math.round(num) : null;
}

async function salvarFormularioExame(): Promise<void> {
  const f = formExame.value;
  if (!f.codigoExame.trim() || !f.nomeExame.trim()) {
    dispararErroModal('Informe a sigla AGHU e o nome oficial do exame.');
    return;
  }
  if (Number.isNaN(f.antecedenciaMinimaDias) || f.antecedenciaMinimaDias < 0) {
    dispararErroModal('A antecedência mínima deve ser zero ou maior.');
    return;
  }

  try {
    const salva = await regrasStore.salvarRegraExame({
      id: f.id,
      codigoExame: f.codigoExame,
      nomeExame: f.nomeExame,
      unidadeExecutora: f.unidadeExecutora || null,
      antecedenciaMinimaDias: f.antecedenciaMinimaDias,
      janelaRetornoMaxHoras: converterInteiroOpcional(f.janelaRetornoMaxHoras),
      idadeMinimaAlerta: converterInteiroOpcional(f.idadeMinimaAlerta),
      exigeJejum: f.exigeJejum,
      priorizarManhaDiabetico: f.priorizarManhaDiabetico,
      orientacoesPreparo: f.orientacoesPreparo || null,
      ativo: f.ativo,
    });
    fecharModalExame();
    toast.success(
      f.id
        ? `Regra do exame ${salva.codigoExame} atualizada. Alertas da fila recalculados.`
        : `Regra do exame ${salva.codigoExame} cadastrada com sucesso.`,
    );
  } catch (err) {
    dispararErroModal(err instanceof Error ? err.message : 'Erro ao salvar regra do exame.');
  }
}

async function alternarExame(exame: IRegraExame): Promise<void> {
  const novoEstado = !exame.ativo;
  try {
    await regrasStore.alternarAtivoRegraExame(exame.id);
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'Erro ao alterar a situação da regra.');
    return;
  }
  toast.info(
    `Regra de ${exame.codigoExame} ${novoEstado ? 'ativada' : 'desativada'}. Alertas atualizados.`,
  );
}

// ── CRUD Matriz de Incompatibilidades ───────────────────────────────────────
function abrirModalIncompatibilidade(inc?: IIncompatibilidadeExame): void {
  limparErroModal();
  if (inc) {
    formIncomp.value = {
      id: inc.id,
      codigoExameOrigem: inc.codigoExameOrigem,
      codigoExameConflitante: inc.codigoExameConflitante,
      tipoConflito: inc.tipoConflito,
      intervaloMinimoDias: inc.intervaloMinimoDias,
      motivo: inc.motivo,
      ativo: inc.ativo,
    };
  } else {
    formIncomp.value = criarFormIncompPadrao();
  }
  modalIncompAberto.value = true;
}

function fecharModalIncompatibilidade(): void {
  modalIncompAberto.value = false;
  limparErroModal();
}

async function salvarFormularioIncompatibilidade(): Promise<void> {
  const f = formIncomp.value;
  const origem = f.codigoExameOrigem.trim().toUpperCase();
  const conflitante = f.codigoExameConflitante.trim().toUpperCase();

  if (!origem || !conflitante) {
    dispararErroModal('Selecione ambos os exames para configurar a incompatibilidade.');
    return;
  }
  if (origem === conflitante) {
    dispararErroModal('Auto-conflito não permitido: selecione dois exames distintos.');
    return;
  }

  const parDuplicado = regrasStore.incompatibilidadesAtivas.some((item) => {
    if (item.id === f.id) {
      return false;
    }
    const o = item.codigoExameOrigem.trim().toUpperCase();
    const c = item.codigoExameConflitante.trim().toUpperCase();
    return (o === origem && c === conflitante) || (o === conflitante && c === origem);
  });
  if (parDuplicado) {
    dispararErroModal(`O par ${origem} × ${conflitante} já está cadastrado na matriz.`);
    return;
  }

  if (!f.motivo.trim()) {
    dispararErroModal('Informe o motivo clínico da incompatibilidade.');
    return;
  }

  try {
    const salva = await regrasStore.salvarIncompatibilidade({
      id: f.id,
      codigoExameOrigem: origem,
      codigoExameConflitante: conflitante,
      tipoConflito: f.tipoConflito,
      intervaloMinimoDias: f.intervaloMinimoDias,
      motivo: f.motivo,
      ativo: f.ativo,
    });
    fecharModalIncompatibilidade();
    toast.success(
      f.id
        ? `Par ${salva.codigoExameOrigem} × ${salva.codigoExameConflitante} atualizado.`
        : `Par ${salva.codigoExameOrigem} × ${salva.codigoExameConflitante} adicionado à matriz.`,
    );
  } catch (err) {
    dispararErroModal(err instanceof Error ? err.message : 'Erro ao salvar incompatibilidade.');
  }
}

async function alternarIncompatibilidade(inc: IIncompatibilidadeExame): Promise<void> {
  const novoEstado = !inc.ativo;
  try {
    await regrasStore.alternarAtivoIncompatibilidade(inc.id);
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'Erro ao alterar a situação da incompatibilidade.');
    return;
  }
  toast.info(
    `Incompatibilidade ${inc.codigoExameOrigem} × ${inc.codigoExameConflitante} ${novoEstado ? 'ativada' : 'desativada'}.`,
  );
}

// ── Soft Delete & Recarga do Servidor ──────────────────────────────────────────────
function solicitarRemocao(
  tipo: 'prioridade' | 'exame' | 'incompatibilidade',
  id: number,
  rotulo: string,
): void {
  alvoRemocao.value = { tipo, id, rotulo };
  modalConfirmarRemocaoAberto.value = true;
}

function fecharModalRemocao(): void {
  modalConfirmarRemocaoAberto.value = false;
  alvoRemocao.value = null;
}

async function confirmarRemocao(): Promise<void> {
  const alvo = alvoRemocao.value;
  if (!alvo) {
    return;
  }

  try {
    if (alvo.tipo === 'prioridade') {
      await regrasStore.removerPrioridade(alvo.id);
    } else if (alvo.tipo === 'exame') {
      await regrasStore.removerRegraExame(alvo.id);
    } else {
      await regrasStore.removerIncompatibilidade(alvo.id);
    }
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'Erro ao remover a regra.');
    return;
  }

  toast.warning(`Regra "${alvo.rotulo}" removida logicamente (Soft Delete). Fila recalculada.`);
  fecharModalRemocao();
}

async function recarregarDoServidor(): Promise<void> {
  try {
    await regrasStore.carregarRegras();
    toast.success('Regras recarregadas do servidor.');
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'Não foi possível carregar as regras do servidor.');
  }
}

// ── Formatadores & Badges Clínicos (Zero Roxo/Violeta) ──────────────────────
function rotuloTipoCriterio(tipo: TipoCriterioPrioridade): string {
  switch (tipo) {
    case 'CLINICA':
      return 'Clínica';
    case 'GRUPO_CLINICO':
      return 'Grupo Clínico';
    case 'VULNERAVEL':
      return 'Vulnerável';
    case 'AFINIDADE_EXAME':
      return 'Afinidade';
    case 'RETORNO_PROXIMO':
      return 'Retorno Próximo';
  }
}

function classeTipoCriterio(tipo: TipoCriterioPrioridade): string {
  switch (tipo) {
    case 'CLINICA':
      return 'bg-teal-50 text-teal-800 border border-teal-200';
    case 'GRUPO_CLINICO':
      return 'bg-emerald-50 text-emerald-800 border border-emerald-200';
    case 'VULNERAVEL':
      return 'bg-amber-50 text-amber-800 border border-amber-200';
    case 'AFINIDADE_EXAME':
      return 'bg-sky-50 text-sky-800 border border-sky-200';
    case 'RETORNO_PROXIMO':
      return 'bg-stone-100 text-stone-700 border border-stone-200';
  }
}

function rotuloTipoConflito(tipo: TipoConflitoExame): string {
  switch (tipo) {
    case 'MESMO_DIA':
      return 'Mesmo Dia';
    case 'PREPARO':
      return 'Preparo';
    case 'INTERVALO_MINIMO':
      return 'Intervalo Mínimo';
  }
}

function classeTipoConflito(tipo: TipoConflitoExame): string {
  switch (tipo) {
    case 'MESMO_DIA':
      return 'bg-red-50 text-red-800 border border-red-200';
    case 'PREPARO':
      return 'bg-amber-50 text-amber-800 border border-amber-200';
    case 'INTERVALO_MINIMO':
      return 'bg-sky-50 text-sky-800 border border-sky-200';
  }
}

watch(abaAtiva, async () => {
  await nextTick();
  posicionarPilulaAba(false);
});

watch(
  contagemAba,
  async () => {
    await nextTick();
    posicionarPilulaAba(true);
  },
  { deep: true },
);

onMounted(async () => {
  try {
    await regrasStore.carregarRegras();
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'Não foi possível carregar as regras do servidor.');
  }
  await nextTick();
  posicionarPilulaAba(true);
  window.addEventListener('resize', aoRedimensionar);
});

onUnmounted(() => {
  window.removeEventListener('resize', aoRedimensionar);
});
</script>
