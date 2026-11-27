<template>
  <div class="space-y-6">
    <!-- Barra de Recorte Gerencial -->
    <Card>
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 class="text-xl font-bold text-slate-800">
            Indicadores da Fila e Triagem de Exames
          </h2>
          <p class="mt-1 text-sm text-slate-600">
            Acompanhamento gerencial da fila ativa, confirmações 24h, higienização Forms × AGHU e demanda TFD.
          </p>
        </div>

        <div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center lg:justify-end">
          <!-- Seletor de período com sliding pill -->
          <div
            ref="tabsContainerRef"
            class="t-tabs"
            role="tablist"
            aria-label="Recorte de período dos indicadores"
          >
            <div class="t-tabs-pill" :style="pillStyle" aria-hidden="true"></div>
            <button
              v-for="(opcao, idx) in opcoesPeriodo"
              :key="String(opcao.valor)"
              :ref="(el) => registrarRefAba(el, idx)"
              type="button"
              role="tab"
              :aria-selected="dashboardStore.periodoDias === opcao.valor"
              class="t-tab"
              @click="selecionarPeriodo(opcao.valor)"
            >
              {{ opcao.label }}
            </button>
          </div>

          <!-- Filtro por Unidade Solicitante -->
          <div class="min-w-[210px]">
            <label for="filtro-unidade-kpi" class="sr-only">Unidade Solicitante</label>
            <select
              id="filtro-unidade-kpi"
              :value="dashboardStore.unidadeFiltro"
              class="form-control text-sm text-slate-700"
              @change="onUnidadeChange"
            >
              <option value="">Todas as unidades solicitantes</option>
              <option
                v-for="unidade in examesStore.unidadesDisponiveis"
                :key="unidade"
                :value="unidade"
              >
                {{ unidade }}
              </option>
            </select>
          </div>

          <!-- Atualizar Indicadores -->
          <Button
            variant="primary"
            :loading="dashboardStore.atualizando"
            @click="handleAtualizarIndicadores"
          >
            <template #icon>
              <ArrowPathIcon
                class="h-4 w-4"
                :class="{ 'animate-spin': dashboardStore.atualizando }"
              />
            </template>
            Atualizar Indicadores
          </Button>
        </div>
      </div>

      <div class="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-stone-200/80 pt-3 text-xs text-slate-500">
        <span>
          Recorte ativo:
          <strong class="font-semibold text-slate-700">{{ labelPeriodoAtivo }}</strong>
          ·
          <strong class="font-semibold text-slate-700">
            {{ dashboardStore.unidadeFiltro || 'Todas as unidades' }}
          </strong>
        </span>
        <span class="tabular-nums">
          Atualizado em {{ ultimaAtualizacaoFormatada }}
        </span>
      </div>
    </Card>

    <!-- Grid Principal de 6 KPIs -->
    <section aria-label="Indicadores principais">
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 t-stagger">
        <!-- KPI 1: Total na Fila Ativa -->
        <article
          class="t-kpi-card t-stagger-item rounded-lg border border-stone-200/80 bg-white p-5 shadow-paper flex flex-col justify-between gap-3"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Total na Fila Ativa
              </p>
              <p class="mt-2 text-3xl font-extrabold text-slate-800 tabular-nums">
                <span class="t-subtle-number" :class="{ 'is-animating': animandoNumeros }">
                  <span class="t-subtle-new">{{ kpis.totalNaFila }}</span>
                </span>
              </p>
            </div>
            <span class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-teal-200 bg-teal-50 text-teal-700 shrink-0">
              <QueueListIcon class="h-5 w-5" />
            </span>
          </div>
          <div class="flex items-center justify-between text-xs text-slate-600 border-t border-stone-100 pt-2.5">
            <span>Aguardando contato inicial</span>
            <span class="font-semibold text-teal-700 tabular-nums">
              {{ kpis.filaPorExame.length }} tipos de exame
            </span>
          </div>
        </article>

        <!-- KPI 2: Aguardando Confirmação 24h -->
        <article
          class="t-kpi-card t-stagger-item rounded-lg border border-stone-200/80 bg-white p-5 shadow-paper flex flex-col justify-between gap-3"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Aguardando Confirmação 24h
              </p>
              <p class="mt-2 text-3xl font-extrabold text-slate-800 tabular-nums">
                <span class="t-subtle-number" :class="{ 'is-animating': animandoNumeros }">
                  <span class="t-subtle-new">{{ kpis.aguardando24h }}</span>
                </span>
              </p>
            </div>
            <span class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-amber-200 bg-amber-50 text-amber-800 shrink-0">
              <ClockIcon class="h-5 w-5" />
            </span>
          </div>
          <div class="flex items-center justify-between gap-2 border-t border-stone-100 pt-2.5 text-xs">
            <span class="text-slate-600">Janela de retorno do paciente</span>
            <button
              v-if="kpis.prazo24hVencidos > 0"
              type="button"
              class="inline-flex items-center rounded-full border border-red-200 bg-red-50 px-2.5 py-0.5 font-semibold text-red-800 tabular-nums hover:bg-red-100 transition-colors cursor-pointer"
              @click="abrirFilaVencidos24h"
            >
              {{ kpis.prazo24hVencidos }} prazo(s) vencido(s)
            </button>
            <span
              v-else
              class="inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 font-semibold text-emerald-800"
            >
              Nenhum vencido
            </span>
          </div>
        </article>

        <!-- KPI 3: Confirmados / Agendados AGHU -->
        <article
          class="t-kpi-card t-stagger-item rounded-lg border border-stone-200/80 bg-white p-5 shadow-paper flex flex-col justify-between gap-3"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Confirmados / Agendados AGHU
              </p>
              <p class="mt-2 text-3xl font-extrabold text-slate-800 tabular-nums">
                <span class="t-subtle-number" :class="{ 'is-animating': animandoNumeros }">
                  <span class="t-subtle-new">{{ kpis.confirmadosAgendados }}</span>
                </span>
              </p>
            </div>
            <span class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700 shrink-0">
              <CheckCircleIcon class="h-5 w-5" />
            </span>
          </div>
          <div class="flex items-center justify-between gap-2 border-t border-stone-100 pt-2.5 text-xs">
            <span class="text-slate-600 tabular-nums">
              {{ kpis.semResposta24h }} sem resposta 24h
            </span>
            <span class="inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 font-semibold text-emerald-800 tabular-nums">
              Taxa 24h: {{ kpis.taxaConfirmacao24h }}%
            </span>
          </div>
        </article>

        <!-- KPI 4: Tempo Médio de Espera -->
        <article
          class="t-kpi-card t-stagger-item rounded-lg border border-stone-200/80 bg-white p-5 shadow-paper flex flex-col justify-between gap-3"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Tempo Médio de Espera
              </p>
              <p class="mt-2 text-3xl font-extrabold text-slate-800 tabular-nums">
                <span class="t-subtle-number" :class="{ 'is-animating': animandoNumeros }">
                  <span class="t-subtle-new">{{ tempoMedioFormatado }}</span>
                </span>
                <span class="ml-1.5 text-base font-semibold text-slate-500">dias</span>
              </p>
            </div>
            <span class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-sky-200 bg-sky-50 text-sky-700 shrink-0">
              <CalendarDaysIcon class="h-5 w-5" />
            </span>
          </div>
          <div class="flex items-center justify-between text-xs text-slate-600 border-t border-stone-100 pt-2.5">
            <span>Da solicitação AGHU até hoje</span>
            <span class="font-semibold text-slate-700 tabular-nums">
              {{ totalAtivosNaFila }} itens ativos
            </span>
          </div>
        </article>

        <!-- KPI 5: Duplicidades e Divergências Barradas -->
        <article
          class="t-kpi-card t-stagger-item rounded-lg border border-stone-200/80 bg-white p-5 shadow-paper flex flex-col justify-between gap-3"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Duplicidades e Divergências Barradas
              </p>
              <p class="mt-2 text-3xl font-extrabold text-slate-800 tabular-nums">
                <span class="t-subtle-number" :class="{ 'is-animating': animandoNumeros }">
                  <span class="t-subtle-new">{{ totalBarradasHigienizacao }}</span>
                </span>
              </p>
            </div>
            <span class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-amber-200 bg-amber-50 text-amber-800 shrink-0">
              <ShieldExclamationIcon class="h-5 w-5" />
            </span>
          </div>
          <div class="flex flex-wrap items-center justify-between gap-2 border-t border-stone-100 pt-2.5 text-xs text-slate-600 tabular-nums">
            <span>{{ kpis.duplicidadesBarradas }} duplicidades</span>
            <span>{{ kpis.divergenciasDetectadas }} divergências Forms × AGHU</span>
          </div>
        </article>

        <!-- KPI 6: Pacientes com TFD na Fila -->
        <article
          class="t-kpi-card t-stagger-item rounded-lg border border-stone-200/80 bg-white p-5 shadow-paper flex flex-col justify-between gap-3"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Pacientes com TFD na Fila
              </p>
              <p class="mt-2 text-3xl font-extrabold text-slate-800 tabular-nums">
                <span class="t-subtle-number" :class="{ 'is-animating': animandoNumeros }">
                  <span class="t-subtle-new">{{ kpis.totalTfdFila }}</span>
                </span>
              </p>
            </div>
            <span class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-sky-200 bg-sky-50 text-sky-700 shrink-0">
              <TruckIcon class="h-5 w-5" />
            </span>
          </div>
          <div class="flex items-center justify-between gap-2 border-t border-stone-100 pt-2.5 text-xs">
            <span class="text-slate-600 tabular-nums">{{ percentualTfd }}% da fila ativa</span>
            <button
              type="button"
              class="font-semibold text-teal-700 hover:text-teal-900 transition-colors cursor-pointer"
              @click="abrirFilaTfd"
            >
              Filtrar TFD na fila →
            </button>
          </div>
        </article>
      </div>
    </section>

    <!-- Painéis Analíticos Visuais (SVG / CSS puro) -->
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-12">
      <!-- Volume por Exame (clicável para /fila) -->
      <Card class="lg:col-span-7 border border-stone-200/80">
        <template #header>
          <div class="flex items-center justify-between gap-2 border-b border-stone-100 pb-3">
            <div>
              <h3 class="text-base font-bold text-slate-800">Volume na Fila por Exame</h3>
              <p class="text-xs text-slate-500">
                Clique em um exame para abrir a fila operacional já filtrada.
              </p>
            </div>
            <span class="rounded-md border border-stone-200 bg-stone-50 px-2.5 py-1 text-xs font-semibold text-slate-700 tabular-nums">
              {{ totalAtivosNaFila }} ativo(s)
            </span>
          </div>
        </template>

        <div v-if="kpis.filaPorExame.length > 0" class="space-y-2.5">
          <button
            v-for="item in kpis.filaPorExame"
            :key="item.codigoExame"
            type="button"
            class="group w-full rounded-lg border border-transparent px-2.5 py-2 text-left transition-colors hover:border-stone-200 hover:bg-stone-50/90 cursor-pointer"
            :title="`Abrir Fila de Exames filtrada por ${item.exame}`"
            @click="abrirFilaPorExame(item.codigoExame)"
          >
            <div class="flex items-center justify-between gap-3 text-sm">
              <div class="flex items-center gap-2 min-w-0">
                <span class="rounded border border-stone-200 bg-stone-100 px-1.5 py-0.5 font-mono text-xs font-semibold text-slate-700 shrink-0">
                  {{ item.codigoExame }}
                </span>
                <span class="truncate font-medium text-slate-800 group-hover:text-teal-800 transition-colors">
                  {{ item.exame }}
                </span>
              </div>
              <span class="font-bold text-slate-800 tabular-nums shrink-0">
                {{ item.quantidade }}
              </span>
            </div>
            <div class="mt-1.5 h-2.5 w-full overflow-hidden rounded-full bg-stone-100">
              <div
                class="h-full rounded-full bg-teal-600 transition-[width] duration-300 ease-out group-hover:bg-teal-700"
                :style="{ width: `${calcularLarguraBarra(item.quantidade, maxVolumeExame)}%` }"
              ></div>
            </div>
          </button>
        </div>

        <div v-else class="py-10 text-center text-sm text-slate-500">
          Nenhum exame ativo na fila para o recorte selecionado.
        </div>
      </Card>

      <!-- Distribuição Geográfica & Urgência (Anel SVG + Legenda + TFD) -->
      <Card class="lg:col-span-5 border border-stone-200/80">
        <template #header>
          <div class="flex items-center justify-between gap-2 border-b border-stone-100 pb-3">
            <div>
              <h3 class="text-base font-bold text-slate-800">Distribuição Geográfica</h3>
              <p class="text-xs text-slate-500">
                Origem dos pacientes ativos na fila e cobertura TFD.
              </p>
            </div>
            <MapPinIcon class="h-5 w-5 text-teal-700 shrink-0" />
          </div>
        </template>

        <div class="flex flex-col gap-5 sm:flex-row sm:items-center">
          <!-- Anel SVG puro -->
          <div class="relative mx-auto flex h-40 w-40 shrink-0 items-center justify-center">
            <svg viewBox="0 0 160 160" class="h-full w-full -rotate-90" role="img" aria-label="Distribuição geográfica da fila ativa">
              <circle
                cx="80"
                cy="80"
                :r="RAIO_ANEL"
                fill="transparent"
                stroke="#ebe9e3"
                stroke-width="20"
              />
              <circle
                v-for="seg in segmentosAnel"
                :key="seg.regiao"
                cx="80"
                cy="80"
                :r="RAIO_ANEL"
                fill="transparent"
                :stroke="seg.cor"
                stroke-width="20"
                stroke-linecap="butt"
                :stroke-dasharray="`${seg.comprimento} ${CIRCUNFERENCIA_ANEL}`"
                :stroke-dashoffset="seg.offset"
                class="donut-segment"
              />
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center text-center">
              <span class="text-2xl font-extrabold text-slate-800 tabular-nums">
                {{ totalAtivosNaFila }}
              </span>
              <span class="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Na fila
              </span>
            </div>
          </div>

          <!-- Legenda detalhada -->
          <div class="flex-1 space-y-2">
            <button
              v-for="reg in kpis.filaPorRegiao"
              :key="reg.regiao"
              type="button"
              class="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left text-sm transition-colors hover:bg-stone-50 cursor-pointer"
              @click="abrirFilaPorRegiao(reg.regiao)"
            >
              <span class="flex items-center gap-2 min-w-0">
                <span
                  class="h-3 w-3 rounded-full shrink-0"
                  :style="{ backgroundColor: CORES_REGIAO[reg.regiao] }"
                ></span>
                <span class="truncate text-slate-700">{{ reg.label }}</span>
              </span>
              <span class="ml-2 font-semibold text-slate-800 tabular-nums shrink-0">
                {{ reg.quantidade }}
                <span class="text-xs font-normal text-slate-500">({{ reg.percentual }}%)</span>
              </span>
            </button>
          </div>
        </div>

        <!-- Destaque TFD -->
        <div class="mt-5 rounded-lg border border-sky-200 bg-sky-50/70 p-3.5 text-xs text-sky-900">
          <div class="flex items-center justify-between gap-2">
            <span class="font-bold flex items-center gap-1.5">
              <TruckIcon class="h-4 w-4 text-sky-700 shrink-0" />
              Apoio Logístico TFD (Intermunicipal)
            </span>
            <span class="font-bold tabular-nums">
              {{ kpis.totalTfdFila }} paciente(s) · {{ percentualTfd }}%
            </span>
          </div>
          <p class="mt-1 text-sky-800">
            Pacientes de fora da Capital que dependem de transporte municipal exigem confirmação com antecedência para emissão de guia TFD.
          </p>
        </div>
      </Card>
    </div>

    <!-- Funil de Qualidade da Higienização Forms × AGHU + Unidades -->
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-12">
      <Card class="lg:col-span-7 border border-stone-200/80">
        <template #header>
          <div class="flex flex-wrap items-center justify-between gap-2 border-b border-stone-100 pb-3">
            <div>
              <h3 class="text-base font-bold text-slate-800">
                Funil de Qualidade da Higienização (Forms × AGHU)
              </h3>
              <p class="text-xs text-slate-500">
                Comparativo entre solicitações validadas e ocorrências barradas antes de poluir a fila.
              </p>
            </div>
            <span class="rounded-md border border-stone-200 bg-stone-50 px-2.5 py-1 text-xs font-semibold text-slate-700 tabular-nums">
              {{ totalAnalisadoFunil }} registros avaliados
            </span>
          </div>
        </template>

        <div class="space-y-5">
          <!-- Barra empilhada proporcional -->
          <div>
            <div class="flex h-4 w-full overflow-hidden rounded-full bg-stone-100">
              <div
                v-for="etapa in etapasFunil"
                :key="etapa.chave"
                class="h-full transition-[width] duration-300 ease-out"
                :class="etapa.corBarra"
                :style="{ width: `${etapa.percentual}%` }"
                :title="`${etapa.label}: ${etapa.quantidade} (${etapa.percentual}%)`"
              ></div>
            </div>
          </div>

          <!-- Blocos de métricas do funil (máx 2 níveis) -->
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div
              v-for="etapa in etapasFunil"
              :key="etapa.chave"
              class="rounded-lg border border-stone-200/80 bg-stone-50/50 p-3.5"
            >
              <div class="flex items-center justify-between gap-2">
                <span class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-600">
                  <span class="h-2.5 w-2.5 rounded-full shrink-0" :class="etapa.corBarra"></span>
                  {{ etapa.label }}
                </span>
                <span
                  class="rounded-full px-2 py-0.5 text-[11px] font-bold tabular-nums"
                  :class="etapa.badgeClasse"
                >
                  {{ etapa.percentual }}%
                </span>
              </div>
              <p class="mt-2 text-2xl font-extrabold text-slate-800 tabular-nums">
                {{ etapa.quantidade }}
              </p>
              <p class="mt-0.5 text-xs text-slate-500">{{ etapa.descricao }}</p>
            </div>
          </div>
        </div>
      </Card>

      <!-- Demanda por Unidade Solicitante -->
      <Card class="lg:col-span-5 border border-stone-200/80">
        <template #header>
          <div class="flex items-center justify-between gap-2 border-b border-stone-100 pb-3">
            <div>
              <h3 class="text-base font-bold text-slate-800">Unidades Solicitantes</h3>
              <p class="text-xs text-slate-500">
                Concentração da fila ativa por ambulatório ou serviço de origem.
              </p>
            </div>
            <BuildingOffice2Icon class="h-5 w-5 text-teal-700 shrink-0" />
          </div>
        </template>

        <div v-if="kpis.filaPorUnidade.length > 0" class="space-y-3">
          <div
            v-for="u in kpis.filaPorUnidade"
            :key="u.unidade"
            class="space-y-1"
          >
            <div class="flex items-center justify-between gap-2 text-sm">
              <span class="truncate font-medium text-slate-700">{{ u.unidade }}</span>
              <span class="font-bold text-slate-800 tabular-nums shrink-0">{{ u.quantidade }}</span>
            </div>
            <div class="h-2 w-full overflow-hidden rounded-full bg-stone-100">
              <div
                class="h-full rounded-full bg-sky-600 transition-[width] duration-300 ease-out"
                :style="{ width: `${calcularLarguraBarra(u.quantidade, maxVolumeUnidade)}%` }"
              ></div>
            </div>
          </div>
        </div>

        <div v-else class="py-10 text-center text-sm text-slate-500">
          Nenhuma unidade com itens ativos neste recorte.
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  ArrowPathIcon,
  BuildingOffice2Icon,
  CalendarDaysIcon,
  CheckCircleIcon,
  ClockIcon,
  MapPinIcon,
  QueueListIcon,
  ShieldExclamationIcon,
  TruckIcon,
} from '@heroicons/vue/24/outline';
import Card from '../components/Card.vue';
import Button from '../components/Button.vue';
import { useDashboardStore } from '../stores/dashboard';
import { useExamesStore } from '../stores/exames';
import type { PeriodoDashboard, RegiaoGeografica } from '../types/exames';

