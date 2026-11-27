<template>
  <div class="space-y-6">
    <Card>
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 class="text-lg font-semibold text-gray-800">Regras configuráveis da fila</h2>
          <p class="text-sm text-paper-text">
            Pesos de prioridade, regras de preparo/retorno por exame e incompatibilidades usados no score e nos alertas.
            Alterações valem para os próximos cálculos da fila e ficam registradas na auditoria.
          </p>
        </div>
        <Button type="button" variant="default" :loading="store.carregando" @click="carregarTudo">
          <template #icon><ArrowPathIcon class="h-5 w-5" /></template>
          Atualizar
        </Button>
      </div>

      <div class="mt-4 flex flex-wrap gap-2 border-b border-gray-200" role="tablist" aria-label="Tipos de regra">
        <button
          v-for="aba in ABAS"
          :key="aba.valor"
          type="button"
          role="tab"
          :aria-selected="abaAtiva === aba.valor"
          :class="abaAtiva === aba.valor ? 'border-paper-primary text-paper-primary' : 'border-transparent text-gray-500 hover:text-gray-700'"
          class="-mb-px border-b-2 px-4 py-2 text-sm font-semibold transition-colors"
          @click="abaAtiva = aba.valor"
        >
          {{ aba.rotulo }} ({{ contagem[aba.valor] }})
        </button>
      </div>
    </Card>

    <Card>
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        <p class="text-sm text-paper-text">{{ DESCRICAO_ABA[abaAtiva] }}</p>
        <Button type="button" variant="primary" @click="abrirNovo">
          <template #icon><PlusIcon class="h-5 w-5" /></template>
          {{ ROTULO_NOVO[abaAtiva] }}
        </Button>
      </div>

      <p v-if="store.erro && !modalFormulario" class="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
        {{ store.erro }}
      </p>

      <!-- Pesos de Prioridade -->
      <DataTable v-if="abaAtiva === 'prioridades'" :headers="colunasPrioridades" :items="prioridadesOrdenadas">
        <template #cell-criterio="{ item }">
          <p class="font-medium text-gray-800">{{ item.nome }}</p>
          <p class="text-xs text-gray-500">{{ item.codigo }}<span v-if="item.descricao"> · {{ item.descricao }}</span></p>
        </template>
        <template #cell-tipo="{ item }">{{ ROTULO_CRITERIO[item.tipoCriterio as TipoCriterio] }}</template>
        <template #cell-valorMatch="{ item }">
          <span class="text-xs text-gray-600">{{ item.valorMatch || '—' }}</span>
        </template>
        <template #cell-peso="{ item }">
          <span class="inline-block min-w-12 rounded-full bg-paper-primary px-2.5 py-1 text-center text-sm font-bold text-white">
            +{{ item.peso }}
          </span>
        </template>
        <template #cell-ativo="{ item }"><BadgeAtivo :ativo="item.ativo" /></template>
        <template #actions="{ item }">
          <AcoesLinha
            :ativo="item.ativo"
            :desabilitado="store.carregando"
            @editar="abrirEdicao(item as IRegraPrioridade)"
            @alternar="alternarAtivo(item as IRegraPrioridade)"
            @remover="pedirRemocao(item.id as number, `${item.codigo} · ${item.nome}`)"
          />
        </template>
      </DataTable>

      <!-- Regras por Exame -->
      <DataTable v-else-if="abaAtiva === 'exames'" :headers="colunasExames" :items="examesOrdenados">
        <template #cell-exame="{ item }">
          <p class="font-medium text-gray-800">{{ item.nomeExame }}</p>
          <p class="text-xs text-gray-500">{{ item.codigoExame }}<span v-if="item.unidadeExecutora"> · {{ item.unidadeExecutora }}</span></p>
        </template>
        <template #cell-prazos="{ item }">
          <p class="text-xs">Antecedência: {{ item.antecedenciaMinimaDias }} dia(s)</p>
          <p class="text-xs">Retorno: {{ formatarJanela(item.janelaRetornoMaxHoras) }}</p>
        </template>
        <template #cell-preparo="{ item }">
          <div class="flex flex-wrap gap-1">
            <span v-if="item.exigeJejum" class="rounded bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">Jejum</span>
            <span v-if="item.priorizarManhaDiabetico" class="rounded bg-sky-100 px-2 py-0.5 text-xs font-semibold text-sky-800">Manhã p/ diabético</span>
            <span v-if="item.idadeMinimaAlerta !== null" class="rounded bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-700">
              Alerta &lt; {{ item.idadeMinimaAlerta }} anos
            </span>
          </div>
          <p v-if="item.orientacoesPreparo" class="mt-1 max-w-xs truncate text-xs text-gray-500" :title="item.orientacoesPreparo">
            {{ item.orientacoesPreparo }}
          </p>
        </template>
        <template #cell-ativo="{ item }"><BadgeAtivo :ativo="item.ativo" /></template>
        <template #actions="{ item }">
          <AcoesLinha
            :ativo="item.ativo"
            :desabilitado="store.carregando"
            @editar="abrirEdicao(item as IRegraExame)"
            @alternar="alternarAtivo(item as IRegraExame)"
            @remover="pedirRemocao(item.id as number, `${item.codigoExame} · ${item.nomeExame}`)"
          />
        </template>
      </DataTable>

      <!-- Matriz de Incompatibilidades -->
      <DataTable v-else :headers="colunasIncompatibilidades" :items="incompatibilidadesOrdenadas">
        <template #cell-par="{ item }">
          <p class="font-medium text-gray-800">
            {{ item.codigoExameOrigem }} × {{ item.codigoExameConflitante }}
          </p>
          <p class="text-xs text-gray-500">{{ nomeExame(item.codigoExameOrigem) }} × {{ nomeExame(item.codigoExameConflitante) }}</p>
        </template>
        <template #cell-tipo="{ item }">
          <span class="rounded bg-orange-100 px-2 py-0.5 text-xs font-semibold text-orange-800 whitespace-nowrap">
            {{ ROTULO_CONFLITO[item.tipoConflito as TipoConflito] }}
          </span>
          <p v-if="item.tipoConflito === 'INTERVALO_MINIMO'" class="mt-1 text-xs text-gray-500">
            Mínimo de {{ item.intervaloMinimoDias }} dia(s)
          </p>
        </template>
        <template #cell-motivo="{ item }">
          <span class="text-xs text-gray-600">{{ item.motivo }}</span>
        </template>
        <template #cell-ativo="{ item }"><BadgeAtivo :ativo="item.ativo" /></template>
        <template #actions="{ item }">
          <AcoesLinha
            :ativo="item.ativo"
            :desabilitado="store.carregando"
            @editar="abrirEdicao(item as IIncompatibilidadeExame)"
            @alternar="alternarAtivo(item as IIncompatibilidadeExame)"
            @remover="pedirRemocao(item.id as number, `${item.codigoExameOrigem} × ${item.codigoExameConflitante}`)"
          />
        </template>
      </DataTable>
    </Card>

    <!-- Modal de criação/edição -->
    <Modal :show="modalFormulario" largura="max-w-2xl" @close="fecharFormulario">
      <template #header>{{ tituloFormulario }}</template>

      <form id="formRegra" class="grid grid-cols-1 gap-x-4 md:grid-cols-2" @submit.prevent="salvar">
        <template v-if="abaAtiva === 'prioridades'">
          <div class="form-group">
            <label for="fCodigo" class="form-label">Código *</label>
            <input id="fCodigo" v-model="formPrioridade.codigo" class="form-control" :disabled="emEdicao"
              required minlength="2" maxlength="100" placeholder="Ex.: ONCOLOGIA">
          </div>
          <div class="form-group">
            <label for="fNome" class="form-label">Nome *</label>
            <input id="fNome" v-model="formPrioridade.nome" class="form-control" required minlength="3" maxlength="255">
          </div>
          <div class="form-group">
            <label for="fTipo" class="form-label">Tipo de critério *</label>
            <select id="fTipo" v-model="formPrioridade.tipoCriterio" class="form-control">
              <option v-for="(rotulo, valor) in ROTULO_CRITERIO" :key="valor" :value="valor">{{ rotulo }}</option>
            </select>
          </div>
          <div class="form-group">
            <label for="fPeso" class="form-label">Peso (0 a 1000) *</label>
            <input id="fPeso" v-model.number="formPrioridade.peso" type="number" min="0" max="1000" class="form-control" required>
          </div>
          <div class="form-group md:col-span-2">
            <label for="fMatch" class="form-label">Termos de correspondência</label>
            <input id="fMatch" v-model="formPrioridade.valorMatch" class="form-control" maxlength="255"
              placeholder="Ex.: ONCOLOGIA,HEMATOLOGIA (unidade ou exame que ativa o peso)">
          </div>
          <div class="form-group md:col-span-2">
            <label for="fDescricao" class="form-label">Descrição</label>
            <textarea id="fDescricao" v-model="formPrioridade.descricao" rows="2" class="form-control" maxlength="2000"></textarea>
          </div>
          <label class="inline-flex items-center gap-2 text-sm text-paper-text">
            <input v-model="formPrioridade.ativo" type="checkbox" class="h-4 w-4"> Ativo
          </label>
        </template>

        <template v-else-if="abaAtiva === 'exames'">
          <div class="form-group">
            <label for="fCodExame" class="form-label">Sigla do exame (AGHU) *</label>
            <input id="fCodExame" v-model="formExame.codigoExame" class="form-control" :disabled="emEdicao"
              required maxlength="50" placeholder="Ex.: ESPIRO">
          </div>
          <div class="form-group">
            <label for="fNomeExame" class="form-label">Nome do exame *</label>
            <input id="fNomeExame" v-model="formExame.nomeExame" class="form-control" required minlength="2" maxlength="255">
          </div>
          <div class="form-group">
            <label for="fUnidade" class="form-label">Unidade executora</label>
            <input id="fUnidade" v-model="formExame.unidadeExecutora" class="form-control" maxlength="255">
          </div>
          <div class="form-group">
            <label for="fAntecedencia" class="form-label">Antecedência mínima (dias)</label>
            <input id="fAntecedencia" v-model.number="formExame.antecedenciaMinimaDias" type="number" min="0" max="365" class="form-control">
          </div>
          <div class="form-group">
            <label for="fJanela" class="form-label">Janela máx. até o retorno (horas)</label>
            <input id="fJanela" v-model="formExame.janelaRetornoMaxHoras" type="number" min="0" max="8760" class="form-control"
              placeholder="Vazio = sem janela (ex.: INR 72, espirometria 240)">
          </div>
          <div class="form-group">
            <label for="fIdade" class="form-label">Idade mínima para alerta</label>
            <input id="fIdade" v-model="formExame.idadeMinimaAlerta" type="number" min="0" max="150" class="form-control"
              placeholder="Vazio = sem alerta (ex.: mamografia 40)">
          </div>
          <div class="form-group md:col-span-2">
            <label for="fOrientacoes" class="form-label">Orientações de preparo</label>
            <textarea id="fOrientacoes" v-model="formExame.orientacoesPreparo" rows="3" class="form-control" maxlength="5000"></textarea>
          </div>
          <div class="md:col-span-2 flex flex-wrap gap-x-6 gap-y-2">
            <label class="inline-flex items-center gap-2 text-sm text-paper-text">
              <input v-model="formExame.exigeJejum" type="checkbox" class="h-4 w-4"> Exige jejum
            </label>
            <label class="inline-flex items-center gap-2 text-sm text-paper-text">
              <input v-model="formExame.priorizarManhaDiabetico" type="checkbox" class="h-4 w-4"> Priorizar manhã para diabético
            </label>
            <label class="inline-flex items-center gap-2 text-sm text-paper-text">
              <input v-model="formExame.ativo" type="checkbox" class="h-4 w-4"> Ativo
            </label>
          </div>
        </template>

        <template v-else>
          <div class="form-group">
            <label for="fOrigem" class="form-label">Exame de origem *</label>
            <input id="fOrigem" v-model="formIncompatibilidade.codigoExameOrigem" class="form-control" list="siglasExames"
              required maxlength="50" placeholder="Ex.: COLONO">
          </div>
          <div class="form-group">
            <label for="fConflitante" class="form-label">Exame conflitante *</label>
            <input id="fConflitante" v-model="formIncompatibilidade.codigoExameConflitante" class="form-control" list="siglasExames"
              required maxlength="50" placeholder="Ex.: HEMO">
          </div>
          <datalist id="siglasExames">
            <option v-for="exame in store.regrasExames" :key="exame.id" :value="exame.codigoExame">{{ exame.nomeExame }}</option>
          </datalist>
          <div class="form-group">
            <label for="fTipoConflito" class="form-label">Tipo de conflito *</label>
            <select id="fTipoConflito" v-model="formIncompatibilidade.tipoConflito" class="form-control">
              <option v-for="(rotulo, valor) in ROTULO_CONFLITO" :key="valor" :value="valor">{{ rotulo }}</option>
            </select>
          </div>
          <div class="form-group">
            <label for="fIntervalo" class="form-label">Intervalo mínimo (dias)</label>
            <input id="fIntervalo" v-model.number="formIncompatibilidade.intervaloMinimoDias" type="number" min="0" max="365"
              class="form-control" :required="formIncompatibilidade.tipoConflito === 'INTERVALO_MINIMO'">
          </div>
          <div class="form-group md:col-span-2">
            <label for="fMotivo" class="form-label">Motivo clínico *</label>
            <textarea id="fMotivo" v-model="formIncompatibilidade.motivo" rows="2" class="form-control"
              required minlength="3" maxlength="2000"></textarea>
          </div>
          <label class="inline-flex items-center gap-2 text-sm text-paper-text">
            <input v-model="formIncompatibilidade.ativo" type="checkbox" class="h-4 w-4"> Ativo
          </label>
        </template>
      </form>

      <p v-if="erroFormulario" class="mt-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">{{ erroFormulario }}</p>

      <template #footer>
        <Button type="button" variant="default" @click="fecharFormulario">Cancelar</Button>
        <Button type="submit" form="formRegra" variant="primary" :loading="store.carregando">Salvar</Button>
      </template>
    </Modal>

    <!-- Confirmação de exclusão lógica -->
    <Modal :show="alvoRemocao !== null" @close="alvoRemocao = null">
      <template #header>Remover regra</template>
      <p>
        Remover <strong>{{ alvoRemocao?.rotulo }}</strong>? A regra deixa de valer para a fila e sai da lista
        (exclusão lógica, o histórico continua na auditoria). Para suspender temporariamente, use “Pausar”.
      </p>
      <template #footer>
        <Button type="button" variant="default" @click="alvoRemocao = null">Cancelar</Button>
        <Button type="button" variant="danger" :loading="store.carregando" @click="confirmarRemocao">Remover</Button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref, type PropType } from 'vue';
