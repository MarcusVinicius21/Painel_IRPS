from pathlib import Path
import json,os
from pydantic import BaseModel,ConfigDict,SecretStr

APP_ROOT=Path(__file__).resolve().parents[2]
class Settings(BaseModel):
 model_config=ConfigDict(extra='forbid')
 database_url:SecretStr=SecretStr('')
 owner_database_url:SecretStr=SecretStr('')
 auth_mode:str='oidc'
 issuer:str=''
 audience:str='irps-local'
 jwks_url:str=''
 cookie_secure:bool=True
 allowed_origins:list[str]=['http://127.0.0.1:5210']
 runtime:str=str(APP_ROOT/'.runtime')
 ai_enabled:bool=False
 token_seconds:int=3600
 rate_limit:int=240
 testing:bool=False
 monitoring_worker_enabled:bool=False
 operator_org_id:str=''
 operator_actor_id:str=''
 operator_password_hash:SecretStr=SecretStr('')

def load_settings():
 # Only an explicitly selected project-local test configuration is opened.
 p=os.environ.get('IRPS_LOCAL_CONFIG','')
 if p:
  path=Path(p).resolve();base=(APP_ROOT/'.runtime').resolve()
  if base not in path.parents:raise ValueError('Configuração local fora da pasta de execução.')
  return Settings(**json.loads(path.read_text(encoding='utf-8')))
 return Settings()

