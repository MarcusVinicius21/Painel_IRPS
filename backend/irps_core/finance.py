"""Simulação comercial isolada dos preços públicos de referência e dos orçamentos do município."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
from .domain import ValidationError

CENT = Decimal('0.01')

def money(v: Decimal) -> Decimal:
    return v.quantize(CENT, rounding=ROUND_HALF_UP)

@dataclass(frozen=True)
class QuoteInput:
    quantity: Decimal | int
    acquisition_cost_unit: Decimal
    intended_sale_price_unit: Decimal
    fixed_freight: Decimal=Decimal('0')
    fixed_expenses: Decimal=Decimal('0')
    other_variable_cost_unit: Decimal=Decimal('0')
    sales_tax_rate: Decimal=Decimal('0')
    # Taxa representa hipótese de custo efetivo sobre o faturamento; depende de regime tributário real.

@dataclass(frozen=True)
class QuoteResult:
    gross_revenue: Decimal
    total_costs: Decimal
    contribution_profit: Decimal
    margin_percent: Decimal | None
    markup_percent: Decimal | None
    break_even_unit_price: Decimal | None


def calculate_quote(q: QuoteInput) -> QuoteResult:
    vals=(q.acquisition_cost_unit,q.intended_sale_price_unit,q.fixed_freight,
          q.fixed_expenses,q.other_variable_cost_unit,q.sales_tax_rate)
    if not Decimal(str(q.quantity)).is_finite() or q.quantity<0 or any(not x.is_finite() or x<0 for x in vals) or q.sales_tax_rate>=Decimal('1'):
        raise ValidationError('Valores inválidos; alíquota deve ficar entre 0 e menos de 100%.')
    revenue=money(q.intended_sale_price_unit*q.quantity)
    goods=money((q.acquisition_cost_unit+q.other_variable_cost_unit)*q.quantity)
    taxes=money(revenue*q.sales_tax_rate)
    costs=money(goods+q.fixed_freight+q.fixed_expenses+taxes)
    gain=money(revenue-costs)
    pct=money(Decimal('100')*gain/revenue) if revenue>0 else None
    # Markup usa custo total documentado, diferente da margem sobre receita.
    markup=money(Decimal('100')*gain/costs) if costs>0 else None
    break_even=((((q.acquisition_cost_unit+q.other_variable_cost_unit)*q.quantity+q.fixed_freight+q.fixed_expenses)
                      /(Decimal(q.quantity)*(Decimal('1')-q.sales_tax_rate))).quantize(CENT,rounding=ROUND_CEILING) if q.quantity>0 else None)
    return QuoteResult(revenue,costs,gain,pct,markup,break_even)
