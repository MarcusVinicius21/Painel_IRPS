"""Objetos de domínio; separação rigorosa de quantidade, valor e natureza da evidência."""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

class ValidationError(ValueError):
    """Dados insuficientes, unidades incompatíveis ou regra administrativa violada."""

class FactKind(str, Enum):
    PUBLISHED_ESTIMATE = 'publicado_estimado'  # não é compra realizada
    AWARDED = 'homologado'
    CONTRACTED = 'contratado'
    ORDERED = 'solicitado'
    DELIVERED = 'entregue'
    CONSUMED = 'consumido'
    COMMITTED = 'empenhado'
    LIQUIDATED = 'liquidado'
    PAID = 'pago'    # dinheiro pago não prova a quantidade consumida

class Status(str, Enum):
    READY_FOR_REVIEW = 'para_revisao'
    INSUFFICIENT_DATA = 'dados_insuficientes'
    BLOCKED = 'bloqueado'

class Sharing(str, Enum):
    PUBLIC = 'publico'
    GOVERNMENT_INTERNAL = 'interno_publico'
    BUSINESS_PRIVATE = 'privado_empresa'

@dataclass(frozen=True)
class Municipality:
    ibge_code: str
    name: str
    state: str

    def __post_init__(self):
        # Durante migração, não inventar códigos; cadastro incompleto deve ser tratado fora de cálculos.
        if not (self.ibge_code.isdigit() and len(self.ibge_code) == 7):
            raise ValidationError('Código IBGE de sete dígitos obrigatório para cálculos.')
        if not self.name.strip() or len(self.state) != 2:
            raise ValidationError('Nome e UF obrigatórios.')

@dataclass(frozen=True)
class Item:
    key: str
    description: str
    unit: str
    category: str
    catalog_code: Optional[str] = None
    specification_version: Optional[str] = None
    quantity_step: Decimal = Decimal('1')   # 1 unidade; 0.01 m2; 0.001 m3 etc.

    def __post_init__(self):
        if not all((self.key.strip(), self.description.strip(), self.unit.strip(), self.category.strip())):
            raise ValidationError('Produto/serviço, unidade e categoria são obrigatórios.')
        if not self.quantity_step.is_finite() or self.quantity_step <= 0:
            raise ValidationError('Passo de quantidade inválido.')

@dataclass(frozen=True)
class Evidence:
    event_id: str
    municipality_ibge: str
    item_key: str
    specification_version: str
    unit: str
    kind: FactKind
    year: int
    quantity: Optional[Decimal]
    amount_brl: Optional[Decimal]
    source_url: str
    document_key: str
    source_updated_at: str
    sharing: Sharing = Sharing.PUBLIC

    def __post_init__(self):
        if not self.event_id or not self.document_key or not self.source_url.startswith(('http://','https://')):
            raise ValidationError('Identidade do registro, documento e URL da fonte obrigatórios.')
        if len(self.municipality_ibge) != 7 or not self.municipality_ibge.isdigit():
            raise ValidationError('Identificador municipal inválido.')
        if self.year < 2000 or self.year > 2100:
            raise ValidationError('Ano do registro fora do intervalo aceito.')
        if self.quantity is not None and (not self.quantity.is_finite() or self.quantity < 0):
            raise ValidationError('Quantidade negativa ou inválida.')
        if self.amount_brl is not None and (not self.amount_brl.is_finite() or self.amount_brl < 0):
            raise ValidationError('Valor negativo ou inválido.')

@dataclass(frozen=True)
class QuantityInput:
    municipality_ibge: str
    item: Item
    period: str
    driver_name: str
    driver_count: Optional[Decimal]
    units_per_driver: Optional[Decimal]
    driver_source: str
    rate_source: str
    safety_rate: Decimal = Decimal('0')
    available_stock: Decimal = Decimal('0')
    confirmed_incoming: Decimal = Decimal('0')
    floor: Optional[Decimal] = None
    ceiling: Optional[Decimal] = None
    justification: str = ''

@dataclass(frozen=True)
class NeedResult:
    municipality_ibge: str
    item_key: str
    period: str
    quantity: Optional[Decimal]
    unit: str
    status: Status
    calculation: str
    notices: tuple[str,...] = field(default_factory=tuple)
    specification_version: Optional[str] = None
