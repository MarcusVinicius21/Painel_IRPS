from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import Field, model_validator
from .schemas import Strict, Code, ItemRef, Number

PHASES = Literal['publicado_estimado','homologado','contratado','solicitado','empenhado','liquidado','entregue','pago','consumido','estorno']

class HistoricalScope(Strict):
    municipalities: list[Code] = Field(min_length=1,max_length=6000)
    start: date
    end: date
    modalities: list[int] = Field(default_factory=lambda:[6],min_length=1,max_length=14)
    publications: bool = True
    contracts: bool = False
    organization_cnpjs: list[str] = Field(default_factory=list,max_length=200)
    items: bool = True
    results: bool = True
    size: int = Field(default=10,ge=10,le=20)
    max_pages: int = Field(default=100,ge=1,le=2000)
    @model_validator(mode='after')
    def bounds(self):
        if self.end<self.start or (self.end-self.start).days>1826 or self.end>date.today():raise ValueError('Escolha até cinco anos encerrados na data atual.')
        if len(set(self.municipalities))!=len(self.municipalities):raise ValueError('Município repetido.')
        if len(set(self.modalities))!=len(self.modalities) or any(m<1 or m>14 for m in self.modalities):raise ValueError('Modalidade inválida.')
        if not self.publications and not self.contracts:raise ValueError('Escolha ao menos uma fonte.')
        if self.results and not self.items:raise ValueError('Resultados precisam dos itens.')
        if self.contracts and not self.organization_cnpjs:raise ValueError('Contratos exigem CNPJ do órgão; a fonte não filtra por município.')
        if any(not __import__('re').fullmatch(r'\d{14}',x) for x in self.organization_cnpjs):raise ValueError('CNPJ do órgão inválido.')
        windows=((self.end-self.start).days//7)+1
        if windows*(len(self.municipalities)*len(self.modalities)*self.publications+len(self.organization_cnpjs)*self.contracts)>6000:raise ValueError('Divida o período em recortes menores.')
        return self

class Advance(Strict):
    pages: int = Field(default=1,ge=1,le=3)

class MunicipalGroup(Strict):
    name: str = Field(min_length=3,max_length=120)
    municipalities: list[Code] = Field(min_length=1,max_length=6000)

class OpportunityFilter(Strict):
    dataset: Literal['official','synthetic']='official'
    phase: PHASES='homologado'
    start: date = date(2024,1,1)
    end: date = Field(default_factory=date.today)
    municipalities: list[Code] = Field(default_factory=list,max_length=6000)
    groups: list[str] = Field(default_factory=list,max_length=100)
    buyers: list[str] = Field(default_factory=list,max_length=100)
    categories: list[str] = Field(default_factory=list,max_length=100)
    item_ids: list[str] = Field(default_factory=list,max_length=100)
    modalities: list[int] = Field(default_factory=list,max_length=14)
    suppliers: list[str] = Field(default_factory=list,max_length=100)
    months: list[int] = Field(default_factory=list,max_length=12)
    years: list[int] = Field(default_factory=list,max_length=20)
    q: str = Field(default='',max_length=150)
    min_quantity: Number|None=None
    max_quantity: Number|None=None
    min_amount: Number|None=None
    max_amount: Number|None=None
    min_price: Number|None=None
    max_price: Number|None=None
    weights: dict[str,int] = Field(default_factory=lambda:{'recurrence':30,'spread':20,'price':20,'ease':30})
    order: Literal['priority','recurrence','municipalities','value']='recurrence'
    offset: int = Field(default=0,ge=0,le=20000)
    limit: int = Field(default=30,ge=1,le=100)
    @model_validator(mode='after')
    def bounds(self):
        if self.end<self.start or (self.end-self.start).days>3653 or self.end>date.today():raise ValueError('Escolha um período histórico encerrado na data atual.')
        for a,b in [('min_quantity','max_quantity'),('min_amount','max_amount'),('min_price','max_price')]:
            if getattr(self,a) is not None and getattr(self,b) is not None and getattr(self,a)>getattr(self,b):raise ValueError('Limites invertidos.')
        if any(x<1 or x>12 for x in self.months) or any(x<1 or x>14 for x in self.modalities) or any(x>date.today().year for x in self.years):raise ValueError('Mês, ano ou modalidade inválidos.')
        if set(self.weights)!={'recurrence','spread','price','ease'} or any(v<0 or v>100 for v in self.weights.values()) or sum(self.weights.values())!=100:raise ValueError('Os pesos precisam somar 100.')
        from uuid import UUID
        for value in self.groups+self.buyers:UUID(value)
        return self

class Equivalence(Strict):
    name: str = Field(min_length=5,max_length=160)
    category: str = Field(min_length=3,max_length=120)
    unit: str = Field(min_length=1,max_length=120)
    members: list[ItemRef] = Field(min_length=2,max_length=100)
    justification: str = Field(min_length=20,max_length=2000)
    evidence: str = Field(min_length=10,max_length=2000)
    confirmed: Literal[True]

class Criterion(Strict):
    rating: int = Field(ge=1,le=5)
    evidence: str = Field(min_length=10,max_length=1000)

class ViabilityReview(Strict):
    revision: int = Field(default=0,ge=0)
    criteria: dict[str,Criterion]
    legal: Literal['pending','viable','not_viable']
    operational: Literal['pending','viable','not_viable']
    legal_evidence: str = Field(min_length=10,max_length=2000)
    operational_evidence: str = Field(min_length=10,max_length=2000)
    @model_validator(mode='after')
    def criteria_keys(self):
        if set(self.criteria)!={'logistics','standardization','suppliers','requirements','deadline','availability'}:raise ValueError('Confira os seis critérios de fornecimento.')
        return self

class ScenarioFromOpportunity(Strict):
    filters: OpportunityFilter
    title: str = Field(min_length=3,max_length=180)
    period: str = Field(min_length=4,max_length=80)
    participants: list[Code] = Field(min_length=1,max_length=6000)
    expected_fingerprint: str = Field(min_length=64,max_length=64)
    confirm_review_required: Literal[True]

class OpportunityWatch(Strict):
    name: str = Field(min_length=3,max_length=160)
    filters: OpportunityFilter
    opportunity_key: str|None = Field(default=None,max_length=80)