import { useToast } from 'vue-toastification';
import { ArrowPathIcon, PauseIcon, PencilSquareIcon, PlayIcon, PlusIcon, TrashIcon } from '@heroicons/vue/24/outline';
import Card from '../components/Card.vue';
import Button from '../components/Button.vue';
import DataTable from '../components/DataTable.vue';
import Modal from '../components/Modal.vue';
import { useRegrasStore, type RecursoRegras } from '../stores/regras';
import type { IIncompatibilidadeExame, IRegraExame, IRegraPrioridade } from '../types/exames';

type TipoCriterio = IRegraPrioridade['tipoCriterio'];
type TipoConflito = IIncompatibilidadeExame['tipoConflito'];
type Regra = IRegraPrioridade | IRegraExame | IIncompatibilidadeExame;
type CorpoRegra = Omit<IRegraPrioridade, 'id'> | Omit<IRegraExame, 'id'> | Omit<IIncompatibilidadeExame, 'id'>;

const ABAS: Array<{ valor: RecursoRegras; rotulo: string }> = [
  { valor: 'prioridades', rotulo: 'Pesos de Prioridade' },
  { valor: 'exames', rotulo: 'Regras por Exame' },
  { valor: 'incompatibilidades', rotulo: 'Matriz de Incompatibilidades' },
];
const DESCRICAO_ABA: Record<RecursoRegras, string> = {
  prioridades: 'Critérios que somam pontos ao score da fila. Maior peso = atendido antes.',
  exames: 'Preparo, jejum, antecedência e janela até o retorno médico de cada exame (sigla do AGHU).',
  incompatibilidades: 'Pares de exames que não podem ser marcados no mesmo dia ou exigem intervalo mínimo.',
};
const ROTULO_NOVO: Record<RecursoRegras, string> = {
  prioridades: 'Novo critério',
  exames: 'Nova regra de exame',
  incompatibilidades: 'Nova incompatibilidade',
};
const ROTULO_CRITERIO: Record<TipoCriterio, string> = {
  CLINICA: 'Clínica / unidade',
  GRUPO_CLINICO: 'Grupo clínico',
  VULNERAVEL: 'Vulnerável',
  AFINIDADE_EXAME: 'Afinidade de exame',
  RETORNO_PROXIMO: 'Retorno próximo',
};
const ROTULO_CONFLITO: Record<TipoConflito, string> = {
  MESMO_DIA: 'Não marcar no mesmo dia',
  PREPARO: 'Conflito de preparo',
  INTERVALO_MINIMO: 'Intervalo mínimo',
};

