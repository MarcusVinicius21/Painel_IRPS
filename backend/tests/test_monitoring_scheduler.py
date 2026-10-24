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
    assert c.get('/api/v1/portfolio/refresh').status_code==200
    assert c.post('/api/v1/portfolio/refresh').status_code==202
    assert c.post('/api/v1/portfolio/refresh').status_code==429
    assert login('consulta-a').post('/api/v1/portfolio/refresh').status_code==403
    assert login('compras-b').get('/api/v1/portfolio/refresh').json()['last_run'] is None
