import hashlib,json
from app.municipal_catalogue import inspect_binding,summarize
from app.catalogue_evidence import CATALOGUE_URL


def fact(kind='M',**change):
    record={'numeroItem':1,'descricao':'Papel A4 caixa com 10 resmas','unidadeMedida':'caixa com 10 resmas',
        'catalogo':{'id':1,'url':CATALOGUE_URL,'nome':'Catálogo do Compras.gov.br'},
        'catalogoCodigoItem':'123','materialOuServico':kind}
    record.update(change);body=json.dumps([record])
    return {'id':'qa-fact','source_id':'qa-source','item_id':'qa-item','item_version':1,
        'description':record['descricao'],'unit':record['unidadeMedida'],'provider':'PNCP_ITENS',
        'metadata':{'purchase':{'number':1}},'source_body':body,
        'source_sha256':hashlib.sha256(body.encode()).hexdigest()}


def test_equal_numeric_codes_in_different_namespaces_remain_distinct():
    a=inspect_binding(fact('M'));b=inspect_binding(fact('S'))
    assert a['namespace']=='CATMAT' and b['namespace']=='CATSER'
    result=summarize([a,b]);assert result['distinct_declared_codes']==2
    assert result['links_created']==0 and result['technical_equivalences_created']==0


def test_missing_code_missing_unit_and_source_hash_require_review():
    a=inspect_binding(fact(catalogoCodigoItem=None))
    assert a['state']=='requires_review' and a['code'] is None
    b=inspect_binding({**fact(),'source_sha256':'bad'})
    assert b['reasons']==['ORIGINAL_RECORD_NOT_VERIFIED']
    c=inspect_binding(fact(unidadeMedida=None))
    assert c['unit'] is None and c['state']=='requires_review'


def test_local_catalogue_number_does_not_imply_catmat():
    row=fact(catalogo={'id':999,'url':'https://example.invalid/qa','nome':'CATMAT'})
    result=inspect_binding(row)
    assert result['namespace'] is None and result['reasons']==['CATALOGUE_NAMESPACE_OR_CODE_MISSING']


def entry():
    sha='a'*64
    return {'snapshot_id':'qa-snapshot','kind':'CATMAT','code':'123',
        'name':'PAPEL A4 CAIXA COM 10 RESMAS','sha256':sha,'snapshot_count':1,'imported_at':'2026-10-24',
        'origin':json.dumps({'official_snapshot':True,'reconciled':True,'sha256':sha,'unique_valid_records':1})}


def test_reuses_existing_gate_and_never_converts_units_or_catalogue_namespace():
    good=inspect_binding(fact(),entry())
    assert good['state']=='eligible_existing_source_link'
    assert not good['technical_equivalence_between_purchases']
    wrong_namespace=inspect_binding(fact('S'),entry())
    assert 'catalogue_namespace_or_code_conflict' in wrong_namespace['reasons']
    wrong_unit=inspect_binding(fact(unidadeMedida='caixa com 20 resmas'),entry())
    assert 'unit_or_package_needs_review' in wrong_unit['reasons']
    assert 'package_conflict' in wrong_unit['reasons']