const colunasPrioridades = [
  { text: 'Critério', value: 'criterio' },
  { text: 'Tipo', value: 'tipo' },
  { text: 'Correspondência', value: 'valorMatch' },
  { text: 'Peso', value: 'peso' },
  { text: 'Situação', value: 'ativo' },
];
const colunasExames = [
  { text: 'Exame', value: 'exame' },
  { text: 'Prazos', value: 'prazos' },
  { text: 'Preparo e alertas', value: 'preparo' },
  { text: 'Situação', value: 'ativo' },
];
const colunasIncompatibilidades = [
  { text: 'Par de exames', value: 'par' },
  { text: 'Conflito', value: 'tipo' },
  { text: 'Motivo', value: 'motivo' },
  { text: 'Situação', value: 'ativo' },
];

/** Badge de situação ativa/pausada. */
const BadgeAtivo = defineComponent({
  props: { ativo: { type: Boolean, required: true } },
  setup(props) {
    return () =>
      h(
        'span',
        {
          class: [
            'rounded-full px-2 py-0.5 text-xs font-semibold whitespace-nowrap',
            props.ativo ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-600',
          ],
        },
        props.ativo ? 'Ativa' : 'Pausada',
      );
  },
});

/** Botões de editar, pausar/ativar e remover de cada linha. */
const AcoesLinha = defineComponent({
  props: {
    ativo: { type: Boolean, required: true },
    desabilitado: { type: Boolean as PropType<boolean>, default: false },
  },
  emits: ['editar', 'alternar', 'remover'],
  setup(props, { emit }) {
    const botao = (variant: string, titulo: string, icone: object, evento: 'editar' | 'alternar' | 'remover') =>
      h(
        Button,
        { variant, title: titulo, 'aria-label': titulo, disabled: props.desabilitado, onClick: () => emit(evento) },
        () => h(icone, { class: 'h-4 w-4' }),
      );
    return () =>
      h('div', { class: 'flex gap-2' }, [
        botao('info', 'Editar', PencilSquareIcon, 'editar'),
        botao(props.ativo ? 'warning' : 'success', props.ativo ? 'Pausar' : 'Ativar', props.ativo ? PauseIcon : PlayIcon, 'alternar'),
        botao('danger', 'Remover', TrashIcon, 'remover'),
      ]);
  },
});

