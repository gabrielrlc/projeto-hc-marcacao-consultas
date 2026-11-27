import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import {
  MOCK_HISTORICO_IMPORTACOES,
  MOCK_ITENS_FILA_BASE,
  MOCK_LOTE_UPLOAD_DEMO,
  MOCK_SOLICITACOES_AGHU,
} from '../mocks/examesMock';
import type {
  IAlertaExame,
  IAtualizarStatusPayload,
  IFiltrosFila,
  IImportacaoForms,
  IIncompatibilidadeExame,
  IItemFila,
  ILinhaHigienizadaPreview,
  IOutroExameProntuario,
  IRegraExame,
  IRegraPrioridade,
  ISolicitacaoAghu,
  IVincularSolicitacaoPayload,
  RegiaoGeografica,
  SeveridadeAlerta,
  StatusHigienizacao,
} from '../types/exames';
import { useRegrasStore } from './regras';

const MS_HORA = 60 * 60 * 1000;
const MS_DIA = 24 * MS_HORA;

const TIPOS_GRUPO_CLINICO = new Set<string>(['CLINICA', 'GRUPO_CLINICO', 'VULNERAVEL']);
const PALAVRAS_GENERICAS_AFINIDADE = new Set<string>([
  'CLINICA',
  'CLINICO',
  'CLINICAS',
  'EXAME',
  'EXAMES',
  'COMPLETO',
  'COMPLETA',
  'TOTAL',
  'AMBULATORIO',
  'AMBULATORIAL',
  'SERVICO',
  'UNIDADE',
  'SETOR',
  'DIGITAL',
  'BILATERAL',
  'NECESSARIO',
  'PARA',
  'COM',
  'SEM',
]);

const SEVERIDADE_ORDEM: Record<SeveridadeAlerta, number> = {
  ALTA: 0,
  MEDIA: 1,
  INFO: 2,
};

const MUNICIPIOS_RMR = new Set<string>([
  'OLINDA',
  'JABOATAO DOS GUARARAPES',
  'PAULISTA',
  'CAMARAGIBE',
  'ABREU E LIMA',
  'IGARASSU',
  'SAO LOURENCO DA MATA',
  'CABO DE SANTO AGOSTINHO',
  'IPOJUCA',
  'MORENO',
  'ITAPISSUMA',
  'ITAMARACA',
  'ARACOIABA',
]);

function criarFiltrosPadrao(): IFiltrosFila {
  return {
    busca: '',
    codigoExame: '',
    unidade: '',
    statusOperacional: 'TODOS',
    statusHigienizacao: 'TODOS',
    regiao: 'TODAS',
    municipio: '',
    apenasTfd: false,
    apenas24hVencidos: false,
    apenasComAlertas: false,
  };
}

function normalizarTexto(texto: string | null | undefined): string {
  if (!texto) {
    return '';
  }
  return texto
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
    .replace(/\s+/g, ' ')
    .trim();
}

function termosRegra(valorMatch: string | null | undefined): string[] {
  return (valorMatch ?? '')
    .split(',')
    .map((parte) => normalizarTexto(parte))
    .filter(Boolean);
}

function extrairPalavrasSignificativas(texto: string | null | undefined): Set<string> {
  const tokens = normalizarTexto(texto)
    .split(/[^A-Z0-9]+/)
    .filter((token) => token.length >= 4 && !PALAVRAS_GENERICAS_AFINIDADE.has(token));
  return new Set(tokens);
}

function parseDataLocal(valor: string | null | undefined): Date | null {
  if (!valor) {
    return null;
  }
  const limpo = valor.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(limpo)) {
    const [ano, mes, dia] = limpo.split('-').map(Number);
    return new Date(ano, mes - 1, dia, 0, 0, 0, 0);
  }
  const parsed = new Date(limpo);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function inicioDoDia(data: Date): Date {
  return new Date(data.getFullYear(), data.getMonth(), data.getDate());
}

function diferencaDiasCalendario(alvo: Date, base: Date): number {
  const diffMs = inicioDoDia(alvo).getTime() - inicioDoDia(base).getTime();
  return Math.round(diffMs / MS_DIA);
}

function calcularIdade(nascimento: Date, referencia: Date): number {
  let idade = referencia.getFullYear() - nascimento.getFullYear();
  const mesAtual = referencia.getMonth();
  const mesNasc = nascimento.getMonth();
  if (mesAtual < mesNasc || (mesAtual === mesNasc && referencia.getDate() < nascimento.getDate())) {
    idade -= 1;
  }
  return idade;
}

function formatarDataBr(data: Date): string {
  const dia = String(data.getDate()).padStart(2, '0');
  const mes = String(data.getMonth() + 1).padStart(2, '0');
  const ano = data.getFullYear();
  return `${dia}/${mes}/${ano}`;
}

function formatarDataHoraBr(data: Date): string {
  const hh = String(data.getHours()).padStart(2, '0');
  const mm = String(data.getMinutes()).padStart(2, '0');
  return `${formatarDataBr(data)} ${hh}:${mm}`;
}

function formatarDias(n: number): string {
  return n === 1 ? '1 dia' : `${n} dias`;
}

function inferirRegiao(municipio: string | null | undefined): RegiaoGeografica {
  const norm = normalizarTexto(municipio);
  if (!norm) {
    return 'NAO_INFORMADO';
  }
  if (norm === 'RECIFE') {
    return 'CAPITAL';
  }
  if (MUNICIPIOS_RMR.has(norm)) {
    return 'RMR';
  }
  return 'INTERIOR';
}

function aguardarCurto(ms = 140): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function ehRegraRotina(regra: IRegraPrioridade): boolean {
  return regra.tipoCriterio === 'GRUPO_CLINICO' && termosRegra(regra.valorMatch).includes('ROTINA');
}

