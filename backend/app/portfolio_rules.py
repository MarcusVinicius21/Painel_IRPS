"""Conservative, versioned technical triage; never commercial authorization.

Exact product headings plus explicit purpose narrow candidates. A broad class or
textual mention cannot establish technical identity across purchases.
"""
import re,unicodedata
VERSION='consormulti-fcp-2026-10-23-v1'
DIRECT='DIRECT_TECHNICAL';REVIEW='NEEDS_TECH_REVIEW';INDIRECT='INDIRECT';EXCLUDED='EXCLUDED'


def fold(value):
    text=unicodedata.normalize('NFKD',str(value or '')).upper()
    return re.sub(r'\s+',' ',''.join(c for c in text if not unicodedata.combining(c))).strip()


# Each group has its own inclusion/exclusion contract. No inherited whitelist.
GROUPS=[
 ('01','Compra de veículos','Bens: automóveis, utilitários, ônibus e caminhões'),
 ('02','Material escolar','Artigos com finalidade escolar explícita'),
 ('03','Uniforme escolar','Peças ou kits com finalidade escolar explícita'),
 ('04','Móveis escolares','Mobiliário escolar especificado'),
 ('05','Consultoria em educação','Consultoria e capacitação com escopo educacional'),
 ('06','Material didático','Livros e materiais pedagógicos identificados'),
 ('07','Catracas para alunos (biometria)','Controle de acesso escolar; finalidade a conferir'),
 ('08','Cartão de gestão de frota','Gestão e abastecimento de frota; serviços'),
 ('09','Casqueamento de estrada — termo a confirmar','Cascalhamento; exige confirmação institucional do termo'),
 ('10','Cesta básica','Kit/cesta; alimentos avulsos exigem composição comprovada'),
 ('11','Merenda escolar','Objeto e composição de alimentação escolar'),
 ('12','Uniforme de funcionários','Uniforme profissional; finalidade explícita'),
 ('13','Medicamentos e material hospitalar','Apresentação/concentração e subgrupo precisam de revisão'),
 ('14','Aluguel de frota, máquinas e caminhões','Locação; distinta da compra do bem'),
 ('15','Café','Café como produto; exclui equipamentos e utensílios'),
 ('16','Saúde ocupacional','Medicina e segurança do trabalho'),
 ('17','Material de informática','Equipamentos e suprimentos por especificação'),
 ('18','Asfalto e bloquete','Material e execução de pavimentação separados'),
 ('19','Dedetização','Serviço de controle de pragas; não produtos químicos'),
 ('20','Placas, semáforos e trânsito','Sinalização viária explícita'),
]