const store = useRegrasStore();
const toast = useToast();

const abaAtiva = ref<RecursoRegras>('prioridades');
const modalFormulario = ref(false);
const idEmEdicao = ref<number | null>(null);
const erroFormulario = ref('');
const alvoRemocao = ref<{ id: number; rotulo: string; recurso: RecursoRegras } | null>(null);

const emEdicao = computed(() => idEmEdicao.value !== null);

const prioridadesOrdenadas = computed(() =>
  [...store.prioridades].sort((a, b) => b.peso - a.peso || a.codigo.localeCompare(b.codigo)),
);
const examesOrdenados = computed(() =>
  [...store.regrasExames].sort((a, b) => a.codigoExame.localeCompare(b.codigoExame)),
);
const incompatibilidadesOrdenadas = computed(() =>
  [...store.incompatibilidades].sort(
    (a, b) =>
      a.codigoExameOrigem.localeCompare(b.codigoExameOrigem) ||
      a.codigoExameConflitante.localeCompare(b.codigoExameConflitante),
  ),
);
const contagem = computed<Record<RecursoRegras, number>>(() => ({
  prioridades: store.prioridades.length,
  exames: store.regrasExames.length,
  incompatibilidades: store.incompatibilidades.length,
}));

const tituloFormulario = computed(() => {
  const acao = emEdicao.value ? 'Editar' : 'Nova';
  const nomes: Record<RecursoRegras, string> = {
    prioridades: 'regra de prioridade',
    exames: 'regra de exame',
    incompatibilidades: 'incompatibilidade',
  };
  return `${acao} ${nomes[abaAtiva.value]}`;
});