function regraGrupoCasa(regra: IRegraPrioridade, item: IItemFila, hoje: Date): boolean {
  const termos = termosRegra(regra.valorMatch);
  if (termos.length === 0) {
    return false;
  }
  const textoItem = [
    normalizarTexto(item.especialidadeSolicitante),
    normalizarTexto(item.unidadeSolicitante),
    normalizarTexto(item.grupoPrioritarioManual),
  ].join(' | ');

  const nascimento = parseDataLocal(item.dataNascimento);
  const idade = nascimento ? calcularIdade(nascimento, hoje) : null;

  for (const termo of termos) {
    if (textoItem.includes(termo)) {
      return true;
    }
    if (termo === 'HEMODIALISE' && item.flagHemodialise) {
      return true;
    }
    if (termo === 'IDOSO' && idade !== null && idade >= 60) {
      return true;
    }
    if (termo === 'CRIANCA' && idade !== null && idade <= 12) {
      return true;
    }
  }
  return false;
}

function bonusRetornoCasa(regra: IRegraPrioridade, item: IItemFila, hoje: Date): boolean {
  const match = /^\s*<=\s*(\d+)\s*$/.exec(regra.valorMatch ?? '');
  if (!match) {
    return false;
  }
  const retorno = parseDataLocal(item.dataRetornoMedico);
  if (!retorno) {
    return false;
  }
  const dias = diferencaDiasCalendario(retorno, hoje);
  return dias >= 0 && dias <= Number(match[1]);
}

function bonusAfinidadeCasa(item: IItemFila, mapaRegrasExames: Map<string, IRegraExame>): boolean {
  const codigo = normalizarTexto(item.codigoExame);
  if (!codigo) {
    return false;
  }
  const regraExame = mapaRegrasExames.get(codigo);
  if (!regraExame) {
    return false;
  }
  const palavrasSolicitante = new Set<string>([
    ...extrairPalavrasSignificativas(item.especialidadeSolicitante),
    ...extrairPalavrasSignificativas(item.unidadeSolicitante),
  ]);
  const palavrasExame = new Set<string>([
    ...extrairPalavrasSignificativas(regraExame.unidadeExecutora),
    ...extrairPalavrasSignificativas(regraExame.nomeExame),
  ]);
  for (const palavra of palavrasSolicitante) {
    if (palavrasExame.has(palavra)) {
      return true;
    }
  }
  return false;
}

function calcularPrioridadeItem(
  item: IItemFila,
  regrasPrioridade: IRegraPrioridade[],
  mapaRegrasExames: Map<string, IRegraExame>,
  hoje: Date,
): { scorePrioridade: number; motivosPrioridade: string[] } {
  const ativas = regrasPrioridade.filter((r) => r.ativo && !r.deletedAt && r.peso > 0);

  const grupos = ativas.filter(
    (r) =>
      TIPOS_GRUPO_CLINICO.has(r.tipoCriterio) &&
      !ehRegraRotina(r) &&
      regraGrupoCasa(r, item, hoje),
  );

  let principal: IRegraPrioridade | null = null;
  if (grupos.length > 0) {
    grupos.sort((a, b) => b.peso - a.peso || a.codigo.localeCompare(b.codigo));
    principal = grupos[0];
  } else {
    const rotinas = ativas
      .filter((r) => ehRegraRotina(r))
      .sort((a, b) => a.codigo.localeCompare(b.codigo));
    principal = rotinas[0] ?? null;
  }

  const bonus: IRegraPrioridade[] = [];
  for (const regra of ativas) {
    if (regra.tipoCriterio === 'RETORNO_PROXIMO' && bonusRetornoCasa(regra, item, hoje)) {
      bonus.push(regra);
    } else if (
      regra.tipoCriterio === 'AFINIDADE_EXAME' &&
      bonusAfinidadeCasa(item, mapaRegrasExames)
    ) {
      bonus.push(regra);
    }
  }
  bonus.sort((a, b) => b.peso - a.peso || a.nome.localeCompare(b.nome));

  const aplicadas = principal ? [principal, ...bonus] : bonus;
  const scorePrioridade = aplicadas.reduce((acc, r) => acc + r.peso, 0);
  const motivosPrioridade = aplicadas.map((r) => `${r.nome} +${r.peso}`);

  return { scorePrioridade, motivosPrioridade };
}

function resolverNomeExame(
  codigo: string | null | undefined,
  nomeInformado: string | null | undefined,
  mapaRegrasExames: Map<string, IRegraExame>,
): string {
  const regra = mapaRegrasExames.get(normalizarTexto(codigo));
  if (regra?.nomeExame) {
    return regra.nomeExame;
  }
  return nomeInformado || codigo || 'exame';
}

