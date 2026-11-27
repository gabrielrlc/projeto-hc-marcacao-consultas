import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
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

function clonarLista<T>(lista: T[]): T[] {
  return lista.map((item) => ({ ...item }));
}

function aguardarCurto(ms = 120): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function normalizarCodigo(codigo: string): string {
  return codigo.trim().toUpperCase();
}

export const useRegrasStore = defineStore('regras', () => {
  const prioridades = ref<IRegraPrioridade[]>(clonarLista(MOCK_REGRAS_PRIORIDADE));
  const exames = ref<IRegraExame[]>(clonarLista(MOCK_REGRAS_EXAMES));
  const incompatibilidades = ref<IIncompatibilidadeExame[]>(
    clonarLista(MOCK_INCOMPATIBILIDADES),
  );
  const carregando = ref(false);

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

  async function salvarPrioridade(
    payload: Omit<IRegraPrioridade, 'id'> & { id?: number },
  ): Promise<IRegraPrioridade> {
    carregando.value = true;
    try {
      await aguardarCurto();
      const codigoNormalizado = normalizarCodigo(payload.codigo);
      const pesoSeguro = Math.max(0, Math.min(1000, Math.round(Number(payload.peso) || 0)));
      const agora = new Date().toISOString();

      const duplicada = prioridades.value.find(
        (r) => !r.deletedAt && normalizarCodigo(r.codigo) === codigoNormalizado && r.id !== payload.id,
      );
      if (duplicada) {
        throw new Error(`Já existe uma regra de prioridade com o código "${codigoNormalizado}".`);
      }

      if (payload.id !== undefined) {
        const idx = prioridades.value.findIndex((r) => r.id === payload.id);
        if (idx === -1) {
          throw new Error('Regra de prioridade não encontrada.');
        }
        const atualizada: IRegraPrioridade = {
          ...prioridades.value[idx],
          ...payload,
          id: payload.id,
          codigo: codigoNormalizado,
          nome: payload.nome.trim(),
          valorMatch: payload.valorMatch.trim().toUpperCase(),
          peso: pesoSeguro,
          descricao: payload.descricao?.trim() || null,
          updatedAt: agora,
          deletedAt: null,
        };
        prioridades.value[idx] = atualizada;
        return { ...atualizada };
      }

      const proximoId =
        prioridades.value.reduce((max, r) => Math.max(max, r.id), 0) + 1;
      const nova: IRegraPrioridade = {
        ...payload,
        id: proximoId,
        codigo: codigoNormalizado,
        nome: payload.nome.trim(),
        valorMatch: payload.valorMatch.trim().toUpperCase(),
        peso: pesoSeguro,
        descricao: payload.descricao?.trim() || null,
        updatedAt: agora,
        deletedAt: null,
      };
      prioridades.value.push(nova);
      return { ...nova };
    } finally {
      carregando.value = false;
    }
  }

  async function alternarAtivoPrioridade(id: number): Promise<void> {
    carregando.value = true;
    try {
      await aguardarCurto(90);
      const alvo = prioridades.value.find((r) => r.id === id && !r.deletedAt);
      if (alvo) {
        alvo.ativo = !alvo.ativo;
        alvo.updatedAt = new Date().toISOString();
      }
    } finally {
      carregando.value = false;
    }
  }

  async function removerPrioridade(id: number): Promise<void> {
    carregando.value = true;
    try {
      await aguardarCurto();
      const alvo = prioridades.value.find((r) => r.id === id && !r.deletedAt);
      if (alvo) {
        const agora = new Date().toISOString();
        alvo.ativo = false;
        alvo.deletedAt = agora;
        alvo.updatedAt = agora;
      }
    } finally {
      carregando.value = false;
    }
  }

  async function salvarRegraExame(
    payload: Omit<IRegraExame, 'id'> & { id?: number },
  ): Promise<IRegraExame> {
    carregando.value = true;
    try {
      await aguardarCurto();
      const codigoNormalizado = normalizarCodigo(payload.codigoExame);
      const agora = new Date().toISOString();

      const duplicada = exames.value.find(
        (r) =>
          !r.deletedAt &&
          normalizarCodigo(r.codigoExame) === codigoNormalizado &&
          r.id !== payload.id,
      );
      if (duplicada) {
        throw new Error(`Já existe regra cadastrada para o exame "${codigoNormalizado}".`);
      }

      const antecedencia = Math.max(0, Math.round(Number(payload.antecedenciaMinimaDias) || 0));
      const janela =
        payload.janelaRetornoMaxHoras !== null && payload.janelaRetornoMaxHoras !== undefined
          ? Math.max(1, Math.round(Number(payload.janelaRetornoMaxHoras)))
          : null;
      const idadeMinima =
        payload.idadeMinimaAlerta !== null && payload.idadeMinimaAlerta !== undefined
          ? Math.max(1, Math.round(Number(payload.idadeMinimaAlerta)))
          : null;

      if (payload.id !== undefined) {
        const idx = exames.value.findIndex((r) => r.id === payload.id);
        if (idx === -1) {
          throw new Error('Regra de exame não encontrada.');
        }
        const atualizada: IRegraExame = {
          ...exames.value[idx],
          ...payload,
          id: payload.id,
          codigoExame: codigoNormalizado,
          nomeExame: payload.nomeExame.trim(),
          unidadeExecutora: payload.unidadeExecutora?.trim() || null,
          antecedenciaMinimaDias: antecedencia,
          janelaRetornoMaxHoras: janela,
          idadeMinimaAlerta: idadeMinima,
          orientacoesPreparo: payload.orientacoesPreparo?.trim() || null,
          updatedAt: agora,
          deletedAt: null,
        };
        exames.value[idx] = atualizada;
        return { ...atualizada };
      }

      const proximoId = exames.value.reduce((max, r) => Math.max(max, r.id), 0) + 1;
      const nova: IRegraExame = {
        ...payload,
        id: proximoId,
        codigoExame: codigoNormalizado,
        nomeExame: payload.nomeExame.trim(),
        unidadeExecutora: payload.unidadeExecutora?.trim() || null,
        antecedenciaMinimaDias: antecedencia,
        janelaRetornoMaxHoras: janela,
        idadeMinimaAlerta: idadeMinima,
        orientacoesPreparo: payload.orientacoesPreparo?.trim() || null,
        updatedAt: agora,
        deletedAt: null,
      };
      exames.value.push(nova);
      return { ...nova };
    } finally {
      carregando.value = false;
    }
  }

  async function alternarAtivoRegraExame(id: number): Promise<void> {
    carregando.value = true;
    try {
      await aguardarCurto(90);
      const alvo = exames.value.find((r) => r.id === id && !r.deletedAt);
      if (alvo) {
        alvo.ativo = !alvo.ativo;
        alvo.updatedAt = new Date().toISOString();
      }
    } finally {
      carregando.value = false;
    }
  }

  async function removerRegraExame(id: number): Promise<void> {
    carregando.value = true;
    try {
      await aguardarCurto();
      const alvo = exames.value.find((r) => r.id === id && !r.deletedAt);
      if (alvo) {
        const agora = new Date().toISOString();
        alvo.ativo = false;
        alvo.deletedAt = agora;
        alvo.updatedAt = agora;
      }
    } finally {
      carregando.value = false;
    }
  }

  async function salvarIncompatibilidade(
    payload: Omit<IIncompatibilidadeExame, 'id'> & { id?: number },
  ): Promise<IIncompatibilidadeExame> {
    carregando.value = true;
    try {
      await aguardarCurto();
      const origem = normalizarCodigo(payload.codigoExameOrigem);
      const conflitante = normalizarCodigo(payload.codigoExameConflitante);

      if (!origem || !conflitante) {
        throw new Error('Informe ambos os códigos de exame para o par incompatível.');
      }
      if (origem === conflitante) {
        throw new Error('Um exame não pode ser configurado como incompatível consigo mesmo.');
      }

      const duplicada = incompatibilidades.value.find((item) => {
        if (item.deletedAt || item.id === payload.id) {
          return false;
        }
        const o = normalizarCodigo(item.codigoExameOrigem);
        const c = normalizarCodigo(item.codigoExameConflitante);
        return (o === origem && c === conflitante) || (o === conflitante && c === origem);
      });
      if (duplicada) {
        throw new Error(`O par ${origem} × ${conflitante} já está cadastrado na matriz.`);
      }

      const intervalo = Math.max(0, Math.round(Number(payload.intervaloMinimoDias) || 0));

      if (payload.id !== undefined) {
        const idx = incompatibilidades.value.findIndex((item) => item.id === payload.id);
        if (idx === -1) {
          throw new Error('Incompatibilidade não encontrada.');
        }
        const atualizada: IIncompatibilidadeExame = {
          ...incompatibilidades.value[idx],
          ...payload,
          id: payload.id,
          codigoExameOrigem: origem,
          codigoExameConflitante: conflitante,
          intervaloMinimoDias: intervalo,
          motivo: payload.motivo.trim(),
          deletedAt: null,
        };
        incompatibilidades.value[idx] = atualizada;
        return { ...atualizada };
      }

      const proximoId =
        incompatibilidades.value.reduce((max, item) => Math.max(max, item.id), 0) + 1;
      const nova: IIncompatibilidadeExame = {
        ...payload,
        id: proximoId,
        codigoExameOrigem: origem,
        codigoExameConflitante: conflitante,
        intervaloMinimoDias: intervalo,
        motivo: payload.motivo.trim(),
        deletedAt: null,
      };
      incompatibilidades.value.push(nova);
      return { ...nova };
    } finally {
      carregando.value = false;
    }
  }

  async function alternarAtivoIncompatibilidade(id: number): Promise<void> {
    carregando.value = true;
    try {
      await aguardarCurto(90);
      const alvo = incompatibilidades.value.find((item) => item.id === id && !item.deletedAt);
      if (alvo) {
        alvo.ativo = !alvo.ativo;
      }
    } finally {
      carregando.value = false;
    }
  }

  async function removerIncompatibilidade(id: number): Promise<void> {
    carregando.value = true;
    try {
      await aguardarCurto();
      const alvo = incompatibilidades.value.find((item) => item.id === id && !item.deletedAt);
      if (alvo) {
        alvo.ativo = false;
        alvo.deletedAt = new Date().toISOString();
      }
    } finally {
      carregando.value = false;
    }
  }

  async function restaurarPadraoSeed(): Promise<void> {
    carregando.value = true;
    try {
      await aguardarCurto(150);
      prioridades.value = clonarLista(MOCK_REGRAS_PRIORIDADE);
      exames.value = clonarLista(MOCK_REGRAS_EXAMES);
      incompatibilidades.value = clonarLista(MOCK_INCOMPATIBILIDADES);
    } finally {
      carregando.value = false;
    }
  }

  return {
    prioridades,
    exames,
    incompatibilidades,
    carregando,
    prioridadesAtivas,
    examesAtivos,
    incompatibilidadesAtivas,
    salvarPrioridade,
    alternarAtivoPrioridade,
    removerPrioridade,
    salvarRegraExame,
    alternarAtivoRegraExame,
    removerRegraExame,
    salvarIncompatibilidade,
    alternarAtivoIncompatibilidade,
    removerIncompatibilidade,
    restaurarPadraoSeed,
  };
});