// ── Formulários (campos numéricos opcionais ficam como texto até o envio) ──
function prioridadeVazia() {
  return { codigo: '', nome: '', tipoCriterio: 'CLINICA' as TipoCriterio, valorMatch: '', peso: 0, ativo: true, descricao: '' };
}
function exameVazio() {
  return {
    codigoExame: '',
    nomeExame: '',
    unidadeExecutora: '',
    antecedenciaMinimaDias: 0,
    janelaRetornoMaxHoras: '' as string | number,
    exigeJejum: false,
    priorizarManhaDiabetico: false,
    idadeMinimaAlerta: '' as string | number,
    orientacoesPreparo: '',
    ativo: true,
  };
}
function incompatibilidadeVazia() {
  return {
    codigoExameOrigem: '',
    codigoExameConflitante: '',
    tipoConflito: 'MESMO_DIA' as TipoConflito,
    intervaloMinimoDias: 0,
    motivo: '',
    ativo: true,
  };
}

const formPrioridade = reactive(prioridadeVazia());
const formExame = reactive(exameVazio());
const formIncompatibilidade = reactive(incompatibilidadeVazia());

function inteiroOuNulo(valor: string | number | null): number | null {
  if (valor === null || valor === '') return null;
  const numero = Number(valor);
  return Number.isFinite(numero) ? Math.round(numero) : null;
}
function textoOuNulo(valor: string | null | undefined): string | null {
  const limpo = (valor ?? '').trim();
  return limpo || null;
}

