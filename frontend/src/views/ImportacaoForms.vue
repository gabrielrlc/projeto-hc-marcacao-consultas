<template>
  <div class="space-y-6">
    <!-- Upload da planilha do Google Forms (CSV/XLSX), sem alterar o arquivo original -->
    <Card>
      <div class="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <h2 class="text-lg font-semibold text-gray-800">Importar planilha do Google Forms</h2>
          <p class="text-sm text-paper-text">
            Envie a exportação da planilha (.csv ou .xlsx). Cada resposta é cruzada com o AGHU para detectar
            código inválido, exame divergente, duplicidade e exame já realizado. A planilha não é alterada.
          </p>
        </div>
        <a href="/modelo_planilha_forms.csv" download class="text-sm font-semibold text-paper-primary hover:underline">
          Baixar planilha de exemplo
        </a>
      </div>

      <div
        :class="arrastando ? 'border-paper-primary bg-blue-50' : 'border-gray-300 bg-gray-50'"
        class="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-8 text-center transition-colors"
        @dragover.prevent="arrastando = true"
        @dragleave.prevent="arrastando = false"
        @drop.prevent="aoSoltarArquivo"
      >
        <ArrowUpTrayIcon class="h-10 w-10 text-gray-400" />
        <p class="text-sm text-gray-700">
          Arraste a planilha aqui ou
          <button type="button" class="font-semibold text-paper-primary hover:underline" @click="abrirSeletor">
            selecione um arquivo
          </button>
        </p>
        <p class="text-xs text-gray-500">Formatos aceitos: .csv e .xlsx</p>
        <input ref="inputArquivo" type="file" accept=".csv,.xlsx" class="hidden" @change="aoSelecionarArquivo">
      </div>

      <div v-if="arquivo" class="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-md bg-gray-50 px-4 py-3">
        <div class="flex items-center gap-2 text-sm text-gray-700">
          <DocumentTextIcon class="h-5 w-5 text-gray-500" />
          <span class="font-medium">{{ arquivo.name }}</span>
          <span class="text-gray-500">({{ formatarTamanho(arquivo.size) }})</span>
        </div>
        <div class="flex gap-2">
          <Button type="button" variant="default" :disabled="store.enviando" @click="limparArquivo">Remover</Button>
          <Button type="button" variant="primary" :loading="store.enviando" @click="enviar">
            <template #icon><DocumentArrowUpIcon class="h-5 w-5" /></template>
            {{ store.enviando ? 'Higienizando…' : 'Importar e higienizar' }}
          </Button>
        </div>
      </div>

      <p v-if="erroArquivo || store.erroEnvio" class="mt-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
        {{ erroArquivo || store.erroEnvio }}
      </p>
    </Card>

    <!-- Relatório de higienização do lote selecionado -->
    <Card v-if="relatorio">
      <div class="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <h2 class="text-lg font-semibold text-gray-800">Relatório de higienização · lote #{{ relatorio.importacao.id }}</h2>
          <p class="text-sm text-paper-text">
            {{ relatorio.importacao.nomeArquivo }} · importado em {{ formatarDataHora(relatorio.importacao.importadoEm) }}
            por {{ relatorio.importacao.usuarioImportador }}
          </p>
        </div>
        <Button type="button" variant="info" @click="router.push('/fila')">
          <template #icon><QueueListIcon class="h-5 w-5" /></template>
          Ver fila priorizada
        </Button>
      </div>

      <div class="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6 mb-4">
        <div class="rounded-lg border border-gray-200 px-4 py-3">
          <p class="text-xs font-semibold uppercase text-gray-500">Linhas lidas</p>
          <p class="text-2xl font-bold text-gray-800">{{ relatorio.importacao.totalLinhas }}</p>
          <p class="text-xs text-gray-500">{{ taxaAproveitamento }}% aproveitadas</p>
        </div>
        <div v-for="status in ORDEM_STATUS" :key="status" :class="COR_CARTAO[status]" class="rounded-lg border px-4 py-3">
          <p class="text-xs font-semibold uppercase">{{ ROTULO_HIGIENIZACAO[status] }}</p>
          <p class="text-2xl font-bold">{{ relatorio.contadores[status] ?? 0 }}</p>
          <p class="text-xs">{{ DESCRICAO_STATUS[status] }}</p>
        </div>
      </div>

      <details class="mb-4 rounded-md bg-gray-50 px-4 py-3 text-sm text-gray-700">
        <summary class="cursor-pointer font-semibold">
          Colunas da planilha ({{ Object.keys(relatorio.colunasReconhecidas).length }} reconhecidas,
          {{ relatorio.colunasIgnoradas.length }} ignoradas)
        </summary>
        <ul class="mt-2 grid grid-cols-1 gap-1 md:grid-cols-2">
          <li v-for="(coluna, campo) in relatorio.colunasReconhecidas" :key="campo">
            <span class="font-medium">{{ ROTULO_CAMPO[campo] ?? campo }}</span> ← “{{ coluna }}”
          </li>
        </ul>
        <p v-if="relatorio.colunasIgnoradas.length" class="mt-2 text-gray-500">
          Ignoradas: {{ relatorio.colunasIgnoradas.join(', ') }}
        </p>
      </details>

      <div class="mb-4 flex flex-wrap gap-2" role="tablist" aria-label="Filtrar linhas por resultado">
        <button
          v-for="aba in ABAS"
          :key="aba.valor"
          type="button"
          role="tab"
          :aria-selected="filtroStatus === aba.valor"
          :class="filtroStatus === aba.valor ? 'bg-paper-primary text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
          class="rounded-full px-3 py-1 text-sm font-semibold transition-colors"
          @click="filtroStatus = aba.valor"
        >
          {{ aba.rotulo }} ({{ contagemAba(aba.valor) }})
        </button>
      </div>

      <p v-if="store.erroRelatorio" class="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
        {{ store.erroRelatorio }}
      </p>

      <DataTable :headers="colunasItens" :items="itensFiltrados">
        <template #cell-linha="{ item }">
          <span class="text-gray-500">{{ item.linhaPlanilha ?? '—' }}</span>
        </template>
        <template #cell-paciente="{ item }">
          <p class="font-medium text-gray-800">{{ item.nomePaciente }}</p>
          <p class="text-xs text-gray-500">
            Pront. {{ item.prontuario ?? '—' }} · Solic. {{ item.codigoSolicitacao }}
            <span v-if="item.idadeInformada !== null"> · {{ item.idadeInformada }} anos</span>
          </p>
        </template>
        <template #cell-exame="{ item }">
          <p>{{ item.exameInformadoForms || '—' }}</p>
          <p class="text-xs text-gray-500">
            AGHU: {{ item.codigoExame ?? 'sem correspondência' }}
            <span v-if="item.unidadeSolicitante"> · {{ item.unidadeSolicitante }}</span>
          </p>
        </template>
        <template #cell-municipio="{ item }">
          <p>{{ item.municipio ?? 'Não informado' }}</p>
          <p class="text-xs text-gray-500">
            {{ ROTULO_REGIAO[item.regiaoGeografica as RegiaoGeografica] ?? item.regiaoGeografica }}
            <span v-if="item.utilizaTfd" class="ml-1 rounded bg-indigo-100 px-1.5 py-0.5 font-semibold text-indigo-800">TFD</span>
          </p>
        </template>
        <template #cell-retorno="{ item }">
          {{ item.dataRetornoMedico ? formatarData(item.dataRetornoMedico) : '—' }}
        </template>
        <template #cell-resultado="{ item }">
          <span :class="COR_BADGE[item.statusHigienizacao as StatusHigienizacao]"
            class="rounded-full px-2 py-0.5 text-xs font-semibold whitespace-nowrap">
            {{ ROTULO_BADGE[item.statusHigienizacao as StatusHigienizacao] }}
          </span>
          <p v-if="item.observacoes" class="mt-1 max-w-xs text-xs text-gray-500">{{ item.observacoes }}</p>
        </template>
      </DataTable>
    </Card>

    <!-- Histórico de importações -->
    <Card>
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h2 class="text-lg font-semibold text-gray-800">Histórico de importações</h2>
          <p class="text-sm text-paper-text">{{ store.historico.length }} lote(s) registrado(s)</p>
        </div>
        <Button type="button" variant="default" :loading="store.carregandoHistorico" @click="store.carregarHistorico()">
          <template #icon><ArrowPathIcon class="h-5 w-5" /></template>
          Atualizar
        </Button>
      </div>

      <p v-if="store.erroHistorico" class="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
        {{ store.erroHistorico }}
      </p>

      <DataTable :headers="colunasHistorico" :items="store.historico">
        <template #cell-arquivo="{ item }">
          <p class="font-medium text-gray-800">{{ item.nomeArquivo }}</p>
          <p class="text-xs text-gray-500">Lote #{{ item.id }} · {{ item.usuarioImportador }}</p>
        </template>
        <template #cell-importadoEm="{ item }">{{ formatarDataHora(item.importadoEm) }}</template>
        <template #cell-totalValidas="{ item }">
          <span class="font-semibold text-green-700">{{ item.totalValidas }}</span>
        </template>
        <template #cell-totalDuplicadas="{ item }">
          <span class="font-semibold text-gray-700">{{ item.totalDuplicadas }}</span>
        </template>
        <template #cell-totalErros="{ item }">
          <span class="font-semibold text-orange-700">{{ item.totalErros }}</span>
        </template>
        <template #actions="{ item }">
          <Button
            variant="info"
            :disabled="store.carregandoRelatorio"
            title="Ver relatório"
            aria-label="Ver relatório"
            @click="abrirRelatorio(item.id as number)"
          >
            <EyeIcon class="h-4 w-4" />
          </Button>
        </template>
      </DataTable>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'vue-toastification';