const MS_DIA = 24 * 60 * 60 * 1000;
const RAIO_ANEL = 56;
const CIRCUNFERENCIA_ANEL = 2 * Math.PI * RAIO_ANEL;

const CORES_REGIAO: Record<RegiaoGeografica, string> = {
  CAPITAL: '#0f766e',
  RMR: '#0284c7',
  INTERIOR: '#d97706',
  NAO_INFORMADO: '#78716c',
};

const opcoesPeriodo: Array<{ valor: PeriodoDashboard; label: string }> = [
  { valor: 7, label: '7 dias' },
  { valor: 30, label: '30 dias' },
  { valor: 90, label: '90 dias' },
  { valor: 'TODOS', label: 'Todo o período' },
];

const router = useRouter();
const dashboardStore = useDashboardStore();
const examesStore = useExamesStore();

const kpis = computed(() => dashboardStore.kpis);
const animandoNumeros = ref(false);
let timerAnimacao: ReturnType<typeof setTimeout> | null = null;

// Controle da pílula deslizante (.t-tabs-pill)
const tabsContainerRef = ref<HTMLElement | null>(null);
const abaRefs = ref<Array<HTMLElement | null>>([]);
const pillStyle = ref<{ transform: string; width: string }>({
  transform: 'translateX(0px)',
  width: '0px',
});

