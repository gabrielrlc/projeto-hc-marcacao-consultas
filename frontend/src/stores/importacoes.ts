import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../services/api';
import { executar } from '../services/requisicao';
import type { IImportacaoResumo, IRelatorioImportacao } from '../types/exames';

/**
 * Importação do Google Forms (/api/importacoes) — consumida pela TASK-014.
 * Upload da planilha (CSV/XLSX) para higienização Forms × AGHU, histórico de
 * lotes e relatório de cada importação. A planilha não é alterada nem armazenada.
 */
export const useImportacoesStore = defineStore('importacoes', () => {
  const historico = ref<IImportacaoResumo[]>([]);
  const carregandoHistorico = ref(false);
  const erroHistorico = ref<string | null>(null);

  const relatorio = ref<IRelatorioImportacao | null>(null);
  const carregandoRelatorio = ref(false);
  const erroRelatorio = ref<string | null>(null);

  const enviando = ref(false);
  const erroEnvio = ref<string | null>(null);

  /** Lista os lotes importados, do mais recente para o mais antigo. */
  async function carregarHistorico(limite = 50) {
    return executar(carregandoHistorico, erroHistorico, async () => {
      const { data } = await api.get<IImportacaoResumo[]>('/api/importacoes', { params: { limite } });
      historico.value = data;
      return data;
    });
  }

  /** Carrega o relatório completo (contadores e linhas) de um lote. */
  async function carregarRelatorio(id: number) {
    return executar(carregandoRelatorio, erroRelatorio, async () => {
      const { data } = await api.get<IRelatorioImportacao>(`/api/importacoes/${id}`);
      relatorio.value = data;
      return data;
    });
  }

  /** Envia a planilha do Forms; o relatório devolvido vira o lote em exibição. */
  async function enviarPlanilha(arquivo: File) {
    return executar(enviando, erroEnvio, async () => {
      const formulario = new FormData();
      formulario.append('arquivo', arquivo);
      // Content-Type undefined: o navegador define multipart/form-data com o boundary.
      const { data } = await api.post<IRelatorioImportacao>('/api/importacoes/forms', formulario, {
        headers: { 'Content-Type': undefined },
      });
      relatorio.value = data;
      historico.value = [data.importacao, ...historico.value.filter((imp) => imp.id !== data.importacao.id)];
      return data;
    });
  }

  return {
    historico,
    carregandoHistorico,
    erroHistorico,
    relatorio,
    carregandoRelatorio,
    erroRelatorio,
    enviando,
    erroEnvio,
    carregarHistorico,
    carregarRelatorio,
    enviarPlanilha,
  };
});
