from decimal import Decimal
from typing import Annotated,Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator

class Strict(BaseModel):
 model_config=ConfigDict(extra='forbid',str_strip_whitespace=True,allow_inf_nan=False)

Number=Annotated[Decimal,Field(ge=0,le=Decimal('1000000000000'),max_digits=24,decimal_places=8)]
Code=Annotated[str,Field(pattern=r'^\d{7}$')]

class ItemRef(Strict):
 id:str=Field(min_length=1,max_length=80)
 version:int=Field(ge=1,le=10000)

class NeedInput(Strict):
 driver_name:str=Field(default='Base de cálculo',max_length=160)
 driver_count:Number|None=None
 units_per_driver:Number|None=None
 driver_source:str=Field(default='',max_length=1000)
 rate_source:str=Field(default='',max_length=1000)
 safety_rate:Annotated[Decimal,Field(ge=0,le=1)]=Decimal('0')
 available_stock:Number|None=None
 confirmed_incoming:Number|None=None
 floor:Number|None=None
 ceiling:Number|None=None
 justification:str=Field(default='',max_length=2000)

class PriceInput(Strict):
 item_version:int=Field(ge=1)
 unit:str=Field(min_length=1,max_length=120)
 unit_price:Number
 source_url:str=Field(min_length=9,max_length=1000)
 reference_date:str=Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
 justification:str=Field(min_length=3,max_length=2000)
 @field_validator('source_url')
 @classmethod
 def https(cls,v):
  from urllib.parse import urlparse
  u=urlparse(v)
  if u.scheme!='https' or not u.hostname or u.username or u.password:raise ValueError('A fonte precisa de endereço HTTPS.')
  return v

class Candidate(Strict):
 ibge:Code
 weight:Number
 floor:Number
 ceiling:Number
 criteria_source:str=Field(min_length=3,max_length=1000)

class DistributionInput(Strict):
 target:Number
 justification:str=Field(min_length=10,max_length=2000)
 candidates:list[Candidate]=Field(min_length=1,max_length=6000)

class Snapshot(Strict):
 period:str=Field(min_length=4,max_length=80)
 mode:Literal['A','B']='A'
 participants:list[Code]=Field(min_length=1,max_length=6000)
 items:list[ItemRef]=Field(min_length=1,max_length=100)
 inputs:dict[str,NeedInput]=Field(default_factory=dict,max_length=600000)
 prices:dict[str,PriceInput]=Field(default_factory=dict,max_length=100)
 allocations:dict[str,DistributionInput]=Field(default_factory=dict,max_length=100)
 justification:str=Field(default='',max_length=3000)

class ScenarioCreate(Strict):
 title:str=Field(min_length=3,max_length=180)
 classification:Literal['synthetic','internal']='internal'
 snapshot:Snapshot

class SyntheticCreate(Strict):
 participants:int=Field(ge=1,le=118,default=3)
 items:int=Field(ge=1,le=100,default=5)
 title:str=Field(default='Compra compartilhada · dados fictícios',min_length=3,max_length=180)

class QuoteBody(Strict):
 quantity:Number
 acquisition_cost_unit:Number
 intended_sale_price_unit:Number
 fixed_freight:Number=Decimal('0')
 fixed_expenses:Number=Decimal('0')
 other_variable_cost_unit:Number=Decimal('0')
 sales_tax_rate:Annotated[Decimal,Field(ge=0,lt=1)]=Decimal('0')

class DocumentReview(Strict):
 revision:int=Field(ge=1)
 decision:Literal['reviewed','needs_changes']
 corrections:dict[str,str]=Field(default_factory=dict,max_length=1000)
 note:str=Field(min_length=3,max_length=2000)

class ToolCall(Strict):
 tool:Literal['search_purchases','net_payments','calculate_scenario','read_quote','forecast']
 municipality_ibge:Code|None=None
 item_id:str|None=Field(default=None,max_length=80)
 item_version:int|None=Field(default=None,ge=1)
 phase:Literal['publicado_estimado','homologado','contratado','solicitado','entregue','consumido','empenhado','liquidado','pago','estorno']|None=None
 obligation_id:str|None=Field(default=None,max_length=180)
 scenario_id:str|None=None
 quote_id:str|None=None
 dataset:Literal['official','synthetic']='official'
 @model_validator(mode='after')
 def per_tool(self):
  allowed={'search_purchases':{'municipality_ibge','item_id','item_version','phase','obligation_id'},'net_payments':{'municipality_ibge','item_id','item_version','obligation_id'},'forecast':{'municipality_ibge','item_id','item_version','phase'},'calculate_scenario':{'scenario_id'},'read_quote':{'quote_id'}}[self.tool]
  for k in ('municipality_ibge','item_id','item_version','phase','obligation_id','scenario_id','quote_id'):
   if getattr(self,k) is not None and k not in allowed:raise ValueError('Este filtro não pertence à operação escolhida.')
  if self.tool=='forecast' and (not self.municipality_ibge or self.phase not in ('contratado','entregue','consumido')):raise ValueError('Escolha município e histórico compatível para estimar quantidade.')
  from uuid import UUID
  for k in ('scenario_id','quote_id'):
   if getattr(self,k):UUID(getattr(self,k))
  return self

class AssistantBody(Strict):
 question:str=Field(min_length=2,max_length=2000)
 session_id:str|None=None
 dataset:Literal['official','synthetic']='official'

class SourceSync(Strict):
 provider:Literal['IBGE','PNCP','PNCP_ITENS','COMPRAS_CATMAT','COMPRAS_CATSER']
 procurement_id:str|None=None
 municipality_ibge:Code|None=None
 start_date:str|None=Field(default=None,pattern=r'^\d{4}-\d{2}-\d{2}$')
 end_date:str|None=Field(default=None,pattern=r'^\d{4}-\d{2}-\d{2}$')
 page:int=Field(default=1,ge=1,le=1000)
 size:int=Field(default=10,ge=10,le=20)
 modality:int=Field(default=6,ge=1,le=19)
 @model_validator(mode='after')
 def source_scope(self):
  allowed={'IBGE':{'municipality_ibge'},'PNCP':{'municipality_ibge','start_date','end_date','page','size','modality'},'PNCP_ITENS':{'procurement_id','page','size'},'COMPRAS_CATMAT':{'page','size'},'COMPRAS_CATSER':{'page','size'}}[self.provider]|{'provider'}
  if self.model_fields_set-allowed:raise ValueError('Há filtros incompatíveis com esta fonte.')
  if self.provider=='PNCP_ITENS':
   from uuid import UUID
   if not self.procurement_id:raise ValueError('Escolha uma publicação oficial para consultar os itens.')
   UUID(self.procurement_id)
  elif self.procurement_id:raise ValueError('Este filtro pertence à consulta de itens.')
  return self

class Login(Strict):
 user_key:Literal['compras-a','compras-b','consulta-a','empresa-a','empresa-b','tecnico-a']

class WatchBody(Strict):
 query:str=Field(min_length=2,max_length=180)
 dataset:Literal['official','synthetic']='official'
