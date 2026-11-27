import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import api from '../services/api';
import {
  MOCK_INCOMPATIBILIDADES,
  MOCK_REGRAS_EXAMES,
  MOCK_REGRAS_PRIORIDADE,
} from '../mocks/examesMock';
import type {
  IIncompatibilidadeExame,
  IRegraExame,
  IRegraPrioridade,
} from '../types/exames';

/**
 * Store das Regras Configuráveis (TASK-015).
 *
 * Consome a API `/api/regras` (TASK-006): Pesos de Prioridade, Regras por Exame
 * e Matriz de Incompatibilidades. Até a primeira carga do backend, mantém os
 * dados de exemplo para que as telas ainda mockadas (fila/dashboard) continuem
 * calculando scores; `carregarRegras()` substitui tudo pelos dados reais.
 */

const URL_BASE = '/api/regras';

function clonarLista<T>(lista: T[]): T[] {
  return lista.map((item) => ({ ...item }));
}

function normalizarCodigo(codigo: string): string {
  return codigo.trim().toUpperCase();
}

function textoOpcional(valor: string | null | undefined): string | null {
  const limpo = (valor ?? '').trim();
  return limpo ? limpo : null;
}

function inteiroOpcional(valor: number | string | null | undefined): number | null {
  if (valor === null || valor === undefined || valor === '') {
    return null;
  }
  const numero = Math.round(Number(valor));
  return Number.isNaN(numero) ? null : numero;
}

/** Extrai a mensagem `detail` do backend (string ou lista de erros do Pydantic). */
export function extrairMensagemErro(err: unknown, padrao: string): string {
  const resposta = (err as { response?: { status?: number; data?: { detail?: unknown } } })?.response;
  const detail = resposta?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => String((item as { msg?: string })?.msg ?? item).replace(/^Value error, /, ''))
      .join(' ');
  }
  if (resposta?.status === 403) {
    return 'Seu perfil não tem permissão para esta operação.';
  }
  if (err instanceof Error && !resposta) {
    return err.message || padrao;
  }
  return padrao;
}

function corpoPrioridade(regra: Omit<IRegraPrioridade, 'id'>) {
  return {
    nome: regra.nome.trim(),
    tipoCriterio: regra.tipoCriterio,
    valorMatch: (regra.valorMatch ?? '').trim().toUpperCase(),
    peso: Math.max(0, Math.min(1000, Math.round(Number(regra.peso) || 0))),
    ativo: regra.ativo,
    descricao: textoOpcional(regra.descricao),
  };
}

function corpoRegraExame(regra: Omit<IRegraExame, 'id'>) {
  return {
    nomeExame: regra.nomeExame.trim(),
    unidadeExecutora: textoOpcional(regra.unidadeExecutora),
    antecedenciaMinimaDias: Math.max(0, Math.round(Number(regra.antecedenciaMinimaDias) || 0)),
    janelaRetornoMaxHoras: inteiroOpcional(regra.janelaRetornoMaxHoras),
    exigeJejum: regra.exigeJejum,
    priorizarManhaDiabetico: regra.priorizarManhaDiabetico,
    idadeMinimaAlerta: inteiroOpcional(regra.idadeMinimaAlerta),
    orientacoesPreparo: textoOpcional(regra.orientacoesPreparo),
    ativo: regra.ativo,
  };
}

function corpoIncompatibilidade(item: Omit<IIncompatibilidadeExame, 'id'>) {
  return {
    codigoExameOrigem: normalizarCodigo(item.codigoExameOrigem),
    codigoExameConflitante: normalizarCodigo(item.codigoExameConflitante),
    tipoConflito: item.tipoConflito,
    intervaloMinimoDias: Math.max(0, Math.round(Number(item.intervaloMinimoDias) || 0)),
    motivo: item.motivo.trim(),
    ativo: item.ativo,
  };
}

function prioridadeDaApi(dado: IRegraPrioridade): IRegraPrioridade {
  return { ...dado, valorMatch: dado.valorMatch ?? '', deletedAt: null };
}