function registrarRefAba(el: unknown, idx: number): void {
  abaRefs.value[idx] = el instanceof HTMLElement ? el : null;
}

function atualizarPosicaoPill(): void {
  const idx = opcoesPeriodo.findIndex((op) => op.valor === dashboardStore.periodoDias);
  const botao = idx >= 0 ? abaRefs.value[idx] : null;
  if (!botao) {
    return;
  }
  pillStyle.value = {
    transform: `translateX(${botao.offsetLeft}px)`,
    width: `${botao.offsetWidth}px`,
  };
}

function dispararAnimacaoNumeros(): void {
  if (timerAnimacao) {
    clearTimeout(timerAnimacao);
  }
  animandoNumeros.value = false;
  requestAnimationFrame(() => {
    animandoNumeros.value = true;
    timerAnimacao = setTimeout(() => {
      animandoNumeros.value = false;
    }, 480);
  });
}

function selecionarPeriodo(dias: PeriodoDashboard): void {
  if (dashboardStore.periodoDias === dias) {
    return;
  }
  dashboardStore.definirPeriodo(dias);
  dispararAnimacaoNumeros();
}

function onUnidadeChange(event: Event): void {
  const select = event.target as HTMLSelectElement;
  dashboardStore.definirUnidade(select.value);
  dispararAnimacaoNumeros();
}

