import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import type {
  IKpiDashboard,
  PeriodoDashboard,
  RegiaoGeografica,
} from '../types/exames';
import { useExamesStore } from './exames';

const MS_DIA = 24 * 60 * 60 * 1000;

const LABELS_REGIAO: Record<RegiaoGeografica, string> = {
  CAPITAL: 'Capital (Recife)',
  RMR: 'Região Metropolitana (RMR)',
  INTERIOR: 'Interior de PE',
  NAO_INFORMADO: 'Não Informado',
};

const ORDEM_REGIOES: RegiaoGeografica[] = ['CAPITAL', 'RMR', 'INTERIOR', 'NAO_INFORMADO'];

export const useDashboardStore = defineStore('dashboard', () => {
  const examesStore = useExamesStore();

  const periodoDias = ref<PeriodoDashboard>('TODOS');
  const unidadeFiltro = ref<string>('');
  const atualizando = ref<boolean>(false);
  const ultimaAtualizacao = ref<string>(new Date().toISOString());

  const kpis = computed<IKpiDashboard>(() => {
    const agoraMs = Date.now();
    const limiteMs =
      periodoDias.value === 'TODOS' ? null : agoraMs - periodoDias.value * MS_DIA;
    const unidadeAlvo = unidadeFiltro.value.trim().toUpperCase();

    const itensRecorte = examesStore.itensEnriquecidos.filter((item) => {
      if (unidadeAlvo) {
        const un = (item.unidadeSolicitante ?? '').toUpperCase();
        if (!un.includes(unidadeAlvo)) {
          return false;
        }
      }
      if (limiteMs !== null && item.dataSolicitacao) {
        const ts = new Date(item.dataSolicitacao).getTime();
        if (!Number.isNaN(ts) && ts < limiteMs) {
          return false;
        }
      }
      return true;
    });

    const ativosNaFila = itensRecorte.filter(
      (item) =>
        item.statusOperacional === 'NA_FILA' ||
        item.statusOperacional === 'AGUARDANDO_CONFIRMACAO_24H',
    );

    const totalNaFila = itensRecorte.filter(
      (item) => item.statusOperacional === 'NA_FILA',
    ).length;

    const aguardando24h = itensRecorte.filter(
      (item) => item.statusOperacional === 'AGUARDANDO_CONFIRMACAO_24H',
    ).length;

    const prazo24hVencidos = itensRecorte.filter((item) =>
      item.alertas.some((alerta) => alerta.tipo === 'PRAZO_24H_VENCIDO'),
    ).length;

    const confirmadosAgendados = itensRecorte.filter(
      (item) => item.statusOperacional === 'CONFIRMADO_AGENDADO_AGHU',
    ).length;

    const semResposta24h = itensRecorte.filter(
      (item) => item.statusOperacional === 'SEM_RESPOSTA_24H',
    ).length;

    const totalDecididos24h = confirmadosAgendados + semResposta24h;
    const taxaConfirmacao24h =
      totalDecididos24h > 0
        ? Math.round((confirmadosAgendados / totalDecididos24h) * 100)
        : 0;

    // Contadores de higienização combinando histórico de importações (quando no período) e estado atual
    const importacoesRecorte = examesStore.historicoImportacoes.filter((imp) => {
      if (limiteMs === null) {
        return true;
      }
      const ts = new Date(imp.importadoEm).getTime();
      return Number.isNaN(ts) || ts >= limiteMs;
    });

    const dupHistorico = importacoesRecorte.reduce((acc, imp) => acc + imp.totalDuplicadas, 0);
    const divHistorico = importacoesRecorte.reduce((acc, imp) => acc + imp.totalDivergencias, 0);
    const naoEncHistorico = importacoesRecorte.reduce(
      (acc, imp) => acc + imp.totalNaoEncontradas,
      0,
    );

    const dupFila = itensRecorte.filter((i) => i.statusHigienizacao === 'DUPLICADA').length;
    const divFila = itensRecorte.filter((i) => i.statusHigienizacao === 'DIVERGENCIA_EXAME').length;
    const naoEncFila = itensRecorte.filter((i) => i.statusHigienizacao === 'NAO_ENCONTRADA').length;

    const duplicidadesBarradas = unidadeAlvo ? dupFila : Math.max(dupHistorico, dupFila);
    const divergenciasDetectadas = unidadeAlvo ? divFila : Math.max(divHistorico, divFila);
    const naoEncontradasAghu = unidadeAlvo ? naoEncFila : Math.max(naoEncHistorico, naoEncFila);

    // Tempo médio de espera (dias) dos itens ativos na fila
    const esperasDias = ativosNaFila
      .map((item) => {
        if (!item.dataSolicitacao) {
          return null;
        }
        const ts = new Date(item.dataSolicitacao).getTime();
        if (Number.isNaN(ts)) {
          return null;
        }
        return Math.max(0, (agoraMs - ts) / MS_DIA);
      })
      .filter((v): v is number => v !== null);

    const tempoMedioEsperaDias =
      esperasDias.length > 0
        ? Number((esperasDias.reduce((acc, v) => acc + v, 0) / esperasDias.length).toFixed(1))
        : 0;

    const totalTfdFila = ativosNaFila.filter((item) => item.utilizaTfd).length;

    // Volume na fila ativa por exame
    const mapaExames = new Map<string, { codigoExame: string; exame: string; quantidade: number }>();
    for (const item of ativosNaFila) {
      const codigo = item.codigoExame ?? 'PENDENTE';
      const nome = item.nomeExame ?? 'Aguardando Vínculo AGHU';
      const atual = mapaExames.get(codigo);
      if (atual) {
        atual.quantidade += 1;
      } else {
        mapaExames.set(codigo, { codigoExame: codigo, exame: nome, quantidade: 1 });
      }
    }
    const filaPorExame = Array.from(mapaExames.values()).sort(
      (a, b) => b.quantidade - a.quantidade || a.codigoExame.localeCompare(b.codigoExame),
    );

    // Volume na fila ativa por unidade solicitante
    const mapaUnidades = new Map<string, number>();
    for (const item of ativosNaFila) {
      const unidade = item.unidadeSolicitante ?? 'Sem Unidade Vinculada';
      mapaUnidades.set(unidade, (mapaUnidades.get(unidade) ?? 0) + 1);
    }
    const filaPorUnidade = Array.from(mapaUnidades.entries())
      .map(([unidade, quantidade]) => ({ unidade, quantidade }))
      .sort((a, b) => b.quantidade - a.quantidade || a.unidade.localeCompare(b.unidade));

    // Distribuição geográfica da fila ativa
    const mapaRegiao = new Map<RegiaoGeografica, number>();
    for (const reg of ORDEM_REGIOES) {
      mapaRegiao.set(reg, 0);
    }
    for (const item of ativosNaFila) {
      mapaRegiao.set(item.regiaoGeografica, (mapaRegiao.get(item.regiaoGeografica) ?? 0) + 1);
    }
    const totalAtivos = ativosNaFila.length;
    const filaPorRegiao = ORDEM_REGIOES.map((regiao) => {
      const quantidade = mapaRegiao.get(regiao) ?? 0;
      const percentual = totalAtivos > 0 ? Math.round((quantidade / totalAtivos) * 100) : 0;
      return {
        regiao,
        label: LABELS_REGIAO[regiao],
        quantidade,
        percentual,
      };
    });

    return {
      totalNaFila,
      aguardando24h,
      prazo24hVencidos,
      confirmadosAgendados,
      semResposta24h,
      taxaConfirmacao24h,
      duplicidadesBarradas,
      divergenciasDetectadas,
      naoEncontradasAghu,
      tempoMedioEsperaDias,
      totalTfdFila,
      filaPorExame,
      filaPorUnidade,
      filaPorRegiao,
    };
  });

  function definirPeriodo(dias: PeriodoDashboard): void {
    periodoDias.value = dias;
    ultimaAtualizacao.value = new Date().toISOString();
  }

  function definirUnidade(unidade: string): void {
    unidadeFiltro.value = unidade;
    ultimaAtualizacao.value = new Date().toISOString();
  }

  async function atualizarIndicadores(): Promise<void> {
    atualizando.value = true;
    try {
      await new Promise<void>((resolve) => {
        setTimeout(resolve, 180);
      });
      ultimaAtualizacao.value = new Date().toISOString();
    } finally {
      atualizando.value = false;
    }
  }

  return {
    periodoDias,
    unidadeFiltro,
    atualizando,
    ultimaAtualizacao,
    kpis,
    definirPeriodo,
    definirUnidade,
    atualizarIndicadores,
  };
});
