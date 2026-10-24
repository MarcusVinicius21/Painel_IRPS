import hashlib,json
from app.catalogue_evidence import declaration,automatic_checks,original_record,CATALOGUE_URL

def source():
    return {'catalogo':{'id':1,'nome':'Catálogo do Compras.gov.br','url':CATALOGUE_URL},
        'catalogoCodigoItem':'14729','materialOuServico':'S','numeroItem':1,
        'descricao':'Treinamento na área de administração pública Curso específico do órgão','unidadeMedida':'UNIDADE'}

def entry():
    sha='a'*64
    return {'kind':'CATSER','code':'14729','name':'TREINAMENTO NA AREA DE ADMINISTRACAO PUBLICA','snapshot_id':'test-snapshot',
        'sha256':sha,'snapshot_count':1,'imported_at':'2026-10-22','origin':json.dumps({'official_snapshot':True,'reconciled':True,'sha256':sha,'unique_valid_records':1})}

def fact(record):
    body=json.dumps([record],ensure_ascii=False)
    return {'description':record['descricao'],'unit':record['unidadeMedida'],'metadata':{'purchase':{'number':1},'catalogue_code':record.get('catalogoCodigoItem')},
        'provider':'PNCP_ITENS','source_body':body,'source_sha256':hashlib.sha256(body.encode()).hexdigest()}

def test_numeric_code_requires_catalogue_object_and_namespace():
    record=source();assert declaration(record)['namespace']=='CATSER'
    assert not declaration({**record,'catalogo':None})['namespace_verified']
    assert not declaration({**record,'catalogo':{'id':2,'nome':'Outro','url':CATALOGUE_URL}})['namespace_verified']
    assert not declaration({**record,'catalogo':{**record['catalogo'],'url':'https://example.invalid'}})['namespace_verified']
    assert declaration({**record,'materialOuServico':'M'})['namespace']=='CATMAT'

def test_declared_identity_does_not_merge_units_or_namespaces():
    record=source();row=fact(record)
    assert automatic_checks(entry(),row,original_record(row))['eligible']
    assert not automatic_checks({**entry(),'kind':'CATMAT'},row,record)['eligible']
    assert not automatic_checks({**entry(),'code':'99999'},row,record)['eligible']
    assert not automatic_checks(entry(),row,{**record,'catalogo':None})['eligible']
    unrelated={**row,'description':'Não é treinamento. Produto sem relação com o catálogo.'}
    assert not automatic_checks(entry(),unrelated,record)['eligible']
    assert not automatic_checks(entry(),{**row,'unit':''},record)['eligible']
    assert automatic_checks(entry(),row,record)['technical_equivalence_between_purchases'] is False

def test_original_source_hash_description_and_unit_are_required():
    row=fact(source());assert original_record(row)
    assert original_record({**row,'source_sha256':'0'*64}) is None
    assert original_record({**row,'description':'Descrição alterada'}) is None
    assert original_record({**row,'unit':'CAIXA'}) is None
    padded={**source(),'descricao':' '+source()['descricao']+' ','unidadeMedida':'UNIDADE  '}
    preserved=fact(padded)
    assert original_record({**preserved,'description':padded['descricao'].strip(),'unit':'UNIDADE'})==padded