import {
  ArrowPathIcon,
  ArrowUpTrayIcon,
  DocumentArrowUpIcon,
  DocumentTextIcon,
  EyeIcon,
  QueueListIcon,
} from '@heroicons/vue/24/outline';
import Card from '../components/Card.vue';
import Button from '../components/Button.vue';
import DataTable from '../components/DataTable.vue';
import { useImportacoesStore } from '../stores/importacoes';
import type { RegiaoGeografica, StatusHigienizacao } from '../types/exames';

type FiltroStatus = 'TODAS' | StatusHigienizacao;

/** Mesmo limite do backend (planilha_forms_helper.TAMANHO_MAXIMO_BYTES). */
const TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024;

const ORDEM_STATUS: StatusHigienizacao[] = ['VALIDA', 'DUPLICADA', 'DIVERGENCIA_EXAME', 'NAO_ENCONTRADA', 'JA_REALIZADA'];

const ROTULO_HIGIENIZACAO: Record<StatusHigienizacao, string> = {
  VALIDA: 'Válidas',
  DUPLICADA: 'Duplicadas',
  DIVERGENCIA_EXAME: 'Divergência de exame',
  NAO_ENCONTRADA: 'Não encontradas no AGHU',
  JA_REALIZADA: 'Já realizadas',
};
const ROTULO_BADGE: Record<StatusHigienizacao, string> = {
  VALIDA: 'Válida',
  DUPLICADA: 'Duplicada',
  DIVERGENCIA_EXAME: 'Divergência de exame',
  NAO_ENCONTRADA: 'Não encontrada no AGHU',
  JA_REALIZADA: 'Já realizada',
};
const DESCRICAO_STATUS: Record<StatusHigienizacao, string> = {
  VALIDA: 'Entraram na fila',
  DUPLICADA: 'Envios repetidos barrados',
  DIVERGENCIA_EXAME: 'Exame do Forms ≠ AGHU',
  NAO_ENCONTRADA: 'Código inválido ou inexistente',
  JA_REALIZADA: 'Agendadas ou concluídas',
};
const COR_CARTAO: Record<StatusHigienizacao, string> = {
  VALIDA: 'border-green-200 bg-green-50 text-green-800',
  DUPLICADA: 'border-gray-200 bg-gray-50 text-gray-700',
  DIVERGENCIA_EXAME: 'border-amber-200 bg-amber-50 text-amber-800',
  NAO_ENCONTRADA: 'border-red-200 bg-red-50 text-red-800',
  JA_REALIZADA: 'border-sky-200 bg-sky-50 text-sky-800',
};
const COR_BADGE: Record<StatusHigienizacao, string> = {
  VALIDA: 'bg-green-100 text-green-800',
  DUPLICADA: 'bg-gray-200 text-gray-700',
  DIVERGENCIA_EXAME: 'bg-amber-100 text-amber-800',
  NAO_ENCONTRADA: 'bg-red-100 text-red-800',
  JA_REALIZADA: 'bg-sky-100 text-sky-800',
};
const ROTULO_REGIAO: Record<RegiaoGeografica, string> = {
  CAPITAL: 'Capital',
  RMR: 'Região Metropolitana',
  INTERIOR: 'Interior',
  NAO_INFORMADO: 'Região não informada',
};
/** Nomes amigáveis dos campos que o backend reconhece na planilha. */
const ROTULO_CAMPO: Record<string, string> = {
  codigoSolicitacao: 'Nº da solicitação',
  prontuario: 'Prontuário',
  nomePaciente: 'Nome do paciente',
  exameInformado: 'Exame desejado',
  dataRetorno: 'Data do retorno',
  telefone: 'Telefone/WhatsApp',
  municipio: 'Município',
  idade: 'Idade',
  carimbo: 'Carimbo de data/hora',
  tfd: 'TFD',
};