async function handleAtualizarIndicadores(): Promise<void> {
  await dashboardStore.atualizarIndicadores();
  dispararAnimacaoNumeros();
}

const labelPeriodoAtivo = computed(() => {
  const encontrado = opcoesPeriodo.find((op) => op.valor === dashboardStore.periodoDias);
  return encontrado ? encontrado.label : 'Todo o período';
});

const ultimaAtualizacaoFormatada = computed(() => {
  const dt = new Date(dashboardStore.ultimaAtualizacao);
  if (Number.isNaN(dt.getTime())) {
    return '—';
  }
  return dt.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
});

const totalAtivosNaFila = computed(() => kpis.value.totalNaFila + kpis.value.aguardando24h);

const tempoMedioFormatado = computed(() =>
  kpis.value.tempoMedioEsperaDias.toFixed(1).replace('.', ','),
);

const totalBarradasHigienizacao = computed(
  () => kpis.value.duplicidadesBarradas + kpis.value.divergenciasDetectadas,
);

const percentualTfd = computed(() => {
  if (totalAtivosNaFila.value === 0) {
    return 0;
  }
  return Math.round((kpis.value.totalTfdFila / totalAtivosNaFila.value) * 100);
});

const maxVolumeExame = computed(() =>
  kpis.value.filaPorExame.reduce((max, item) => Math.max(max, item.quantidade), 0),
);

