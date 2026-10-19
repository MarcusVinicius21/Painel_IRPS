from contextlib import contextmanager
import json,uuid,datetime
from decimal import Decimal
from sqlalchemy import create_engine,text
from .config import Settings

def identifier():return str(uuid.uuid4())
def normalize(value):
 if isinstance(value,dict):return {str(k):normalize(v) for k,v in value.items()}
 if isinstance(value,(list,tuple)):return [normalize(v) for v in value]
 if isinstance(value,(Decimal,uuid.UUID)):return str(value)
 if isinstance(value,(datetime.datetime,datetime.date)):return value.isoformat()
 return value
def encoded(value):return json.dumps(normalize(value),ensure_ascii=False,separators=(',',':'))
class DB:
 def __init__(self,conn):self.conn=conn
 def all(self,sql,params=None):return [dict(r) for r in self.conn.execute(text(sql),params or {}).mappings()]
 def one(self,sql,params=None):
  rows=self.all(sql,params);return rows[0] if rows else None
 def execute(self,sql,params=None):return self.conn.execute(text(sql),params or {})
class Database:
 def __init__(self,settings:Settings):
  self.engine=create_engine(settings.database_url.get_secret_value(),pool_pre_ping=True,hide_parameters=True,pool_size=8,max_overflow=8) if settings.database_url.get_secret_value() else None
 @contextmanager
 def transaction(self,org=None,actor=None):
  if self.engine is None:raise RuntimeError('Banco não configurado.')
  with self.engine.begin() as conn:
   if org:conn.execute(text("SELECT set_config('irps.org_id',:org,true),set_config('irps.actor_id',:actor,true)"),{'org':str(org),'actor':str(actor or '')})
   yield DB(conn)

