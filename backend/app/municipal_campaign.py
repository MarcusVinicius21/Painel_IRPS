"""Deterministic scope, distinct from observed source coverage and purchase facts."""
from datetime import date
import hashlib
import json
import re

SOURCES = ('PNCP', 'COMPRAS_GOV', 'IBGE', 'INEP', 'SICONFI', 'TCE', 'PORTAL_MUNICIPAL', 'TRANSFEREGOV', 'DIARIO_OFICIAL')


def closed_months(start: date, end: date) -> list[str]:
    if start.day != 1 or end < start:
        raise ValueError('Use um período de meses completos.')
    following = date(end.year + (end.month == 12), end.month % 12 + 1, 1)
    if (following - end).days != 1:
        raise ValueError('O último mês precisa estar completo.')
    months = []
    current = start
    while current <= end:
        months.append(current.strftime('%Y-%m'))
        current = date(current.year + (current.month == 12), current.month % 12 + 1, 1)
    return months


def freeze_scope(rows: list[dict], start: date, end: date) -> dict:
    cities = []
    seen = set()
    for row in rows:
        code = str(row['ibge']).strip()
        if not re.fullmatch(r'\d{7}', code) or code in seen:
            raise ValueError('Código IBGE inválido ou repetido.')
        if not re.fullmatch(r'[A-Z]{2}', row['uf']) or not row['name'].strip():
            raise ValueError('Município sem identidade suficiente.')
        seen.add(code)
        cities.append({'ibge': code, 'name': row['name'].strip(), 'uf': row['uf']})
    scope = {'schema_version': 1, 'municipalities': sorted(cities, key=lambda x: x['ibge']),
             'months': closed_months(start, end), 'sources': list(SOURCES)}
    scope['sha256'] = hashlib.sha256(json.dumps(scope, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return scope


def pending_matrix(scope: dict) -> list[dict]:
    # A plan does not reclassify existing observations or establish temporal completeness.
    return [{'municipality_ibge': city['ibge'], 'month': month, 'source': source,
             'state': 'pending', 'observed_records': None, 'completeness_percent': None}
            for city in scope['municipalities'] for month in scope['months'] for source in scope['sources']]


def verify_ibge(city: dict, response: dict) -> None:
    region = response.get('microrregiao') or {}
    uf = (region.get('mesorregiao') or {}).get('UF')
    if not uf:
        uf = ((response.get('regiao-imediata') or {}).get('regiao-intermediaria') or {}).get('UF')
    if str(response.get('id')) != city['ibge'] or response.get('nome') != city['name'] or (uf or {}).get('sigla') != city['uf']:
        raise ValueError('A identidade do cadastro diverge da resposta oficial do IBGE.')


def buyer_identity(buyer: dict, record: dict) -> dict:
    """Verify fiscal identity separately from geography and institutional subtype."""
    entity, unit = record.get('orgaoEntidade') or {}, record.get('unidadeOrgao') or {}
    cnpj = str(entity.get('cnpj') or '')
    matching = bool(re.fullmatch(r'\d{14}', cnpj)) and all((
        cnpj == buyer.get('cnpj'), str(unit.get('codigoUnidade') or '') == buyer.get('unit_code'),
        str(unit.get('codigoIbge') or '') == buyer.get('municipality_ibge')))
    sphere, power = entity.get('esferaId'), entity.get('poderId')
    institution = {'M': 'municipal', 'E': 'estadual', 'F': 'federal', 'D': 'distrital'}.get(sphere)
    branch = {'L': 'legislativo', 'E': 'executivo', 'J': 'judiciario'}.get(power)
    return {'state': 'verified' if matching else 'ORGAO_NAO_VERIFICADO',
            'cnpj': cnpj if matching else None, 'cnpj_root': cnpj[:8] if matching else None,
            'unit_code': str(unit.get('codigoUnidade')) if matching else None,
            'municipality_ibge': str(unit.get('codigoIbge')) if matching else None,
            'sphere': institution if matching else None, 'power': branch if matching else None,
            'source_sphere': sphere, 'source_power': power,
            'municipal_buyer': sphere == 'M' if matching and institution else None,
            'institutional_subtype': None,
            'limitation': 'Identidade fiscal e localização não comprovam subtipo institucional, fundo, autarquia ou vínculo com a prefeitura.'}
