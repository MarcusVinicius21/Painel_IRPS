import pytest
from app.portfolio_rules import classify,DIRECT,REVIEW,EXCLUDED,INDIRECT,GROUPS


def entries(name,kind='CATMAT',pdm=''):
    return {r['group_id']:r for r in classify({'name':name,'kind':kind,'pdm_name':pdm})}


@pytest.mark.parametrize('name,group', [('AUTOMÓVEL, NOME: AUTOMÓVEL','01'),
    ('CADERNO, USO: ESCOLAR','02'),('UNIFORME ESCOLAR','03'),('CARTEIRA ESCOLAR','04'),
    ('LIVRO DIDÁTICO','06'),('UNIFORME PROFISSIONAL','12'),('CAFÉ, TIPO: TORRADO, APRESENTAÇÃO: MOÍDO','15')])
def test_explicit_technical_heads_keep_commercial_pending(name,group):
    r=entries(name)[group]
    assert r['technical_status']==DIRECT and r['commercial_status']=='COMMERCIAL_PENDING'
    assert not r['cross_purchase_equivalence']


@pytest.mark.parametrize('name,group', [('PEÇAS AUTOMÓVEL','01'),('CHAVE CATRACA','07'),
    ('TESOURA PARA CASQUEAMENTO DE OVINOS','09')])
def test_known_negatives_excluded(name,group):
    assert entries(name)[group]['technical_status']==EXCLUDED


def test_food_paper_clothes_and_generic_electronics_are_not_blanket_inclusions():
    for name in ['ARROZ TIPO 1','FEIJÃO','PAPEL A4','CAMISA SOCIAL','PLACA ELETRÔNICA','FUNGICIDA']:
        assert entries(name)=={}
    assert entries('CAFETEIRA ELÉTRICA')['15']['technical_status']==INDIRECT
    assert entries('TELHA COR CAFÉ')['15']['technical_status']==INDIRECT


@pytest.mark.parametrize('name,kind,group', [('CONSULTORIA EDUCACIONAL','CATSER','05'),
    ('CATRACA CONTROLE DE ACESSO BIOMÉTRICO','CATMAT','07'),('GESTÃO DE FROTA','CATSER','08'),
    ('CASCALHAMENTO DE ESTRADA','CATSER','09'),('CESTA BÁSICA','CATMAT','10'),
    ('SERVIÇO ALIMENTAÇÃO ESCOLAR','CATSER','11'),('SERINGA','CATMAT','13'),
    ('LOCAÇÃO DE VEÍCULOS','CATSER','14'),('MEDICINA DO TRABALHO','CATSER','16'),
    ('NOTEBOOK','CATMAT','17'),('EMULSÃO ASFÁLTICA','CATMAT','18'),('SEMÁFORO','CATMAT','20')])
def test_ambiguous_contracts_require_review(name,kind,group):
    assert entries(name,kind)[group]['technical_status']==REVIEW


def test_all_twenty_groups_and_namespace_preserved():
    assert len(GROUPS)==20 and len({g[0] for g in GROUPS})==20
    assert '19' in entries('DEDETIZAÇÃO','CATSER')
    assert '19' not in entries('DEDETIZAÇÃO','CATMAT')
    assert '01' not in entries('AUTOMÓVEL','CATSER')
    assert '14' not in entries('AUTOMÓVEL','CATMAT')
    a=entries('MEDICAMENTO CONCENTRAÇÃO: 10 MG COMPRIMIDO')['13']
    b=entries('MEDICAMENTO CONCENTRAÇÃO: 20 MG COMPRIMIDO')['13']
    assert not a['cross_purchase_equivalence'] and not b['cross_purchase_equivalence']


def test_stratified_real_catalogue_negatives_not_enrolled_as_services():
    assert '14' not in entries('LOCAÇÃO / MANUTENÇÃO MÁQUINA HEMODIÁLISE','CATSER')
    assert entries('MANUTENÇÃO EQUIPAMENTO - DEDETIZAÇÃO / PULVERIZAÇÃO','CATSER')['19']['technical_status']==EXCLUDED
    assert entries('CESTA BÁSICA - GÊNEROS ALIMENTÍCIOS')['10']['technical_status']==REVIEW
    assert entries('FORNECIMENTO DE CESTA BASICA DE ALIMENTO "INATIVO"','CATSER')['10']['technical_status']==REVIEW