export const useRegrasStore = defineStore('regras', () => {
  const prioridades = ref<IRegraPrioridade[]>(clonarLista(MOCK_REGRAS_PRIORIDADE));
  const exames = ref<IRegraExame[]>(clonarLista(MOCK_REGRAS_EXAMES));
  const incompatibilidades = ref<IIncompatibilidadeExame[]>(
    clonarLista(MOCK_INCOMPATIBILIDADES),
  );
  const carregando = ref(false);
  const carregadoDoServidor = ref(false);
  const erroCarga = ref<string | null>(null);

  const prioridadesAtivas = computed<IRegraPrioridade[]>(() =>
    prioridades.value
      .filter((regra) => !regra.deletedAt)
      .slice()
      .sort((a, b) => b.peso - a.peso || a.codigo.localeCompare(b.codigo)),
  );

  const examesAtivos = computed<IRegraExame[]>(() =>
    exames.value
      .filter((regra) => !regra.deletedAt)
      .slice()
      .sort((a, b) => a.codigoExame.localeCompare(b.codigoExame)),
  );

  const incompatibilidadesAtivas = computed<IIncompatibilidadeExame[]>(() =>
    incompatibilidades.value
      .filter((item) => !item.deletedAt)
      .slice()
      .sort(
        (a, b) =>
          a.codigoExameOrigem.localeCompare(b.codigoExameOrigem) ||
          a.codigoExameConflitante.localeCompare(b.codigoExameConflitante),
      ),
  );

  async function comCarregamento<T>(acao: () => Promise<T>): Promise<T> {
    carregando.value = true;
    try {
      return await acao();
    } finally {
      carregando.value = false;
    }
  }

  /** Busca as três tabelas de regras no backend (ativas e pausadas; excluídas não vêm). */
  async function carregarRegras(): Promise<void> {
    await comCarregamento(async () => {
      try {
        const [resPrioridades, resExames, resIncompatibilidades] = await Promise.all([
          api.get<IRegraPrioridade[]>(`${URL_BASE}/prioridades`),
          api.get<IRegraExame[]>(`${URL_BASE}/exames`),
          api.get<IIncompatibilidadeExame[]>(`${URL_BASE}/incompatibilidades`),
        ]);
        prioridades.value = resPrioridades.data.map(prioridadeDaApi);
        exames.value = resExames.data.map((r) => ({ ...r, deletedAt: null }));
        incompatibilidades.value = resIncompatibilidades.data.map((i) => ({ ...i, deletedAt: null }));
        carregadoDoServidor.value = true;
        erroCarga.value = null;
      } catch (err) {
        erroCarga.value = extrairMensagemErro(err, 'Não foi possível carregar as regras do servidor.');
        throw new Error(erroCarga.value);
      }
    });
  }

  function substituirNaLista<T extends { id: number }>(lista: T[], item: T): void {
    const idx = lista.findIndex((atual) => atual.id === item.id);
    if (idx === -1) {
      lista.push(item);
    } else {
      lista[idx] = item;
    }
  }

  // ── Pesos de Prioridade ──────────────────────────────────────────────────
  async function salvarPrioridade(
    payload: Omit<IRegraPrioridade, 'id'> & { id?: number },
  ): Promise<IRegraPrioridade> {
    return comCarregamento(async () => {
      try {
        const corpo = corpoPrioridade(payload);
        const { data } =
          payload.id !== undefined
            ? await api.put<IRegraPrioridade>(`${URL_BASE}/prioridades/${payload.id}`, corpo)
            : await api.post<IRegraPrioridade>(`${URL_BASE}/prioridades`, {
                ...corpo,
                codigo: normalizarCodigo(payload.codigo),
              });
        const salva = prioridadeDaApi(data);
        substituirNaLista(prioridades.value, salva);
        return { ...salva };
      } catch (err) {
        throw new Error(extrairMensagemErro(err, 'Erro ao salvar critério de prioridade.'));
      }
    });
  }

  async function alternarAtivoPrioridade(id: number): Promise<void> {
    const alvo = prioridades.value.find((r) => r.id === id && !r.deletedAt);
    if (!alvo) {
      return;
    }
    await salvarPrioridade({ ...alvo, ativo: !alvo.ativo });
  }

  async function removerPrioridade(id: number): Promise<void> {
    await comCarregamento(async () => {
      try {
        await api.delete(`${URL_BASE}/prioridades/${id}`);
        prioridades.value = prioridades.value.filter((r) => r.id !== id);
      } catch (err) {
        throw new Error(extrairMensagemErro(err, 'Erro ao remover critério de prioridade.'));
      }
    });
  }

  // ── Regras por Exame ─────────────────────────────────────────────────────
  async function salvarRegraExame(
    payload: Omit<IRegraExame, 'id'> & { id?: number },
  ): Promise<IRegraExame> {
    return comCarregamento(async () => {
      try {
        const corpo = corpoRegraExame(payload);
        const { data } =
          payload.id !== undefined
            ? await api.put<IRegraExame>(`${URL_BASE}/exames/${payload.id}`, corpo)
            : await api.post<IRegraExame>(`${URL_BASE}/exames`, {
                ...corpo,
                codigoExame: normalizarCodigo(payload.codigoExame),
              });
        const salva = { ...data, deletedAt: null };
        substituirNaLista(exames.value, salva);
        return { ...salva };
      } catch (err) {
        throw new Error(extrairMensagemErro(err, 'Erro ao salvar regra do exame.'));
      }
    });
  }

  async function alternarAtivoRegraExame(id: number): Promise<void> {
    const alvo = exames.value.find((r) => r.id === id && !r.deletedAt);
    if (!alvo) {
      return;
    }
    await salvarRegraExame({ ...alvo, ativo: !alvo.ativo });
  }

  async function removerRegraExame(id: number): Promise<void> {
    await comCarregamento(async () => {
      try {
        await api.delete(`${URL_BASE}/exames/${id}`);
        exames.value = exames.value.filter((r) => r.id !== id);
      } catch (err) {
        throw new Error(extrairMensagemErro(err, 'Erro ao remover regra do exame.'));
      }
    });
  }

  // ── Matriz de Incompatibilidades ─────────────────────────────────────────
  async function salvarIncompatibilidade(
    payload: Omit<IIncompatibilidadeExame, 'id'> & { id?: number },
  ): Promise<IIncompatibilidadeExame> {
    const origem = normalizarCodigo(payload.codigoExameOrigem);
    const conflitante = normalizarCodigo(payload.codigoExameConflitante);
    if (!origem || !conflitante) {
      throw new Error('Informe ambos os códigos de exame para o par incompatível.');
    }
    if (origem === conflitante) {
      throw new Error('Um exame não pode ser configurado como incompatível consigo mesmo.');
    }

    return comCarregamento(async () => {
      try {
        const corpo = corpoIncompatibilidade(payload);
        const { data } =
          payload.id !== undefined
            ? await api.put<IIncompatibilidadeExame>(
                `${URL_BASE}/incompatibilidades/${payload.id}`,
                corpo,
              )
            : await api.post<IIncompatibilidadeExame>(`${URL_BASE}/incompatibilidades`, corpo);
        const salva = { ...data, deletedAt: null };
        substituirNaLista(incompatibilidades.value, salva);
        return { ...salva };
      } catch (err) {
        throw new Error(extrairMensagemErro(err, 'Erro ao salvar incompatibilidade.'));
      }
    });
  }

  async function alternarAtivoIncompatibilidade(id: number): Promise<void> {
    const alvo = incompatibilidades.value.find((item) => item.id === id && !item.deletedAt);
    if (!alvo) {
      return;
    }
    await salvarIncompatibilidade({ ...alvo, ativo: !alvo.ativo });
  }

  async function removerIncompatibilidade(id: number): Promise<void> {
    await comCarregamento(async () => {
      try {
        await api.delete(`${URL_BASE}/incompatibilidades/${id}`);
        incompatibilidades.value = incompatibilidades.value.filter((item) => item.id !== id);
      } catch (err) {
        throw new Error(extrairMensagemErro(err, 'Erro ao remover incompatibilidade.'));
      }
    });
  }

  return {
    prioridades,
    exames,
    incompatibilidades,
    carregando,
    carregadoDoServidor,
    erroCarga,
    prioridadesAtivas,
    examesAtivos,
    incompatibilidadesAtivas,
    carregarRegras,
    salvarPrioridade,
    alternarAtivoPrioridade,
    removerPrioridade,
    salvarRegraExame,
    alternarAtivoRegraExame,
    removerRegraExame,
    salvarIncompatibilidade,
    alternarAtivoIncompatibilidade,
    removerIncompatibilidade,
  };
});