const ABAS: Array<{ valor: FiltroStatus; rotulo: string }> = [
  { valor: 'TODAS', rotulo: 'Todas' },
  ...ORDEM_STATUS.map((status) => ({ valor: status, rotulo: ROTULO_HIGIENIZACAO[status] })),
];

const colunasItens = [
  { text: 'Linha', value: 'linha' },
  { text: 'Paciente', value: 'paciente' },
  { text: 'Exame (Forms / AGHU)', value: 'exame' },
  { text: 'Município', value: 'municipio' },
  { text: 'Retorno', value: 'retorno' },
  { text: 'Resultado', value: 'resultado' },
];
const colunasHistorico = [
  { text: 'Arquivo', value: 'arquivo' },
  { text: 'Importado em', value: 'importadoEm' },
  { text: 'Linhas', value: 'totalLinhas' },
  { text: 'Válidas', value: 'totalValidas' },
  { text: 'Duplicadas', value: 'totalDuplicadas' },
  { text: 'Para revisão', value: 'totalErros' },
];

const store = useImportacoesStore();
const router = useRouter();
const toast = useToast();

const inputArquivo = ref<HTMLInputElement | null>(null);
const arquivo = ref<File | null>(null);
const arrastando = ref(false);
const erroArquivo = ref('');
const filtroStatus = ref<FiltroStatus>('TODAS');