function detectarAlertasItem(
  item: IItemFila,
  outrosExames: IOutroExameProntuario[],
  mapaRegrasExames: Map<string, IRegraExame>,
  incompatibilidades: IIncompatibilidadeExame[],
  agora: Date,
): IAlertaExame[] {
  const alertas: IAlertaExame[] = [];
  const outrosValidos = outrosExames.filter((o) => o.statusOperacional !== 'CANCELADO');
  const codigoItem = normalizarTexto(item.codigoExame);

  // 1. Incompatibilidades
  if (codigoItem) {
    const incsAtivas = incompatibilidades.filter((inc) => inc.ativo && !inc.deletedAt);
    const nomeItem = resolverNomeExame(item.codigoExame, item.nomeExame, mapaRegrasExames);
    const dataItem = parseDataLocal(item.dataAgendadaAghu);

    for (const outro of outrosValidos) {
      const codigoOutro = normalizarTexto(outro.codigoExame);
      if (!codigoOutro || codigoOutro === codigoItem) {
        continue;
      }
      for (const inc of incsAtivas) {
        const o = normalizarTexto(inc.codigoExameOrigem);
        const c = normalizarTexto(inc.codigoExameConflitante);
        const casaPar =
          (o === codigoItem && c === codigoOutro) || (o === codigoOutro && c === codigoItem);
        if (!casaPar) {
          continue;
        }
        const nomeOutro = resolverNomeExame(outro.codigoExame, outro.nomeExame, mapaRegrasExames);
        const intervalo = Math.max(0, inc.intervaloMinimoDias);
        const limite = inc.tipoConflito === 'MESMO_DIA' ? Math.max(intervalo, 1) : intervalo;
        const prefixo = `${nomeItem} × ${nomeOutro}: ${inc.motivo}`;
        const dataOutro = parseDataLocal(outro.dataAgendada);

        if (dataItem && dataOutro) {
          const distancia = Math.abs(diferencaDiasCalendario(dataItem, dataOutro));
          if (distancia < limite) {
            alertas.push({
              tipo: 'INCOMPATIBILIDADE',
              severidade: 'ALTA',
              mensagem: `${prefixo} Agendados com ${formatarDias(distancia)} de intervalo (mínimo ${formatarDias(limite)}).`,
            });
          }
        } else {
          const orientacao =
            inc.tipoConflito === 'MESMO_DIA'
              ? 'Não agendar no mesmo dia.'
              : `Respeitar intervalo mínimo de ${formatarDias(intervalo)}.`;
          alertas.push({
            tipo: 'INCOMPATIBILIDADE',
            severidade: 'MEDIA',
            mensagem: `${prefixo} ${orientacao}`,
          });
        }
      }
    }
  }

  // 2. Duplicidade
  if (item.statusHigienizacao === 'DUPLICADA') {
    alertas.push({
      tipo: 'DUPLICIDADE',
      severidade: 'ALTA',
      mensagem: 'Solicitação marcada como duplicada na higienização.',
    });
  } else if (codigoItem && item.prontuario) {
    const outroIgual = outrosValidos.find(
      (o) => o.origem === 'FILA' && normalizarTexto(o.codigoExame) === codigoItem,
    );
    if (outroIgual) {
      alertas.push({
        tipo: 'DUPLICIDADE',
        severidade: 'ALTA',
        mensagem: `Prontuário já possui outro item ativo na fila para o mesmo exame (solicitação ${outroIgual.codigoSolicitacao ?? '—'}).`,
      });
    }
  }

  // 3. Prazo 24h vencido
  const prazo = parseDataLocal(item.prazoConfirmacaoEm);
  if (item.statusOperacional === 'AGUARDANDO_CONFIRMACAO_24H' && prazo && prazo.getTime() < agora.getTime()) {
    alertas.push({
      tipo: 'PRAZO_24H_VENCIDO',
      severidade: 'ALTA',
      mensagem: `Prazo de confirmação venceu em ${formatarDataHoraBr(prazo)}; liberar a vaga para o próximo da fila.`,
    });
  }

  // 4-7. Regras específicas do exame
  const regra = codigoItem ? mapaRegrasExames.get(codigoItem) : undefined;
  if (regra && regra.ativo && !regra.deletedAt) {
    const nome = regra.nomeExame || item.codigoExame || 'Exame';
    const agendada = parseDataLocal(item.dataAgendadaAghu);

    // 4. Janela de retorno
    const retorno = parseDataLocal(item.dataRetornoMedico);
    if (regra.janelaRetornoMaxHoras !== null && retorno) {
      const janela = regra.janelaRetornoMaxHoras;
      if (agendada) {
        const horasAntes = (inicioDoDia(retorno).getTime() - agendada.getTime()) / MS_HORA;
        if (horasAntes < 0) {
          alertas.push({
            tipo: 'JANELA_RETORNO',
            severidade: 'ALTA',
            mensagem: `${nome} agendado para depois do retorno médico de ${formatarDataBr(retorno)}.`,
          });
        } else if (horasAntes > janela) {
          alertas.push({
            tipo: 'JANELA_RETORNO',
            severidade: 'ALTA',
            mensagem: `${nome} agendado ${Math.round(horasAntes / 24)} dias antes do retorno de ${formatarDataBr(retorno)}; o máximo é ${janela}h.`,
          });
        }
      } else if (inicioDoDia(retorno).getTime() < inicioDoDia(agora).getTime()) {
        alertas.push({
          tipo: 'JANELA_RETORNO',
          severidade: 'ALTA',
          mensagem: `Retorno médico de ${formatarDataBr(retorno)} já passou sem o exame ${nome} agendado.`,
        });
      } else {
        const inicioJanela = new Date(inicioDoDia(retorno).getTime() - janela * MS_HORA);
        alertas.push({
          tipo: 'JANELA_RETORNO',
          severidade: 'INFO',
          mensagem: `Agendar ${nome} entre ${formatarDataBr(inicioJanela)} e o retorno de ${formatarDataBr(retorno)} (até ${janela}h antes).`,
        });
      }
    }

    // 5. Antecedência mínima de preparo
    if (regra.antecedenciaMinimaDias > 0) {
      if (agendada) {
        const base = parseDataLocal(item.contatoIniciadoEm) ?? agora;
        const dias = diferencaDiasCalendario(agendada, base);
        if (dias < regra.antecedenciaMinimaDias) {
          alertas.push({
            tipo: 'ANTECEDENCIA_PREPARO',
            severidade: 'ALTA',
            mensagem: `${nome} agendado com ${formatarDias(Math.max(dias, 0))} de antecedência; o preparo exige no mínimo ${formatarDias(regra.antecedenciaMinimaDias)}.`,
          });
        }
      } else {
        const orientacoes = regra.orientacoesPreparo ? ` ${regra.orientacoesPreparo}` : '';
        alertas.push({
          tipo: 'ANTECEDENCIA_PREPARO',
          severidade: 'INFO',
          mensagem: `${nome} exige antecedência mínima de ${formatarDias(regra.antecedenciaMinimaDias)} para preparo.${orientacoes}`,
        });
      }
    }

    // 6. Jejum clínico e prioridade matutina diabéticos
    if (regra.exigeJejum) {
      if (item.flagDiabeticoJejum && regra.priorizarManhaDiabetico) {
        alertas.push({
          tipo: 'JEJUM_CLINICO',
          severidade: 'MEDIA',
          mensagem: `Paciente diabético: ${nome} exige jejum; agendar nos primeiros horários da manhã.`,
        });
      } else {
        alertas.push({
          tipo: 'JEJUM_CLINICO',
          severidade: 'INFO',
          mensagem: `${nome} exige jejum.`,
        });
      }
    }

    // 7. Alerta etário (ex.: Mamografia >= 40 anos)
    if (regra.idadeMinimaAlerta !== null) {
      const nascimento = parseDataLocal(item.dataNascimento);
      if (!nascimento) {
        alertas.push({
          tipo: 'IDADE_MAMOGRAFIA',
          severidade: 'INFO',
          mensagem: `Conferir idade do paciente: ${nome} é indicado a partir de ${regra.idadeMinimaAlerta} anos.`,
        });
      } else {
        const idade = calcularIdade(nascimento, agora);
        if (idade < regra.idadeMinimaAlerta) {
          alertas.push({
            tipo: 'IDADE_MAMOGRAFIA',
            severidade: 'MEDIA',
            mensagem: `Paciente com ${idade} anos; ${nome} é indicado a partir de ${regra.idadeMinimaAlerta} anos.`,
          });
        }
      }
    }
  }

  // Deduplicação e ordenação determinística
  const unicos = new Map<string, IAlertaExame>();
  for (const alerta of alertas) {
    const chave = `${alerta.tipo}|${alerta.severidade}|${alerta.mensagem}`;
    if (!unicos.has(chave)) {
      unicos.set(chave, alerta);
    }
  }

  return Array.from(unicos.values()).sort(
    (a, b) =>
      SEVERIDADE_ORDEM[a.severidade] - SEVERIDADE_ORDEM[b.severidade] ||
      a.tipo.localeCompare(b.tipo) ||
      a.mensagem.localeCompare(b.mensagem),
  );
}

