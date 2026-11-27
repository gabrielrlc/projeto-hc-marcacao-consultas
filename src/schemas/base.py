"""
Schema Base camelCase
=====================
Base comum para todos os schemas da API: serializa respostas em ``camelCase``
(ex: ``codigoExame``) e aceita entradas em ``camelCase`` ou ``snake_case``.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Modelo Pydantic base com aliases camelCase e leitura de objetos ORM."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
        from_attributes=True,
        str_strip_whitespace=True,
    )