const relatorio = computed(() => store.relatorio);

const taxaAproveitamento = computed(() => {
  const lote = relatorio.value?.importacao;
  if (!lote || lote.totalLinhas === 0) return 0;
  return Math.round((lote.totalValidas / lote.totalLinhas) * 100);
});

const itensFiltrados = computed(() => {
  const itens = relatorio.value?.itens ?? [];
  const filtrados = filtroStatus.value === 'TODAS'
    ? itens
    : itens.filter((item) => item.statusHigienizacao === filtroStatus.value);
  return [...filtrados].sort((a, b) => (a.linhaPlanilha ?? 0) - (b.linhaPlanilha ?? 0));
});

function contagemAba(valor: FiltroStatus): number {
  const itens = relatorio.value?.itens ?? [];
  return valor === 'TODAS' ? itens.length : itens.filter((item) => item.statusHigienizacao === valor).length;
}

/** Valida extensão e tamanho antes de enviar (o backend valida de novo). */
function validarArquivo(candidato: File): string {
  if (!/\.(csv|xlsx)$/i.test(candidato.name)) {
    return 'Formato não suportado. Envie a planilha do Forms em .csv ou .xlsx.';
  }
  if (candidato.size === 0) {
    return 'O arquivo está vazio.';
  }
  if (candidato.size > TAMANHO_MAXIMO_BYTES) {
    return 'O arquivo passa do limite de 5 MB.';
  }
  return '';
}

function definirArquivo(candidato: File | undefined): void {
  if (!candidato) return;
  const erro = validarArquivo(candidato);
  erroArquivo.value = erro;
  store.erroEnvio = null;
  arquivo.value = erro ? null : candidato;
}

function abrirSeletor(): void {
  inputArquivo.value?.click();
}

function aoSelecionarArquivo(evento: Event): void {
  const input = evento.target as HTMLInputElement;
  definirArquivo(input.files?.[0]);
  input.value = '';
}

function aoSoltarArquivo(evento: DragEvent): void {
  arrastando.value = false;
  definirArquivo(evento.dataTransfer?.files?.[0]);
}

function limparArquivo(): void {
  arquivo.value = null;
  erroArquivo.value = '';
}

async function enviar(): Promise<void> {
  if (!arquivo.value) {
    erroArquivo.value = 'Selecione a planilha antes de importar.';
    return;
  }
  const resultado = await store.enviarPlanilha(arquivo.value);
  if (!resultado) {
    toast.error(store.erroEnvio ?? 'Falha ao importar a planilha.');
    return;
  }
  const { contadores } = resultado;
  const revisar = (contadores.DIVERGENCIA_EXAME ?? 0) + (contadores.NAO_ENCONTRADA ?? 0);
  toast.success(
    `Importação concluída: ${contadores.VALIDA ?? 0} válidas, ${contadores.DUPLICADA ?? 0} duplicadas barradas e ${revisar} para revisão.`,
  );
  filtroStatus.value = 'TODAS';
  limparArquivo();
}

async function abrirRelatorio(id: number): Promise<void> {
  filtroStatus.value = 'TODAS';
  const resultado = await store.carregarRelatorio(id);
  if (!resultado) {
    toast.error(store.erroRelatorio ?? 'Não foi possível abrir o relatório.');
  }
}

function formatarTamanho(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

/** Datas-hora do backend chegam em UTC sem "Z". */
function formatarDataHora(iso: string): string {
  const normalizado = /[zZ]|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : `${iso}Z`;
  const data = new Date(normalizado);
  if (Number.isNaN(data.getTime())) return iso;
  return data.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
}

function formatarData(valor: string): string {
  const partes = valor.slice(0, 10).split('-');
  return partes.length === 3 ? `${partes[2]}/${partes[1]}/${partes[0]}` : valor;
}

onMounted(async () => {
  const historico = await store.carregarHistorico();
  if (historico && historico.length > 0 && !store.relatorio) {
    await store.carregarRelatorio(historico[0].id);
  }
});
</script>