function splitLinhaCsv(linha: string, delimitador: string): string[] {
  const resultado: string[] = [];
  let atual = '';
  let dentroAspas = false;

  for (let i = 0; i < linha.length; i += 1) {
    const ch = linha[i];
    if (ch === '"') {
      if (dentroAspas && linha[i + 1] === '"') {
        atual += '"';
        i += 1;
      } else {
        dentroAspas = !dentroAspas;
      }
    } else if (ch === delimitador && !dentroAspas) {
      resultado.push(atual.trim());
      atual = '';
    } else {
      atual += ch;
    }
  }
  resultado.push(atual.trim());
  return resultado;
}

export const useExamesStore = defineStore('exames', () => {
  const regrasStore = useRegrasStore();

  const itensBrutos = ref<IItemFila[]>(MOCK_ITENS_FILA_BASE.map((item) => ({ ...item })));
  const catalogoAghu = ref<ISolicitacaoAghu[]>(MOCK_SOLICITACOES_AGHU.map((item) => ({ ...item })));
  const historicoImportacoes = ref<IImportacaoForms[]>(
    MOCK_HISTORICO_IMPORTACOES.map((imp) => ({
      ...imp,
      linhasPreview: imp.linhasPreview.map((l) => ({ ...l })),
    })),
  );
  const ultimaImportacao = ref<IImportacaoForms | null>(historicoImportacoes.value[0] ?? null);
  const filtros = ref<IFiltrosFila>(criarFiltrosPadrao());
  const carregando = ref(false);
  const buscandoAghu = ref(false);

  const itensEnriquecidos = computed<IItemFila[]>(() => {
    const agora = new Date();
    const mapaRegrasExames = new Map<string, IRegraExame>();
    for (const regra of regrasStore.examesAtivos) {
      if (regra.ativo && !regra.deletedAt) {
        mapaRegrasExames.set(normalizarTexto(regra.codigoExame), regra);
      }
    }

    const enriquecidos = itensBrutos.value.map((item) => {
      const outrosExames: IOutroExameProntuario[] = [];
      const chavesRegistradas = new Set<string>();

      if (item.prontuario) {
        // Outros itens da própria fila local com o mesmo prontuário
        for (const outro of itensBrutos.value) {
          if (outro.id === item.id || outro.prontuario !== item.prontuario) {
            continue;
          }
          if (outro.statusOperacional === 'CANCELADO') {
            continue;
          }
          const chave = `${outro.codigoSolicitacao}|${normalizarTexto(outro.codigoExame)}`;
          chavesRegistradas.add(chave);
          outrosExames.push({
            codigoSolicitacao: outro.codigoSolicitacao,
            codigoExame: outro.codigoExame,
            nomeExame: outro.nomeExame,
            origem: 'FILA',
            dataAgendada: outro.dataAgendadaAghu,
            statusOperacional: outro.statusOperacional,
          });
        }

        // Outras solicitações oficiais no espelho AGHU com o mesmo prontuário
        for (const aghu of catalogoAghu.value) {
          if (aghu.prontuario !== item.prontuario) {
            continue;
          }
          if (
            aghu.codigoSolicitacao === item.codigoSolicitacao &&
            normalizarTexto(aghu.codigoExame) === normalizarTexto(item.codigoExame)
          ) {
            continue;
          }
          const chave = `${aghu.codigoSolicitacao}|${normalizarTexto(aghu.codigoExame)}`;
          if (chavesRegistradas.has(chave)) {
            continue;
          }
          chavesRegistradas.add(chave);
          outrosExames.push({
            codigoSolicitacao: aghu.codigoSolicitacao,
            codigoExame: aghu.codigoExame,
            nomeExame: aghu.nomeExame,
            origem: 'AGHU',
            dataAgendada: null,
            statusOperacional: null,
          });
        }
      }

      const { scorePrioridade, motivosPrioridade } = calcularPrioridadeItem(
        item,
        regrasStore.prioridadesAtivas,
        mapaRegrasExames,
        agora,
      );

      const alertas = detectarAlertasItem(
        item,
        outrosExames,
        mapaRegrasExames,
        regrasStore.incompatibilidadesAtivas,
        agora,
      );

      const regraExame = item.codigoExame
        ? mapaRegrasExames.get(normalizarTexto(item.codigoExame))
        : undefined;

      return {
        ...item,
        scorePrioridade,
        motivosPrioridade,
        alertas,
        orientacoesPreparo: regraExame?.orientacoesPreparo ?? item.orientacoesPreparo ?? null,
        outrosExames,
      };
    });

    // Ordenação determinística: score DESC, dataSolicitacao ASC (nulos por último), id ASC
    return enriquecidos.sort((a, b) => {
      if (b.scorePrioridade !== a.scorePrioridade) {
        return b.scorePrioridade - a.scorePrioridade;
      }
      const dataA = parseDataLocal(a.dataSolicitacao)?.getTime() ?? Number.MAX_SAFE_INTEGER;
      const dataB = parseDataLocal(b.dataSolicitacao)?.getTime() ?? Number.MAX_SAFE_INTEGER;
      if (dataA !== dataB) {
        return dataA - dataB;
      }
      return a.id - b.id;
    });
  });

  const filaFiltrada = computed<IItemFila[]>(() => {
    const f = filtros.value;
    const buscaLimpa = f.busca.trim();
    const buscaNorm = normalizarTexto(buscaLimpa);
    const exameNorm = normalizarTexto(f.codigoExame);
    const unidadeNorm = normalizarTexto(f.unidade);
    const municipioNorm = normalizarTexto(f.municipio);

    return itensEnriquecidos.value.filter((item) => {
      if (exameNorm && normalizarTexto(item.codigoExame) !== exameNorm) {
        return false;
      }
      if (unidadeNorm && !normalizarTexto(item.unidadeSolicitante).includes(unidadeNorm)) {
        return false;
      }
      if (f.statusOperacional !== 'TODOS' && item.statusOperacional !== f.statusOperacional) {
        return false;
      }
      if (f.statusHigienizacao !== 'TODOS' && item.statusHigienizacao !== f.statusHigienizacao) {
        return false;
      }
      if (f.regiao !== 'TODAS' && item.regiaoGeografica !== f.regiao) {
        return false;
      }
      if (municipioNorm && normalizarTexto(item.municipio) !== municipioNorm) {
        return false;
      }
      if (f.apenasTfd && !item.utilizaTfd) {
        return false;
      }
      if (
        f.apenas24hVencidos &&
        !item.alertas.some((alerta) => alerta.tipo === 'PRAZO_24H_VENCIDO')
      ) {
        return false;
      }
      if (f.apenasComAlertas && item.alertas.length === 0) {
        return false;
      }
      if (buscaLimpa) {
        const casaProntuario = (item.prontuario ?? '').includes(buscaLimpa);
        const casaSolicitacao = item.codigoSolicitacao.includes(buscaLimpa);
        const casaNome = normalizarTexto(item.nomePaciente).includes(buscaNorm);
        const casaExame =
          normalizarTexto(item.codigoExame).includes(buscaNorm) ||
          normalizarTexto(item.nomeExame).includes(buscaNorm);
        if (!casaProntuario && !casaSolicitacao && !casaNome && !casaExame) {
          return false;
        }
      }
      return true;
    });
  });

  const examesDisponiveis = computed<Array<{ codigo: string; nome: string }>>(() => {
    const mapa = new Map<string, string>();
    for (const regra of regrasStore.examesAtivos) {
      mapa.set(regra.codigoExame, regra.nomeExame);
    }
    for (const item of itensBrutos.value) {
      if (item.codigoExame && !mapa.has(item.codigoExame)) {
        mapa.set(item.codigoExame, item.nomeExame ?? item.codigoExame);
      }
    }
    return Array.from(mapa.entries())
      .map(([codigo, nome]) => ({ codigo, nome }))
      .sort((a, b) => a.codigo.localeCompare(b.codigo));
  });

  const unidadesDisponiveis = computed<string[]>(() => {
    const set = new Set<string>();
    for (const item of itensBrutos.value) {
      if (item.unidadeSolicitante) {
        set.add(item.unidadeSolicitante);
      }
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  });

  const municipiosDisponiveis = computed<string[]>(() => {
    const set = new Set<string>();
    for (const item of itensBrutos.value) {
      if (item.municipio) {
        set.add(item.municipio);
      }
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  });

  const resumoOperacional = computed(() => {
    const itens = itensEnriquecidos.value;
    const naFila = itens.filter(
      (item) => item.statusOperacional === 'NA_FILA' && item.statusHigienizacao === 'VALIDA',
    ).length;
    const aguardando24h = itens.filter(
      (item) => item.statusOperacional === 'AGUARDANDO_CONFIRMACAO_24H',
    ).length;
    const vencidos24h = itens.filter((item) =>
      item.alertas.some((alerta) => alerta.tipo === 'PRAZO_24H_VENCIDO'),
    ).length;
    const confirmados = itens.filter(
      (item) => item.statusOperacional === 'CONFIRMADO_AGENDADO_AGHU',
    ).length;
    const excecoesHigienizacao = itens.filter(
      (item) =>
        item.statusHigienizacao === 'NAO_ENCONTRADA' ||
        item.statusHigienizacao === 'DIVERGENCIA_EXAME',
    ).length;

    return {
      naFila,
      aguardando24h,
      vencidos24h,
      confirmados,
      excecoesHigienizacao,
    };
  });

  function definirFiltros(parcial: Partial<IFiltrosFila>): void {
    filtros.value = {
      ...filtros.value,
      ...parcial,
    };
  }

  function limparFiltros(): void {
    filtros.value = criarFiltrosPadrao();
  }

  function obterDetalheItem(id: number): IItemFila | undefined {
    return itensEnriquecidos.value.find((item) => item.id === id);
  }

  function selecionarImportacao(id: number): void {
    const encontrada = historicoImportacoes.value.find((imp) => imp.id === id);
    if (encontrada) {
      ultimaImportacao.value = encontrada;
    }
  }

  async function atualizarStatusOperacional(
    id: number,
    payload: IAtualizarStatusPayload,
  ): Promise<IItemFila> {
    carregando.value = true;
    try {
      await aguardarCurto();
      const idx = itensBrutos.value.findIndex((item) => item.id === id);
      if (idx === -1) {
        throw new Error('Item não encontrado na fila.');
      }
      const atual = itensBrutos.value[idx];
      const agora = new Date();

      if (payload.statusOperacional === 'CONFIRMADO_AGENDADO_AGHU' && !payload.dataAgendadaAghu) {
        throw new Error('Informe a data e hora agendadas no AGHU para confirmar o agendamento.');
      }

      const atualizado: IItemFila = {
        ...atual,
        statusOperacional: payload.statusOperacional,
        observacoes:
          payload.observacoes !== undefined ? payload.observacoes : atual.observacoes,
      };

      if (payload.statusOperacional === 'AGUARDANDO_CONFIRMACAO_24H') {
        atualizado.contatoIniciadoEm = agora.toISOString();
        atualizado.prazoConfirmacaoEm = new Date(agora.getTime() + 24 * MS_HORA).toISOString();
      } else if (payload.statusOperacional === 'CONFIRMADO_AGENDADO_AGHU') {
        atualizado.dataAgendadaAghu = payload.dataAgendadaAghu ?? atual.dataAgendadaAghu;
        atualizado.preparoOrientado =
          payload.preparoOrientado !== undefined ? payload.preparoOrientado : true;
      } else if (
        payload.statusOperacional === 'SEM_RESPOSTA_24H' ||
        payload.statusOperacional === 'CANCELADO'
      ) {
        atualizado.dataAgendadaAghu = null;
      } else if (payload.statusOperacional === 'NA_FILA') {
        atualizado.contatoIniciadoEm = null;
        atualizado.prazoConfirmacaoEm = null;
      }

      itensBrutos.value[idx] = atualizado;
      const enriquecido = obterDetalheItem(id);
      if (!enriquecido) {
        throw new Error('Falha ao atualizar item da fila.');
      }
      return enriquecido;
    } finally {
      carregando.value = false;
    }
  }

  async function buscarNoAghu(params: {
    prontuario?: string;
    codigoSolicitacao?: string;
    nome?: string;
  }): Promise<ISolicitacaoAghu[]> {
    buscandoAghu.value = true;
    try {
      await aguardarCurto(180);
      const pront = (params.prontuario ?? '').trim();
      const solic = (params.codigoSolicitacao ?? '').trim();
      const nomeNorm = normalizarTexto(params.nome);

      if (!pront && !solic && !nomeNorm) {
        return catalogoAghu.value.slice(0, 12);
      }

      return catalogoAghu.value.filter((reg) => {
        if (pront && !(reg.prontuario ?? '').includes(pront)) {
          return false;
        }
        if (solic && !reg.codigoSolicitacao.includes(solic)) {
          return false;
        }
        if (nomeNorm && !normalizarTexto(reg.nome).includes(nomeNorm)) {
          return false;
        }
        return true;
      });
    } finally {
      buscandoAghu.value = false;
    }
  }

  async function vincularSolicitacaoAghu(
    itemId: number,
    payload: IVincularSolicitacaoPayload,
  ): Promise<IItemFila> {
    carregando.value = true;
    try {
      await aguardarCurto();
      const idx = itensBrutos.value.findIndex((item) => item.id === itemId);
      if (idx === -1) {
        throw new Error('Item da fila não encontrado para vínculo.');
      }

      const codigoSol = payload.codigoSolicitacao.trim();
      const codigoEx = normalizarTexto(payload.codigoExame);
      const oficial = catalogoAghu.value.find(
        (reg) =>
          reg.codigoSolicitacao === codigoSol && normalizarTexto(reg.codigoExame) === codigoEx,
      );

      if (!oficial) {
        throw new Error(
          `Solicitação ${codigoSol} (${codigoEx}) não encontrada no espelho somente-leitura do AGHU.`,
        );
      }

      const atual = itensBrutos.value[idx];
      itensBrutos.value[idx] = {
        ...atual,
        codigoSolicitacao: oficial.codigoSolicitacao,
        codigoExame: oficial.codigoExame,
        nomeExame: oficial.nomeExame,
        prontuario: oficial.prontuario ?? atual.prontuario,
        nomePaciente: oficial.nome || atual.nomePaciente,
        telefoneContato: oficial.telefone ?? atual.telefoneContato,
        municipio: oficial.cidade ?? atual.municipio,
        regiaoGeografica: oficial.cidade
          ? inferirRegiao(oficial.cidade)
          : atual.regiaoGeografica,
        unidadeSolicitante: oficial.unidadeSolicitante,
        especialidadeSolicitante: oficial.unidadeSolicitante,
        medicoSolicitante: oficial.nomeFuncionario,
        dataSolicitacao: oficial.dataSolicitacao,
        statusHigienizacao: 'VALIDA',
        observacoes: `Solicitação vinculada ao pedido oficial AGHU #${oficial.codigoSolicitacao} (${oficial.codigoExame}).`,
      };

      const enriquecido = obterDetalheItem(itemId);
      if (!enriquecido) {
        throw new Error('Erro ao recalcular item após vínculo com o AGHU.');
      }
      return enriquecido;
    } finally {
      carregando.value = false;
    }
  }

  async function higienizarLinhasCsv(texto: string): Promise<ILinhaHigienizadaPreview[]> {
    const linhasBrutas = texto
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter(Boolean);

    if (linhasBrutas.length < 2) {
      return [];
    }

    const delimitador = linhasBrutas[0].includes(';') ? ';' : ',';
    const cabecalho = splitLinhaCsv(linhasBrutas[0], delimitador).map((col) =>
      normalizarTexto(col),
    );

    const acharColuna = (...aliases: string[]): number =>
      cabecalho.findIndex((col) => aliases.some((alias) => col.includes(alias)));

    const idxSolic = acharColuna('SOLICITAC', 'CODIGO_SOLIC', 'PEDIDO');
    const idxPront = acharColuna('PRONTUARIO');
    const idxNome = acharColuna('PACIENTE', 'NOME');
    const idxTel = acharColuna('TELEFONE', 'WHATSAPP', 'CONTATO');
    const idxMun = acharColuna('MUNICIPIO', 'CIDADE');
    const idxTfd = acharColuna('TFD');
    const idxExame = acharColuna('EXAME', 'PROCEDIMENTO');
    const idxRetorno = acharColuna('RETORNO');

    if (idxSolic === -1 && idxNome === -1) {
      return [];
    }

    const preview: ILinhaHigienizadaPreview[] = [];

    for (let i = 1; i < linhasBrutas.length; i += 1) {
      const cols = splitLinhaCsv(linhasBrutas[i], delimitador);
      const codigoSolic = (idxSolic >= 0 ? cols[idxSolic] : '') || '';
      const prontuario = (idxPront >= 0 ? cols[idxPront] : '') || null;
      const nome = (idxNome >= 0 ? cols[idxNome] : '') || `PACIENTE LINHA ${i}`;
      const telefone = (idxTel >= 0 ? cols[idxTel] : '') || null;
      const municipio = (idxMun >= 0 ? cols[idxMun] : '') || null;
      const tfdRaw = normalizarTexto(idxTfd >= 0 ? cols[idxTfd] : '');
      const utilizaTfd = tfdRaw === 'SIM' || tfdRaw === 'TRUE' || tfdRaw === '1';
      const exameInformado = (idxExame >= 0 ? cols[idxExame] : '') || 'Não informado';
      const retorno = (idxRetorno >= 0 ? cols[idxRetorno] : '') || null;

      const aghuMatch = catalogoAghu.value.find(
        (reg) => reg.codigoSolicitacao === codigoSolic.trim(),
      );
      const jaNaFila = itensBrutos.value.find(
        (it) =>
          it.codigoSolicitacao === codigoSolic.trim() && it.statusOperacional !== 'CANCELADO',
      );

      let statusHigienizacao: StatusHigienizacao = 'VALIDA';
      let detalhe = 'Solicitação confirmada no espelho AGHU.';

      if (!aghuMatch) {
        statusHigienizacao = 'NAO_ENCONTRADA';
        detalhe = `Solicitação ${codigoSolic || 'sem código'} não encontrada no espelho AGHU; encaminhada para Busca Ativa.`;
      } else if (jaNaFila && jaNaFila.statusHigienizacao === 'JA_REALIZADA') {
        statusHigienizacao = 'JA_REALIZADA';
        detalhe = `Solicitação ${codigoSolic} já realizada anteriormente no AGHU.`;
      } else if (jaNaFila) {
        statusHigienizacao = 'DUPLICADA';
        detalhe = `Duplicidade barrada: solicitação ${codigoSolic} já está ativa na fila.`;
      } else {
        const exFormsNorm = normalizarTexto(exameInformado);
        const exAghuCodigo = normalizarTexto(aghuMatch.codigoExame);
        const exAghuNome = normalizarTexto(aghuMatch.nomeExame);
        const combina =
          !exFormsNorm ||
          exFormsNorm.includes(exAghuCodigo) ||
          exAghuNome.includes(exFormsNorm) ||
          exFormsNorm
            .split(/\s+/)
            .some((tok) => tok.length >= 4 && exAghuNome.includes(tok));

        if (!combina) {
          statusHigienizacao = 'DIVERGENCIA_EXAME';
          detalhe = `Divergência Forms × AGHU: Forms informou "${exameInformado}", mas o AGHU indica ${aghuMatch.codigoExame} (${aghuMatch.nomeExame}).`;
        } else {
          detalhe = `Solicitação ${aghuMatch.codigoSolicitacao} validada no AGHU (${aghuMatch.codigoExame}).`;
        }
      }

      const municipioFinal = aghuMatch?.cidade ?? municipio;

      preview.push({
        linhaNumero: i,
        codigoSolicitacaoInformado: codigoSolic || `SEM-COD-${i}`,
        prontuario: aghuMatch?.prontuario ?? prontuario,
        nomePaciente: aghuMatch?.nome ?? nome,
        telefoneContato: aghuMatch?.telefone ?? telefone,
        municipio: municipioFinal,
        regiaoGeografica: inferirRegiao(municipioFinal),
        utilizaTfd,
        exameInformadoForms: exameInformado,
        codigoExameAghu: aghuMatch?.codigoExame ?? null,
        nomeExameAghu: aghuMatch?.nomeExame ?? null,
        unidadeSolicitante: aghuMatch?.unidadeSolicitante ?? null,
        dataRetornoMedico: retorno,
        statusHigienizacao,
        detalheHigienizacao: detalhe,
      });
    }

    return preview;
  }

  async function processarUploadForms(
    arquivo: File | null,
    usuario = 'marcador.central',
  ): Promise<IImportacaoForms> {
    carregando.value = true;
    try {
      await aguardarCurto(320);

      let linhasPreview: ILinhaHigienizadaPreview[] = [];
      if (arquivo && /\.(csv|txt)$/i.test(arquivo.name)) {
        try {
          const texto = await arquivo.text();
          linhasPreview = await higienizarLinhasCsv(texto);
        } catch {
          linhasPreview = [];
        }
      }

      if (linhasPreview.length === 0) {
        linhasPreview = MOCK_LOTE_UPLOAD_DEMO.map((linha) => ({ ...linha }));
      }

      const proximoImportacaoId =
        historicoImportacoes.value.reduce((max, imp) => Math.max(max, imp.id), 0) + 1;

      const totalValidas = linhasPreview.filter((l) => l.statusHigienizacao === 'VALIDA').length;
      const totalDuplicadas = linhasPreview.filter(
        (l) => l.statusHigienizacao === 'DUPLICADA',
      ).length;
      const totalDivergencias = linhasPreview.filter(
        (l) => l.statusHigienizacao === 'DIVERGENCIA_EXAME',
      ).length;
      const totalNaoEncontradas = linhasPreview.filter(
        (l) => l.statusHigienizacao === 'NAO_ENCONTRADA',
      ).length;
      const totalJaRealizadas = linhasPreview.filter(
        (l) => l.statusHigienizacao === 'JA_REALIZADA',
      ).length;

      const novoLote: IImportacaoForms = {
        id: proximoImportacaoId,
        nomeArquivo: arquivo?.name || `forms_central_simulacao_lote_${proximoImportacaoId}.xlsx`,
        importadoEm: new Date().toISOString(),
        usuarioImportador: usuario,
        totalLinhas: linhasPreview.length,
        totalValidas,
        totalDuplicadas,
        totalDivergencias,
        totalNaoEncontradas,
        totalJaRealizadas,
        totalErros: 0,
        linhasPreview,
      };

      // Insere novos itens elegíveis (VALIDA, DIVERGENCIA_EXAME, NAO_ENCONTRADA) na fila sem duplicar os já existentes
      let proximoItemId = itensBrutos.value.reduce((max, it) => Math.max(max, it.id), 100) + 1;

      for (const linha of linhasPreview) {
        if (
          linha.statusHigienizacao === 'DUPLICADA' ||
          linha.statusHigienizacao === 'JA_REALIZADA'
        ) {
          continue;
        }
        const jaExiste = itensBrutos.value.some(
          (it) =>
            it.codigoSolicitacao === linha.codigoSolicitacaoInformado &&
            normalizarTexto(it.codigoExame) === normalizarTexto(linha.codigoExameAghu),
        );
        if (jaExiste) {
          continue;
        }
        const aghuMatch = catalogoAghu.value.find(
          (reg) =>
            reg.codigoSolicitacao === linha.codigoSolicitacaoInformado &&
            (!linha.codigoExameAghu ||
              normalizarTexto(reg.codigoExame) === normalizarTexto(linha.codigoExameAghu)),
        );

        itensBrutos.value.push({
          id: proximoItemId,
          importacaoId: proximoImportacaoId,
          codigoSolicitacao: linha.codigoSolicitacaoInformado,
          codigoExame: linha.codigoExameAghu,
          nomeExame: linha.nomeExameAghu,
          exameInformadoForms: linha.exameInformadoForms,
          prontuario: linha.prontuario,
          nomePaciente: linha.nomePaciente,
          dataNascimento: null,
          telefoneContato: linha.telefoneContato,
          municipio: linha.municipio,
          regiaoGeografica: linha.regiaoGeografica,
          utilizaTfd: linha.utilizaTfd,
          unidadeSolicitante: linha.unidadeSolicitante,
          especialidadeSolicitante: linha.unidadeSolicitante,
          medicoSolicitante: aghuMatch?.nomeFuncionario ?? null,
          flagHemodialise: normalizarTexto(linha.unidadeSolicitante).includes('HEMODIALISE'),
          flagDiabeticoJejum: false,
          grupoPrioritarioManual: null,
          dataSolicitacao: aghuMatch?.dataSolicitacao ?? new Date().toISOString(),
          dataRetornoMedico: linha.dataRetornoMedico,
          statusHigienizacao: linha.statusHigienizacao,
          statusOperacional: 'NA_FILA',
          scorePrioridade: 0,
          motivosPrioridade: [],
          alertas: [],
          contatoIniciadoEm: null,
          prazoConfirmacaoEm: null,
          dataAgendadaAghu: null,
          preparoOrientado: false,
          observacoes: linha.detalheHigienizacao,
        });
        proximoItemId += 1;
      }

      historicoImportacoes.value.unshift(novoLote);
      ultimaImportacao.value = novoLote;
      return novoLote;
    } finally {
      carregando.value = false;
    }
  }

  return {
    itensBrutos,
    catalogoAghu,
    historicoImportacoes,
    ultimaImportacao,
    filtros,
    carregando,
    buscandoAghu,
    itensEnriquecidos,
    filaFiltrada,
    examesDisponiveis,
    unidadesDisponiveis,
    municipiosDisponiveis,
    resumoOperacional,
    definirFiltros,
    limparFiltros,
    obterDetalheItem,
    selecionarImportacao,
    atualizarStatusOperacional,
    buscarNoAghu,
    vincularSolicitacaoAghu,
    processarUploadForms,
  };
});
