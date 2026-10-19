"""Política de leitura de referência; produção deve verificar autorização e tenant no servidor."""
from enum import Enum
from .domain import Sharing

class Role(str, Enum):
    PUBLIC_READER='leitor_publico'
    SUPPLIER='fornecedor'
    MUNICIPAL_OPERATOR='operador_municipal'
    CONSORTIUM_ANALYST='analista_consorcio'
    ORG_ADMIN='administrador_org'


def may_read(role: Role, level: Sharing, same_organization: bool=False,
             organization_kind: str | None=None) -> bool:
    """ORG_ADMIN exige tipo da organização; evitar superpoderes em dados cruzados.

    organization_kind = 'governo' | 'consorcio' | 'fornecedor'.
    """
    if level==Sharing.PUBLIC: return True
    if not same_organization: return False
    if level==Sharing.GOVERNMENT_INTERNAL:
        return role in (Role.MUNICIPAL_OPERATOR,Role.CONSORTIUM_ANALYST) or (
            role==Role.ORG_ADMIN and organization_kind in ('governo','consorcio'))
    if level==Sharing.BUSINESS_PRIVATE:
        return role==Role.SUPPLIER or (role==Role.ORG_ADMIN and organization_kind=='fornecedor')
    return False
