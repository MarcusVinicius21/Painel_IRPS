"""Valor estimado de cenário de licitação; distinto de preço de venda e orçamento privado."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from .domain import ValidationError

CENT=Decimal('0.01')
@dataclass(frozen=True)
class ReferencePrice:
    item_key: str
    specification_version: str
    unit: str
    unit_price_brl: Decimal
    source_url: str
    reference_date: str
    validated: bool

@dataclass(frozen=True)
class TenderLine:
    municipality_ibge: str
    item_key: str
    specification_version: str
    unit: str
    quantity: Decimal
    price: ReferencePrice

@dataclass(frozen=True)
class TenderSummary:
    by_municipality: dict[str, Decimal]
    by_item: dict[str, Decimal]
    total_brl: Decimal
    lines: int


def calculate_tender_value(lines: list[TenderLine]) -> TenderSummary:
    """Falha se faltar preço validado. Não transforma valores estimados em pagamentos."""
    if not lines:
        raise ValidationError('Cenário sem itens ou municípios.')
    seen=set()
    by_city={}; by_item={}
    for l in lines:
        p=l.price
        if len(l.municipality_ibge)!=7 or not l.municipality_ibge.isdigit():
            raise ValidationError('Identificação municipal inválida.')
        try:
            if date.fromisoformat(p.reference_date).isoformat()!=p.reference_date:
                raise ValueError('Formato não canônico')
        except (ValueError,TypeError):
            raise ValidationError('Data da referência deve ser uma data ISO válida.') from None
        key=(l.municipality_ibge,l.item_key,l.specification_version,l.unit)
        if key in seen:
            raise ValidationError('Linha duplicada: revise a origem e a consolidação.')
        seen.add(key)
        if (l.item_key != p.item_key or l.unit != p.unit or
            l.specification_version != p.specification_version):
            raise ValidationError('Preço de outra especificação/unidade não é comparável.')
        if not p.validated or not p.source_url.startswith(('https://','http://')) or not p.reference_date:
            raise ValidationError('Preço de referência ainda não validado ou sem origem.')
        if not p.unit_price_brl.is_finite() or p.unit_price_brl<0 or not l.quantity.is_finite() or l.quantity<0:
            raise ValidationError('Preço/quantidade inválidos.')
        value=(l.quantity*p.unit_price_brl).quantize(CENT,rounding=ROUND_HALF_UP)
        by_city[l.municipality_ibge]=by_city.get(l.municipality_ibge,Decimal('0'))+value
        by_item[l.item_key]=by_item.get(l.item_key,Decimal('0'))+value
    return TenderSummary(by_city,by_item,sum(by_city.values(),Decimal('0.00')),len(lines))
