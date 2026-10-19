"""Indicadores sem somar fases diferentes da mesma contratação."""
from dataclasses import dataclass
from decimal import Decimal
from .domain import Evidence, FactKind, Sharing, ValidationError

@dataclass(frozen=True)
class MarketSummary:
    kind: FactKind
    item_key: str
    unit: str
    years: tuple[int,...]
    municipalities_count: int
    records_count: int
    summed_quantity: Decimal | None
    summed_amount_brl: Decimal | None


def summarize_history(events: list[Evidence], *, kind: FactKind,item_key: str,unit: str,
                      years: set[int],municipalities: set[str],specification_version: str,
                      public_only: bool=True) -> MarketSummary:
    matches=[e for e in events if e.kind == kind and e.item_key == item_key
             and e.unit == unit and e.year in years and e.municipality_ibge in municipalities
             and e.specification_version == specification_version
             and (not public_only or e.sharing==Sharing.PUBLIC)]
    unique={}
    for e in matches:
        if e.event_id in unique and unique[e.event_id]!=e:
            raise ValidationError('Registro duplicado com conteúdo divergente: revisão obrigatória.')
        unique[e.event_id]=e
    matched=list(unique.values())
    # Diferenciar ausência (None) de zero (Decimal('0'))
    qty_values=[e.quantity for e in matched if e.quantity is not None]
    amt_values=[e.amount_brl for e in matched if e.amount_brl is not None]
    return MarketSummary(kind,item_key,unit,tuple(sorted(years)),
                         len({e.municipality_ibge for e in matched}),len(matched),
                         sum(qty_values,Decimal('0')) if kind not in (FactKind.COMMITTED,FactKind.LIQUIDATED,FactKind.PAID) and len(qty_values)==len(matched) and matched else None,
                         sum(amt_values,Decimal('0')) if len(amt_values)==len(matched) and matched else None)