const maxVolumeUnidade = computed(() =>
  kpis.value.filaPorUnidade.reduce((max, item) => Math.max(max, item.quantidade), 0),
);

function calcularLarguraBarra(valor: number, maximo: number): number {
  if (maximo <= 0 || valor <= 0) {
    return 0;
  }
  return Math.max(6, Math.round((valor / maximo) * 100));
}

const segmentosAnel = computed(() => {
  const total = totalAtivosNaFila.value;
  if (total <= 0) {
    return [];
  }
  let acumulado = 0;
  return kpis.value.filaPorRegiao
    .filter((reg) => reg.quantidade > 0)
    .map((reg) => {
      const fracao = reg.quantidade / total;
      const comprimento = fracao * CIRCUNFERENCIA_ANEL;
      const offset = -acumulado;
      acumulado += comprimento;
      return {
        regiao: reg.regiao,
        cor: CORES_REGIAO[reg.regiao],
        comprimento,
        offset,
      };
    });
});

const totalValidasHigienizacao = computed(() => {
  const agoraMs = Date.now();
  const limiteMs =
    dashboardStore.periodoDias === 'TODOS'
      ? null
      : agoraMs - dashboardStore.periodoDias * MS_DIA;
  const unidadeAlvo = dashboardStore.unidadeFiltro.trim().toUpperCase();

  const validasFila = examesStore.itensEnriquecidos.filter((item) => {
    if (item.statusHigienizacao !== 'VALIDA') {
      return false;
    }
    if (unidadeAlvo && !(item.unidadeSolicitante ?? '').toUpperCase().includes(unidadeAlvo)) {
      return false;
    }
    if (limiteMs !== null && item.dataSolicitacao) {
      const ts = new Date(item.dataSolicitacao).getTime();
      if (!Number.isNaN(ts) && ts < limiteMs) {
        return false;
      }
    }
    return true;
  }).length;

  if (unidadeAlvo) {
    return validasFila;
  }

  const validasHistorico = examesStore.historicoImportacoes
    .filter((imp) => {
      if (limiteMs === null) {
        return true;
      }
      const ts = new Date(imp.importadoEm).getTime();
      return Number.isNaN(ts) || ts >= limiteMs;
    })
    .reduce((acc, imp) => acc + imp.totalValidas, 0);

  return Math.max(validasHistorico, validasFila);
});