function abrirNovo(): void {
  idEmEdicao.value = null;
  erroFormulario.value = '';
  if (abaAtiva.value === 'prioridades') Object.assign(formPrioridade, prioridadeVazia());
  else if (abaAtiva.value === 'exames') Object.assign(formExame, exameVazio());
  else Object.assign(formIncompatibilidade, incompatibilidadeVazia());
  modalFormulario.value = true;
}

function abrirEdicao(regra: Regra): void {
  idEmEdicao.value = regra.id;
  erroFormulario.value = '';
  if (abaAtiva.value === 'prioridades') {
    const r = regra as IRegraPrioridade;
    Object.assign(formPrioridade, { ...prioridadeVazia(), ...r, valorMatch: r.valorMatch ?? '', descricao: r.descricao ?? '' });
  } else if (abaAtiva.value === 'exames') {
    const r = regra as IRegraExame;
    Object.assign(formExame, {
      ...exameVazio(),
      ...r,
      unidadeExecutora: r.unidadeExecutora ?? '',
      janelaRetornoMaxHoras: r.janelaRetornoMaxHoras ?? '',
      idadeMinimaAlerta: r.idadeMinimaAlerta ?? '',
      orientacoesPreparo: r.orientacoesPreparo ?? '',
    });
  } else {
    Object.assign(formIncompatibilidade, { ...incompatibilidadeVazia(), ...(regra as IIncompatibilidadeExame) });
  }
  modalFormulario.value = true;
}

function fecharFormulario(): void {
  modalFormulario.value = false;
  idEmEdicao.value = null;
  erroFormulario.value = '';
}

