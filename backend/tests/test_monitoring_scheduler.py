from datetime import date,datetime,timezone
from app.monitoring_scheduler import select_window

def test_rotation_visits_all_cities_before_next_month():
    cities=['3100500','3100609'];today=date(2026,10,24)
    first=select_window(cities,0,today);second=select_window(cities,1,today);third=select_window(cities,2,today)
    assert first[0]!=second[0] and first[1:]==second[1:]
    assert first[1].isoformat()=='2026-09-01'
    assert third[1].isoformat()=='2026-10-01'
    assert len({select_window(cities,n,today) for n in range(26)})==26

def test_refresh_is_tenant_scoped_and_throttled(app,login):
    c=login();identity=c.get('/api/v1/auth/context').json()
    assert app.state.settings.auth_mode=='local_test'
    with app.state.database.transaction(identity['org_id'],identity['actor_id']) as db:
        db.execute('UPDATE monitoring_schedule SET last_request=NULL WHERE org_id=:o',{'o':identity['org_id']})
    response=c.get('/api/v1/portfolio/refresh');assert response.status_code==200
    assert response.json()['queue_scope']=='official_organization_collections_not_purchase_coverage'
    assert isinstance(response.json()['queue'],list)
    assert c.post('/api/v1/portfolio/refresh').status_code==202
    assert c.post('/api/v1/portfolio/refresh').status_code==429
    assert login('consulta-a').post('/api/v1/portfolio/refresh').status_code==403
    assert login('compras-b').get('/api/v1/portfolio/refresh').json()['last_run'] is None


def test_failed_city_rotates_without_marking_success(app,login,monkeypatch):
    from app import monitoring_scheduler as scheduler
    from app.monitoring import register,reconcile
    from app.sources import job_context,observe
    from test_monitoring import fixture
    c=login();identity=c.get('/api/v1/auth/context').json();org=identity['org_id'];actor=identity['actor_id']
    assert app.state.settings.auth_mode=='local_test'
    with app.state.database.transaction(org,actor) as db:
        ctx=job_context(db,org,actor)
        sid=observe(ctx,'IBGE','https://servicodados.ibge.gov.br/api/v1/localidades/estados/QA/municipios',200,b'[]',{'fixture_only':True})
        register(ctx,reconcile(*fixture()),{'MG':sid,'RJ':sid},'a'*64)
        scheduler.ensure(ctx)
        db.execute("UPDATE monitoring_schedule SET enabled=true,cursor=0,next_run=now()-interval '1 minute',last_run=NULL WHERE org_id=:o",{'o':org})
    def unavailable(*args,**kwargs):raise TimeoutError('fixture-only')
    monkeypatch.setattr(scheduler,'plan_city',unavailable)
    assert scheduler.cycle(app.state.database,org,actor,date(2026,10,24))=={'state':'failed','error_type':'TimeoutError'}
    with app.state.database.transaction(org,actor) as db:
        state=db.one('SELECT cursor,last_run,last_error,next_run>now() AS deferred FROM monitoring_schedule WHERE org_id=:o',{'o':org})
        assert state['cursor']==1 and state['last_run'] is None
        assert state['last_error']=='TimeoutError' and state['deferred']