const totalAnalisadoFunil = computed(
  () =>
    totalValidasHigienizacao.value +
    kpis.value.duplicidadesBarradas +
    kpis.value.divergenciasDetectadas +
    kpis.value.naoEncontradasAghu,
);

const etapasFunil = computed(() => {
  const total = totalAnalisadoFunil.value;
  const pct = (qtd: number): number => (total > 0 ? Math.round((qtd / total) * 100) : 0);

  return [
    {
      chave: 'VALIDA',
      label: 'Válidas (Aptas para Fila)',
      quantidade: totalValidasHigienizacao.value,
      percentual: pct(totalValidasHigienizacao.value),
      corBarra: 'bg-emerald-600',
      badgeClasse: 'bg-emerald-50 text-emerald-800 border border-emerald-200',
      descricao: 'Confirmadas no espelho AGHU sem duplicidade ou conflito de exame.',
    },
    {
      chave: 'DUPLICADA',
      label: 'Duplicadas Barradas',
      quantidade: kpis.value.duplicidadesBarradas,
      percentual: pct(kpis.value.duplicidadesBarradas),
      corBarra: 'bg-amber-500',
      badgeClasse: 'bg-amber-50 text-amber-800 border border-amber-200',
      descricao: 'Reenvios no Forms bloqueados antes de duplicar o paciente na fila.',
    },
    {
      chave: 'DIVERGENTE',
      label: 'Divergentes Forms × AGHU',
      quantidade: kpis.value.divergenciasDetectadas,
      percentual: pct(kpis.value.divergenciasDetectadas),
      corBarra: 'bg-orange-500',
      badgeClasse: 'bg-amber-50 text-amber-800 border border-amber-200',
      descricao: 'Exame digitado no formulário difere do pedido oficial no AGHU.',
    },
    {
      chave: 'NAO_ENCONTRADA',
      label: 'Não Encontradas (Busca Ativa)',
      quantidade: kpis.value.naoEncontradasAghu,
      percentual: pct(kpis.value.naoEncontradasAghu),
      corBarra: 'bg-red-600',
      badgeClasse: 'bg-red-50 text-red-800 border border-red-200',
      descricao: 'Solicitação ausente ou digitada incorretamente; requer vínculo AGHU.',
    },
  ];
});