/** Monta o corpo do POST/PUT no formato camelCase de src/schemas/regras.py. */
function corpoFormulario(): CorpoRegra {
  if (abaAtiva.value === 'prioridades') {
    return {
      codigo: formPrioridade.codigo.trim().toUpperCase(),
      nome: formPrioridade.nome.trim(),
      tipoCriterio: formPrioridade.tipoCriterio,
      valorMatch: formPrioridade.valorMatch.trim().toUpperCase(),
      peso: Math.round(Number(formPrioridade.peso) || 0),
      ativo: formPrioridade.ativo,
      descricao: textoOuNulo(formPrioridade.descricao),
    };
  }
  if (abaAtiva.value === 'exames') {
    return {
      codigoExame: formExame.codigoExame.trim().toUpperCase(),
      nomeExame: formExame.nomeExame.trim(),
      unidadeExecutora: textoOuNulo(formExame.unidadeExecutora),
      antecedenciaMinimaDias: Math.round(Number(formExame.antecedenciaMinimaDias) || 0),
      janelaRetornoMaxHoras: inteiroOuNulo(formExame.janelaRetornoMaxHoras),
      exigeJejum: formExame.exigeJejum,
      priorizarManhaDiabetico: formExame.priorizarManhaDiabetico,
      idadeMinimaAlerta: inteiroOuNulo(formExame.idadeMinimaAlerta),
      orientacoesPreparo: textoOuNulo(formExame.orientacoesPreparo),
      ativo: formExame.ativo,
    };
  }
  return {
    codigoExameOrigem: formIncompatibilidade.codigoExameOrigem.trim().toUpperCase(),
    codigoExameConflitante: formIncompatibilidade.codigoExameConflitante.trim().toUpperCase(),
    tipoConflito: formIncompatibilidade.tipoConflito,
    intervaloMinimoDias: Math.round(Number(formIncompatibilidade.intervaloMinimoDias) || 0),
    motivo: formIncompatibilidade.motivo.trim(),
    ativo: formIncompatibilidade.ativo,
  };
}

/** Validações rápidas na tela; o backend (Pydantic) valida de novo. */
function validarFormulario(): string {
  if (abaAtiva.value === 'prioridades') {
    const peso = Number(formPrioridade.peso);
    if (!Number.isFinite(peso) || peso < 0 || peso > 1000) return 'O peso deve estar entre 0 e 1000.';
  }
  if (abaAtiva.value === 'incompatibilidades') {
    const origem = formIncompatibilidade.codigoExameOrigem.trim().toUpperCase();
    const conflitante = formIncompatibilidade.codigoExameConflitante.trim().toUpperCase();
    if (origem && origem === conflitante) return 'O exame conflitante deve ser diferente do exame de origem.';
    if (formIncompatibilidade.tipoConflito === 'INTERVALO_MINIMO' && Number(formIncompatibilidade.intervaloMinimoDias) < 1) {
      return 'Conflitos de intervalo mínimo precisam de pelo menos 1 dia.';
    }
  }
  return '';
}

async function salvar(): Promise<void> {
  erroFormulario.value = validarFormulario();
  if (erroFormulario.value) return;

  const recurso = abaAtiva.value;
  const corpo = corpoFormulario();
  const resultado = idEmEdicao.value !== null
    ? await store.atualizar(recurso, idEmEdicao.value, corpo as never)
    : await store.criar(recurso, corpo as never);

  if (!resultado) {
    erroFormulario.value = store.erro ?? 'Não foi possível salvar a regra.';
    return;
  }
  toast.success(emEdicao.value ? 'Regra atualizada.' : 'Regra criada.');
  fecharFormulario();
}

async function alternarAtivo(regra: Regra): Promise<void> {
  const { id, ...dados } = regra;
  const resultado = await store.atualizar(abaAtiva.value, id, { ...dados, ativo: !regra.ativo } as never);
  if (resultado) {
    toast.info(regra.ativo ? 'Regra pausada.' : 'Regra ativada.');
  } else {
    toast.error(store.erro ?? 'Não foi possível alterar a situação da regra.');
  }
}

function pedirRemocao(id: number, rotulo: string): void {
  alvoRemocao.value = { id, rotulo, recurso: abaAtiva.value };
}

async function confirmarRemocao(): Promise<void> {
  const alvo = alvoRemocao.value;
  if (!alvo) return;
  const ok = await store.remover(alvo.recurso, alvo.id);
  alvoRemocao.value = null;
  if (ok) toast.warning(`Regra "${alvo.rotulo}" removida.`);
  else toast.error(store.erro ?? 'Não foi possível remover a regra.');
}

function nomeExame(codigo: string): string {
  return store.regrasExames.find((exame) => exame.codigoExame === codigo)?.nomeExame ?? 'sem regra cadastrada';
}

function formatarJanela(horas: number | null): string {
  if (horas === null) return 'sem janela';
  if (horas % 24 === 0 && horas >= 48) return `até ${horas / 24} dias`;
  return `até ${horas} h`;
}

async function carregarTudo(): Promise<void> {
  await Promise.all([store.carregar('prioridades'), store.carregar('exames'), store.carregar('incompatibilidades')]);
  if (store.erro) toast.error(store.erro);
}

onMounted(carregarTudo);
</script>
