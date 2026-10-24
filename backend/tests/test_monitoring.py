"""Synthetic identity fixtures only; never seed the operational database."""
import csv,json,copy
from pathlib import Path
import pytest
from app.monitoring import reconcile
from app.monitoring import register
from app.sources import job_context,observe

ROOT=Path(__file__).resolve().parents[2]

def fixture():
    origin=list(csv.DictReader((ROOT/'dados/municipios_118_origem.csv').read_text(encoding='utf-8-sig').splitlines(),delimiter=';'))
    seed=json.loads((ROOT/'backend/seed_data/cities.json').read_text(encoding='utf-8-sig'))
    official=[{'id':r['id'],'nome':r['name'],'microrregiao':{'mesorregiao':{'UF':{'sigla':r['uf']}}}} for r in seed]
    return origin,seed,official

def test_exact_118_aliases_and_no_membership_inference():
    rows=reconcile(*fixture())
    assert len(rows)==118 and len({r['ibge'] for r in rows})==118
    assert all(r['membership_status']=='PENDING' and r['monitoring_enabled'] for r in rows)
    assert next(r for r in rows if r['ibge']=='3163508')['origin_name']=='Jacuri'

@pytest.mark.parametrize('change',['missing','duplicate','wrong_name','wrong_uf','wrong_code','alias_changed'])
def test_invalid_roster_rejected_before_any_write(change):
    origin,seed,official=fixture()
    if change=='missing':official.pop()
    if change=='duplicate':seed[1]=copy.deepcopy(seed[0])
    if change=='wrong_name':official[0]['nome']='Outra cidade'
    if change=='wrong_uf':official[0]['microrregiao']['mesorregiao']['UF']['sigla']='SP'
    if change=='wrong_code':official[0]['id']='9999999'
    if change=='alias_changed':origin[0]['municipio_nome_origem']='Nome não aprovado'
    with pytest.raises(ValueError):reconcile(origin,seed,official)

def test_registration_is_idempotent_tenant_scoped_and_not_membership(app,login):
    client=login();identity=client.get('/api/v1/auth/context').json();rows=reconcile(*fixture())
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        ctx=job_context(db,identity['org_id'],identity['actor_id'])
        sid=observe(ctx,'IBGE','https://servicodados.ibge.gov.br/api/v1/localidades/estados/QA/municipios',200,b'[]',{'fixture_only':True})
        first=register(ctx,rows,{'MG':sid,'RJ':sid},'a'*64)
        second=register(ctx,rows,{'MG':sid,'RJ':sid},'a'*64)
        assert first==second
        assert db.one('SELECT count(*) n FROM monitoring_target')['n']==118
        rls=db.one("SELECT relrowsecurity,relforcerowsecurity FROM pg_class WHERE relname='monitoring_target'")
        assert rls['relrowsecurity'] and rls['relforcerowsecurity']
    response=client.get('/api/v1/portfolio/municipalities');assert response.status_code==200
    assert response.json()['monitored']==118 and response.json()['membership_confirmed']==0
    assert login('compras-b').get('/api/v1/portfolio/municipalities').json()['records']==[]