def classify(entry):
    """Return scoped candidates, including explicit difficult negatives.

    No matches means EXCLUDED from this priority rule version, not deletion from
    the national catalogue. Official namespace/snapshot must be supplied by caller.
    """
    kind=entry.get('kind');name=fold(entry.get('name'));pdm=fold(entry.get('pdm_name'))
    head=pdm or name.split(',')[0].strip('" ');head=head.strip('" ')
    material=kind=='CATMAT';service=kind=='CATSER';result=[]
    def add(group,state,subgroup,reason):
        result.append({'group_id':group,'technical_status':state,'subgroup':subgroup,'reason':reason,
            'commercial_status':'OUT_OF_PORTFOLIO' if state==EXCLUDED else 'COMMERCIAL_PENDING',
            'rule_version':VERSION,'cross_purchase_equivalence':False,
            'multiple_group_reason':None})
    def has(pattern):return bool(re.search(pattern,name))
    vehicles={'AUTOMOVEL','VEICULO UTILITARIO','CAMINHAO','ONIBUS','MICROONIBUS','MICRO-ONIBUS','VEICULO VAN','VAN'}
    if material and head in vehicles:
        add('01',DIRECT,'compra_bem','Cabeçalho/PDM de veículo completo; compra distinta de serviço.')
    elif has(r'\b(AUTOMOVEL|VEICULO|CAMINHAO|ONIBUS)\b') and has(r'\b(PECA|PECAS|ACESSORIO|MANUTENCAO|LOCACAO)\b'):
        add('01',EXCLUDED,'fora_compra_bem','Peça, acessório, manutenção ou locação não é compra de veículo completo.')
    if material and has(r'\bESCOLAR\b') and head in {'LAPIS','CANETA ESFEROGRAFICA','BORRACHA','CADERNO','TESOURA','APONTADOR LAPIS','ESTOJO ESCOLAR','MOCHILA ESCOLAR','KIT MATERIAL ESCOLAR'}:
        add('02',DIRECT,'artigo_escolar','Artigo identificado e finalidade escolar expressa.')
    if material and (head=='UNIFORME ESCOLAR' or has(r'\bUNIFORME ESCOLAR\b')):
        add('03',DIRECT,'uniforme_escolar','Finalidade escolar explicitada; especificação individual preservada.')
    if material and head in {'CARTEIRA ESCOLAR','CONJUNTO ESCOLAR','MESA ESCOLAR','CADEIRA ESCOLAR'}:
        add('04',DIRECT,'mobiliario_escolar','Mobiliário escolar completo identificado pelo cabeçalho/PDM.')
    if service and has(r'\b(CONSULTORIA|ASSESSORIA|CAPACITACAO)\b') and has(r'\b(EDUCACAO|EDUCACIONAL|PEDAGOGICA|ENSINO)\b'):
        add('05',REVIEW,'servico_educacional','Escopo educacional explícito; entregáveis e contratação exigem revisão.')
    if material and head in {'LIVRO DIDATICO','MATERIAL DIDATICO','KIT PEDAGOGICO','JOGO PEDAGOGICO','LIVRO PARADIDATICO'}:
        add('06',DIRECT,'material_pedagogico','Finalidade didática explícita no cabeçalho/PDM.')
    if has(r'\bCATRACA\b'):
        if has(r'\b(CHAVE|FERRAMENTA|MICROMETRO|SOQUETE|TORQUIMETRO)\b'):
            add('07',EXCLUDED,'ferramenta','Catraca mecânica/ferramenta não é controle de acesso escolar.')
        elif has(r'\b(ACESSO|BIOMETRI|ALUNO|ESCOLAR|IDENTIFICACAO)'):
            add('07',REVIEW,'controle_acesso','Equipamento de acesso candidato; aplicação escolar e biometria exigem conferência.')
    if service and has(r'\b(FROTA|VEICULOS)\b') and has(r'\b(GERENCIAMENTO|GESTAO|CARTAO|ABASTECIMENTO)\b'):
        add('08',REVIEW,'gestao_frota','Serviço de gestão/abastecimento; não é aquisição dos veículos.')
    if has(r'\b(CASCALHAMENTO|CASQUEAMENTO)\b'):
        if has(r'\b(ESTRADA|VIAS|RODOVIA|PAVIMENTACAO)\b'):
            add('09',REVIEW,'termo_institucional_pendente','O termo original precisa de confirmação do gestor; sem aprovação automática.')
        else:add('09',EXCLUDED,'fora_estrada','Casqueamento sem contexto de estrada não é correspondência técnica.')
    if (material and head in {'CESTA BASICA','CESTA BASICA - GENEROS ALIMENTICIOS','CESTA DE ALIMENTOS','KIT CESTA BASICA'}
        or service and name.startswith('FORNECIMENTO DE CESTA BASICA DE ALIMENTO')):
        add('10',REVIEW,'kit_cesta','Cesta identificada; composição e quantidades precisam ser conferidas.')
    if has(r'\b(MERENDA ESCOLAR|ALIMENTACAO ESCOLAR|REFEICAO ESCOLAR)\b'):
        add('11',REVIEW,'alimentacao_escolar','Finalidade escolar expressa; cardápio/composição e apresentação pendentes.')
    if material and head in {'UNIFORME PROFISSIONAL','UNIFORME ADMINISTRATIVO'}:
        add('12',DIRECT,'uniforme_profissional','Finalidade profissional explícita; sem equivalência entre peças.')
    if material and (has(r'\b(CONCENTRACAO|DOSAGEM)\s*:') and has(r'\b(COMPRIMIDO|CAPSULA|SOLUCAO INJETAVEL|POMADA|SUSPENSAO ORAL)\b')
        or head in {'SERINGA','AGULHA HIPODERMICA','CATETER','EQUIPO','LUVA CIRURGICA','GAZE','ATADURA','COMPRESSA GAZE'}):
        add('13',REVIEW,'medicamento' if has(r'\b(CONCENTRACAO|DOSAGEM)\s*:') else 'material_hospitalar',
            'Apresentação, concentração e uso médico precisam de revisão específica; não agrega preços de outros códigos.')
    if service and has(r'\b(LOCACAO|ALUGUEL)\b') and has(r'\b(VEICULO|VEICULOS|AUTOMOVEL|CAMINHAO|ONIBUS|MAQUINAS PESADAS|MAQUINA RODOVIARIA|TRATOR|RETROESCAVADEIRA)\b'):
        add('14',REVIEW,'locacao','Locação de frota ou máquina rodoviária explicitada; conferir prazo e operador.')
    if material and head in {'CAFE','CAFE TORRADO','CAFE SOLUVEL'}:
        if has(r'\b(TORRADO|MOIDO|SOLUVEL|GRAO|GRAOS|DESCAFEINADO)\b'):
            add('15',DIRECT,'cafe_produto','Produto café com apresentação identificável; cada código permanece separado.')
        else:add('15',REVIEW,'cafe_produto','Produto café; apresentação ainda requer conferência.')
    elif has(r'\b(CAFE|CAFETEIRA)\b') and head not in {'CAFE','CAFE TORRADO','CAFE SOLUVEL'}:
        add('15',INDIRECT,'fora_cafe_produto','Equipamento, utensílio, cor ou menção indireta não comprova fornecimento de café.')
    if service and has(r'\b(MEDICINA DO TRABALHO|SAUDE OCUPACIONAL|SEGURANCA DO TRABALHO|EXAME OCUPACIONAL)\b'):
        add('16',REVIEW,'saude_ocupacional','Objeto ocupacional explícito; escopo e exames exigem conferência.')
    if material and head in {'MICROCOMPUTADOR','COMPUTADOR','NOTEBOOK','IMPRESSORA','NOBREAK','SWITCH','ROTEADOR','TECLADO MICROCOMPUTADOR','MOUSE COMPUTADOR'}:
        add('17',REVIEW,'equipamento_informatica','Equipamento identificado; modelo, capacidade e oferta comercial pendentes.')
    if material and head in {'ASFALTO','BLOQUETE','BLOCO PAVIMENTO','EMULSAO ASFALTICA','CIMENTO ASFALTICO'}:
        add('18',REVIEW,'material_pavimentacao','Material de pavimentação; unidade e especificação precisam de conferência.')
    elif service and has(r'\b(PAVIMENTACAO|ASFALTAMENTO)\b'):
        add('18',REVIEW,'execucao_pavimentacao','Execução de serviço/obra separada do material.')
    if service and has(r'\b(DEDETIZACAO|DESINSETIZACAO|DESRATIZACAO|CONTROLE DE PRAGAS)\b'):
        if has(r'\b(MANUTENCAO|EQUIPAMENTO|LOCACAO)\b'):
            add('19',EXCLUDED,'fora_controle_pragas','Manutenção/locação de equipamento não é prestação do controle de pragas.')
        else:add('19',DIRECT,'controle_pragas','Serviço de controle de pragas explicitado; não inclui produtos químicos isolados.')
    if material and (head=='SEMAFORO' or has(r'\b(PLACA|SINALIZACAO)\b') and has(r'\b(TRANSITO|VIARIA|RODOVIARIA)\b')):
        add('20',REVIEW,'sinalizacao_viaria','Uso viário explícito; material, dimensões e normas precisam de conferência.')
    if len(result)>1:
        for row in result:row['multiple_group_reason']='Regras independentes; exclusões e candidatos não implicam equivalência ou oferta.'
    return result
