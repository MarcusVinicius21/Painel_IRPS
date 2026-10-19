"""Cálculo físico auditável e referência histórica conservadora.

Nenhum modelo universal de população serve a compras de A a Z.
"""
from __future__ import annotations
from decimal import Decimal, ROUND_CEILING
from statistics import median
from .domain import QuantityInput, NeedResult, Status, Evidence, FactKind, ValidationError


def _check_number(value: Decimal, name: str) -> None:
    if not value.is_finite() or value < 0:
        raise ValidationError(f'{name}: valor inválido/negativo.')


def calculate_need(data: QuantityInput) -> NeedResult:
    """Calcula demanda sem esconder falta de dados; saldo de orçamento não reduz necessidade física."""
    if len(data.municipality_ibge) != 7 or not data.municipality_ibge.isdigit():
        raise ValidationError('Município não resolvido por código IBGE.')
    for key in ('safety_rate', 'available_stock', 'confirmed_incoming'):
        _check_number(getattr(data, key), key)
    if data.safety_rate > Decimal('1'):
        raise ValidationError('Reserva superior a 100% exige outra modelagem explícita.')
    if data.floor is not None and (not Decimal(str(data.floor)).is_finite() or data.floor < 0):
        raise ValidationError('Piso técnico inválido.')
    if data.ceiling is not None and (not Decimal(str(data.ceiling)).is_finite() or data.ceiling < 0):
        raise ValidationError('Teto técnico inválido.')
    if data.floor is not None and data.ceiling is not None and data.floor > data.ceiling:
        return NeedResult(data.municipality_ibge, data.item.key, data.period, None, data.item.unit, Status.BLOCKED,'',('Piso maior que teto: revise os parâmetros.',),data.item.specification_version)
    if (data.driver_count is None or data.units_per_driver is None or
        not data.driver_source.strip() or not data.rate_source.strip()):
        return NeedResult(data.municipality_ibge, data.item.key, data.period, None, data.item.unit, Status.INSUFFICIENT_DATA,'',('Informe público atendido, taxa de uso e respectivas fontes.',),data.item.specification_version)
    _check_number(data.driver_count, 'driver_count')
    _check_number(data.units_per_driver, 'units_per_driver')
    demand_raw = data.driver_count * data.units_per_driver * (Decimal('1')+data.safety_rate)
    demand_net = max(Decimal('0'), demand_raw-data.available_stock-data.confirmed_incoming)
    quantity = (demand_net / data.item.quantity_step).to_integral_value(rounding=ROUND_CEILING) * data.item.quantity_step
    trace = (f'ceil(max(0, {data.driver_count} × {data.units_per_driver} × '
             f'(1 + {data.safety_rate}) - {data.available_stock} - {data.confirmed_incoming}) / {data.item.quantity_step}) × {data.item.quantity_step} = {quantity}')
    notices = []
    if data.floor is not None and quantity < data.floor:
        notices.append(f'Quantidade abaixo do piso técnico informado ({data.floor}).')
    if data.ceiling is not None and quantity > data.ceiling:
        notices.append(f'Quantidade acima do teto físico informado ({data.ceiling}).')
    if notices:
        return NeedResult(data.municipality_ibge,data.item.key,data.period,quantity,data.item.unit,Status.BLOCKED,trace,tuple(notices),data.item.specification_version)
    return NeedResult(data.municipality_ibge,data.item.key,data.period,quantity,data.item.unit,Status.READY_FOR_REVIEW,trace,(),data.item.specification_version)


def forecast_from_history(events: list[Evidence], item_key: str, municipal_ibge: str, unit: str,
                          kind: FactKind, min_distinct_years: int = 3) -> tuple[Decimal | None, list[str]]:
    """Mediana anual de fatos do MESMO tipo, apenas sinal exploratório.

    Não agrega estágios simultâneos (contratado+entregue+pago) e não prevê compra futura garantida.
    """
    if not isinstance(min_distinct_years,int) or isinstance(min_distinct_years,bool) or min_distinct_years < 1:
        raise ValidationError('Quantidade mínima de anos deve ser um inteiro positivo.')
    if kind not in (FactKind.CONSUMED, FactKind.DELIVERED, FactKind.CONTRACTED):
        return None, ['Histórico escolhido não serve para estimar quantidade consumida.']
    valid = [e for e in events if e.item_key == item_key and e.municipality_ibge == municipal_ibge
             and e.unit == unit and e.kind == kind and e.quantity is not None]
    versions = {e.specification_version for e in valid}
    if len(versions) > 1:
        return None, ['Há especificações diferentes: confirme equivalência antes de somar.']
    unique: dict[str, Evidence] = {}
    for e in valid:
        # A chave vem da origem e é estável; duplicata divergente é bloqueada.
        if e.event_id in unique and unique[e.event_id] != e:
            return None, ['Dois registros conflitantes têm a mesma identificação.']
        unique[e.event_id] = e
    by_year: dict[int, Decimal] = {}
    for e in unique.values():
        by_year[e.year] = by_year.get(e.year,Decimal('0')) + (e.quantity or Decimal('0'))
    if len(by_year) < min_distinct_years:
        return None, [f'Histórico insuficiente: {len(by_year)} de {min_distinct_years} anos necessários.']
    value = median(by_year.values())
    return Decimal(str(value)), ['Mediana histórica exploratória. Não é quantidade automaticamente aprovada.']
