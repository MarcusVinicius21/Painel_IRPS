"""Dois modos distintos de planejamento para um grupo variável de municípios."""
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from .domain import NeedResult, Status, ValidationError

@dataclass(frozen=True)
class AllocationCandidate:
    ibge: str
    weight: Decimal  # critério técnico explicitamente documentado, NUNCA população por padrão
    floor: Decimal
    ceiling: Decimal
    criteria_source: str

@dataclass(frozen=True)
class AllocationResult:
    assigned: dict[str,Decimal]
    total: Decimal
    method: str
    notices: tuple[str,...]


def allocate_independent(needs: list[NeedResult], selected: set[str]) -> AllocationResult:
    """Modo recomendado: soma as necessidades locais SEM redistribuir a saída de municípios."""
    if not selected:
        raise ValidationError('Selecione pelo menos um município.')
    by_id = {n.municipality_ibge:n for n in needs}
    if len(by_id) != len(needs):
        raise ValidationError('Duplicidade de município no mesmo item/período.')
    missing = selected - set(by_id)
    if missing:
        raise ValidationError('Municípios sem cálculo: '+', '.join(sorted(missing)))
    selected_needs = [by_id[k] for k in sorted(selected)]
    if any(n.status != Status.READY_FOR_REVIEW or n.quantity is None for n in selected_needs):
        raise ValidationError('Existem cidades sem quantidade revisável: corrigir antes de consolidar.')
    if any(not n.quantity.is_finite() or n.quantity < 0 or len(n.municipality_ibge)!=7 or not n.municipality_ibge.isdigit() for n in selected_needs):
        raise ValidationError('Quantidade ou identificação municipal inválida.')
    units = {n.unit for n in selected_needs}
    keys = {(n.item_key,n.period,n.specification_version) for n in selected_needs}
    if len(units)!=1 or len(keys)!=1:
        raise ValidationError('Não somar itens, unidades ou períodos diferentes.')
    result = {n.municipality_ibge:n.quantity for n in selected_needs}
    return AllocationResult(result,sum(result.values(),Decimal('0')),'necessidade_por_municipio',('Quantidade sujeita a revisão e aprovação dos municípios.',))


def allocate_total(target: Decimal | int, candidates: list[AllocationCandidate],
                   quantity_step: Decimal = Decimal('1')) -> AllocationResult:
    """Distribui meta justificada em passos (inteiros, kg, m² etc.) respeitando limites.

    Para itens com passos decimais, p.ex., 0.01 m², pisos, tetos e meta devem ser múltiplos
    do passo. O algoritmo opera em quotas discretas para conservar exatamente a meta.
    """
    target=Decimal(str(target))
    if not target.is_finite() or target < 0 or not candidates:
        raise ValidationError('Meta ou participantes inválidos.')
    if not quantity_step.is_finite() or quantity_step <= 0:
        raise ValidationError('Passo de quantidade inválido.')
    if len({c.ibge for c in candidates}) != len(candidates):
        raise ValidationError('Participantes duplicados.')
    if any(len(c.ibge)!=7 or not c.ibge.isdigit() for c in candidates):
        raise ValidationError('Identificação municipal inválida.')

    def to_units(v: Decimal | int) -> int:
        d=Decimal(str(v))
        if not d.is_finite() or d < 0:
            raise ValidationError('Quantidade inválida.')
        units=d/quantity_step
        if units != units.to_integral_value():
            raise ValidationError('Meta e limites devem ser múltiplos do passo de quantidade.')
        return int(units)

    target_units=to_units(target)
    floors={c.ibge:to_units(c.floor) for c in candidates}
    ceilings={c.ibge:to_units(c.ceiling) for c in candidates}
    if any(ceilings[c.ibge] < floors[c.ibge] or not c.weight.is_finite() or c.weight < 0 or
           not c.criteria_source.strip() for c in candidates):
        raise ValidationError('Pesos, limites e fontes precisam de validação.')
    lo, hi=sum(floors.values()),sum(ceilings.values())
    if target_units < lo or target_units > hi:
        raise ValidationError(f'Meta não cabe nos limites documentados: mínimo {lo*quantity_step}, máximo {hi*quantity_step}.')
    result=dict(floors)
    remaining=target_units-lo
    while remaining:
        open_cs=[c for c in candidates if result[c.ibge] < ceilings[c.ibge]]
        if not open_cs:
            raise ValidationError('Capacidade técnica insuficiente.')
        total_w=sum((Fraction(c.weight) for c in open_cs),Fraction(0))
        if total_w == 0:
            raise ValidationError('Não há pesos técnicos para distribuir as unidades restantes.')
        quotas={c.ibge:remaining*Fraction(c.weight)/total_w for c in open_cs}
        # Saturar capacidades antes de refazer a proporção do saldo livre.
        saturated=[c for c in open_cs if quotas[c.ibge]>=ceilings[c.ibge]-result[c.ibge]]
        if saturated:
            for c in saturated:
                batch=ceilings[c.ibge]-result[c.ibge]
                result[c.ibge]+=batch;remaining-=batch
            continue
        batches={c.ibge:quotas[c.ibge].numerator//quotas[c.ibge].denominator for c in open_cs}
        for ibge,x in batches.items():result[ibge]+=x
        remaining-=sum(batches.values())
        # Restos da MESMA rodada, sem recalcular quotas após arredondar para baixo.
        ranked=sorted(open_cs,key=lambda c:(-(quotas[c.ibge]-batches[c.ibge]),c.ibge))
        for c in ranked:
            if not remaining:break
            if c.weight>0 and result[c.ibge]<ceilings[c.ibge]:
                result[c.ibge]+=1;remaining-=1
    return AllocationResult({k:Decimal(v)*quantity_step for k,v in result.items()},target,
                            'meta_global_justificada',('Distribuição exploratória sujeita a validação local e administrativa.',))
