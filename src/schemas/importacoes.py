"""
Schemas da Importação do Google Forms (``/api/importacoes``)
============================================================
Contratos de saída do upload/higienização ``Forms × AGHU`` e do histórico de
importações (camelCase, via ``CamelModel``).
"""

from datetime import date, datetime
from typing import Dict, List, Optional

from .base import CamelModel


class ImportacaoResumoOut(CamelModel):
    """Registro do histórico de importações (``importacoes_forms``)."""

    id: int
    nome_arquivo: str
    importado_em: datetime
    usuario_importador: str
    total_linhas: int
    total_validas: int
    total_duplicadas: int
    total_erros: int


class ItemImportacaoOut(CamelModel):
    """Item higienizado gerado pela importação (``acompanhamento_fila``)."""

    id: int
    linha_planilha: Optional[int] = None
    codigo_solicitacao: str
    codigo_exame: Optional[str]
    prontuario: Optional[str]
    nome_paciente: str
    exame_informado_forms: Optional[str]
    unidade_solicitante: Optional[str]
    municipio: Optional[str]
    regiao_geografica: str
    utiliza_tfd: bool
    data_retorno_medico: Optional[date]
    idade_informada: Optional[int]
    status_higienizacao: str
    status_operacional: str
    observacoes: Optional[str]


class RelatorioImportacaoOut(CamelModel):
    """Relatório completo de uma importação: totais, colunas lidas e itens."""

    importacao: ImportacaoResumoOut
    contadores: Dict[str, int]
    colunas_reconhecidas: Dict[str, str] = {}
    colunas_ignoradas: List[str] = []
    itens: List[ItemImportacaoOut]
