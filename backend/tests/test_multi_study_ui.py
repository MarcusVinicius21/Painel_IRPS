from test_multi_studies import sources,scenario,body

def test_list_is_latest_paginated_and_private(login):
 a=login();items=sources(a,2);sc=scenario(a,items);saved=a.post('/api/v1/director/multi-studies',json=body(sc,items)).json()
 records=a.get('/api/v1/director/multi-studies',params={'limit':1,'offset':0}).json()['records']
 assert len(records)==1 and records[0]['id']==saved['id']
 assert a.get('/api/v1/director/multi-studies',params={'limit':101}).status_code==422
 assert saved['id'] not in [r['id'] for r in login('compras-b').get('/api/v1/director/multi-studies').json()['records']]
