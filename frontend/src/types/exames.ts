/**
 * Contratos TypeScript do módulo de Gestão de Fila e Triagem de Exames (HC-UFPE).
 * Alinhados a `docs/especificacao/05-interfaces.md`, `src/schemas/fila.py` e
 * `src/resources/seed_exames.py`.
 *
 * Regra LGPD/AGHU: nunca exibir ou solicitar CPF; a chave clínica visual é
 * sempre `prontuario` + `codigoSolicitacao`.
 */

export type RegiaoGeografica = 'CAPITAL' | 'RMR' | 'INTERIOR' | 'NAO_INFORMADO';

export type StatusHigienizacao =
  | 'VALIDA'
  | 'DUPLICADA'
  | 'DIVERGENCIA_EXAME'
  | 'NAO_ENCONTRADA'
  | 'JA_REALIZADA';

export type StatusOperacional =
  | 'NA_FILA'
  | 'AGUARDANDO_CONFIRMACAO_24H'
  | 'CONFIRMADO_AGENDADO_AGHU'
  | 'SEM_RESPOSTA_24H'
  | 'CANCELADO';

export type TipoAlerta =
  | 'INCOMPATIBILIDADE'
  | 'JANELA_RETORNO'
  | 'ANTECEDENCIA_PREPARO'
  | 'JEJUM_CLINICO'
  | 'IDADE_MAMOGRAFIA'
  | 'PRAZO_24H_VENCIDO'
  | 'DUPLICIDADE';

export type SeveridadeAlerta = 'ALTA' | 'MEDIA' | 'INFO';

export type TipoCriterioPrioridade =
  | 'CLINICA'
  | 'GRUPO_CLINICO'
  | 'VULNERAVEL'
  | 'AFINIDADE_EXAME'
  | 'RETORNO_PROXIMO';

export type TipoConflitoExame = 'MESMO_DIA' | 'PREPARO' | 'INTERVALO_MINIMO';

export type PeriodoDashboard = 7 | 30 | 90 | 'TODOS';

export interface IAlertaExame {
  tipo: TipoAlerta;
  severidade: SeveridadeAlerta;
  mensagem: string;
}

export interface IOutroExameProntuario {
  codigoSolicitacao: string | null;
  codigoExame: string | null;
  nomeExame: string | null;
  origem: 'FILA' | 'AGHU';
  dataAgendada: string | null;
  statusOperacional: StatusOperacional | null;
}

export interface IItemFila {
  id: number;
  importacaoId?: number;
  codigoSolicitacao: string;
  codigoExame: string | null;
  nomeExame: string | null;
  exameInformadoForms?: string | null;
  prontuario: string | null;
  nomePaciente: string;
  dataNascimento?: string | null;
  telefoneContato: string | null;
  municipio: string | null;
  regiaoGeografica: RegiaoGeografica;
  utilizaTfd: boolean;
  unidadeSolicitante: string | null;
  especialidadeSolicitante?: string | null;
  medicoSolicitante?: string | null;
  flagHemodialise?: boolean;
  flagDiabeticoJejum?: boolean;
  grupoPrioritarioManual?: string | null;
  dataSolicitacao: string | null;
  dataRetornoMedico: string | null;
  statusHigienizacao: StatusHigienizacao;
  statusOperacional: StatusOperacional;
  scorePrioridade: number;
  motivosPrioridade: string[];
  alertas: IAlertaExame[];
  contatoIniciadoEm: string | null;
  prazoConfirmacaoEm: string | null;
  dataAgendadaAghu: string | null;
  preparoOrientado: boolean;
  observacoes?: string | null;
  orientacoesPreparo?: string | null;
  outrosExames?: IOutroExameProntuario[];
}

export interface ISolicitacaoAghu {
  prontuario: string | null;
  nome: string;
  telefone: string | null;
  cidade: string | null;
  estado: string | null;
  codigoSolicitacao: string;
  dataSolicitacao: string;
  unidadeSolicitante: string;
  codigoExame: string;
  nomeExame: string;
  idFuncionario: number;
  nomeFuncionario: string;
}

export interface IFiltrosFila {
  busca: string;
  codigoExame: string;
  unidade: string;
  statusOperacional: StatusOperacional | 'TODOS';
  statusHigienizacao: StatusHigienizacao | 'TODOS';
  regiao: RegiaoGeografica | 'TODAS';
  municipio: string;
  apenasTfd: boolean;
  apenas24hVencidos: boolean;
  apenasComAlertas: boolean;
}

export interface IAtualizarStatusPayload {
  statusOperacional: StatusOperacional;
  dataAgendadaAghu?: string | null;
  preparoOrientado?: boolean;
  observacoes?: string | null;
}

export interface IVincularSolicitacaoPayload {
  codigoSolicitacao: string;
  codigoExame: string;
}

export interface ILinhaHigienizadaPreview {
  linhaNumero: number;
  codigoSolicitacaoInformado: string;
  prontuario: string | null;
  nomePaciente: string;
  telefoneContato: string | null;
  municipio: string | null;
  regiaoGeografica: RegiaoGeografica;
  utilizaTfd: boolean;
  exameInformadoForms: string;
  codigoExameAghu: string | null;
  nomeExameAghu: string | null;
  unidadeSolicitante: string | null;
  dataRetornoMedico: string | null;
  statusHigienizacao: StatusHigienizacao;
  detalheHigienizacao: string;
}

export interface IImportacaoForms {
  id: number;
  nomeArquivo: string;
  importadoEm: string;
  usuarioImportador: string;
  totalLinhas: number;
  totalValidas: number;
  totalDuplicadas: number;
  totalDivergencias: number;
  totalNaoEncontradas: number;
  totalJaRealizadas: number;
  totalErros: number;
  linhasPreview: ILinhaHigienizadaPreview[];
}

export interface IRegraPrioridade {
  id: number;
  codigo: string;
  nome: string;
  tipoCriterio: TipoCriterioPrioridade;
  valorMatch: string;
  peso: number;
  ativo: boolean;
  descricao?: string | null;
  updatedAt?: string;
  deletedAt?: string | null;
}

export interface IRegraExame {
  id: number;
  codigoExame: string;
  nomeExame: string;
  unidadeExecutora: string | null;
  antecedenciaMinimaDias: number;
  janelaRetornoMaxHoras: number | null;
  exigeJejum: boolean;
  priorizarManhaDiabetico: boolean;
  idadeMinimaAlerta: number | null;
  orientacoesPreparo: string | null;
  ativo: boolean;
  updatedAt?: string;
  deletedAt?: string | null;
}

export interface IIncompatibilidadeExame {
  id: number;
  codigoExameOrigem: string;
  codigoExameConflitante: string;
  tipoConflito: TipoConflitoExame;
  intervaloMinimoDias: number;
  motivo: string;
  ativo: boolean;
  deletedAt?: string | null;
}

export interface IKpiDashboard {
  totalNaFila: number;
  aguardando24h: number;
  prazo24hVencidos: number;
  confirmadosAgendados: number;
  semResposta24h: number;
  taxaConfirmacao24h: number;
  duplicidadesBarradas: number;
  divergenciasDetectadas: number;
  naoEncontradasAghu: number;
  tempoMedioEsperaDias: number;
  totalTfdFila: number;
  filaPorExame: Array<{ codigoExame: string; exame: string; quantidade: number }>;
  filaPorUnidade: Array<{ unidade: string; quantidade: number }>;
  filaPorRegiao: Array<{
    regiao: RegiaoGeografica;
    label: string;
    quantidade: number;
    percentual: number;
  }>;
}