function abrirFilaPorExame(codigoExame: string): void {
  examesStore.limparFiltros();
  if (codigoExame && codigoExame !== 'PENDENTE') {
    examesStore.definirFiltros({ codigoExame });
    router.push({ path: '/fila', query: { exame: codigoExame } });
  } else {
    examesStore.definirFiltros({ statusHigienizacao: 'NAO_ENCONTRADA' });
    router.push({ path: '/fila' });
  }
}

function abrirFilaPorRegiao(regiao: RegiaoGeografica): void {
  examesStore.limparFiltros();
  examesStore.definirFiltros({ regiao });
  router.push({ path: '/fila', query: { regiao } });
}

function abrirFilaVencidos24h(): void {
  examesStore.limparFiltros();
  examesStore.definirFiltros({ apenas24hVencidos: true });
  router.push({ path: '/fila' });
}

function abrirFilaTfd(): void {
  examesStore.limparFiltros();
  examesStore.definirFiltros({ apenasTfd: true });
  router.push({ path: '/fila' });
}

watch(
  () => dashboardStore.periodoDias,
  async () => {
    await nextTick();
    atualizarPosicaoPill();
  },
);

onMounted(async () => {
  await nextTick();
  atualizarPosicaoPill();
  window.addEventListener('resize', atualizarPosicaoPill);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', atualizarPosicaoPill);
  if (timerAnimacao) {
    clearTimeout(timerAnimacao);
  }
});
</script>

<style scoped>
.donut-segment {
  transition:
    stroke-dasharray var(--duration-slow) var(--ease-smooth-out),
    stroke-dashoffset var(--duration-slow) var(--ease-smooth-out);
}
</style>
