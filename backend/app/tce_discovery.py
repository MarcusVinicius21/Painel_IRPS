"""Official-link discovery is evidence of a portal, never proof of an ingestible dataset."""
from html.parser import HTMLParser
from urllib.parse import urlparse,urljoin,parse_qsl
import re

HOSTS=frozenset(('www.tce.mg.gov.br','tce.mg.gov.br','dadosabertos.tce.mg.gov.br',
    'fiscalizandocomtce.tce.mg.gov.br','bancodepreco.tce.mg.gov.br','doc.tce.mg.gov.br'))
FORMATS=('.csv','.json','.xlsx','.ods','.xml','.zip')


def official_link(value,base):
    try:
        url=urlparse(urljoin(base,value));port=url.port
    except (ValueError,TypeError):return None
    if url.scheme!='https' or url.hostname not in HOSTS or url.username or url.password or port not in (None,443):return None
    if any(re.search(r'token|senha|password|session|ticket|auth|api.?key|chave|secret',key,re.I) for key,_ in parse_qsl(url.query)):return None
    if re.search(r'/(?:login|oauth|autenticacao|reset-password)(?:/|$)',url.path,re.I):return None
    return url._replace(fragment='').geturl()


class OfficialLinks(HTMLParser):
    def __init__(self,base):
        super().__init__(convert_charrefs=True);self.base=base;self.links=set();self.text=[];self.hidden=0
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if tag in ('script','style'):self.hidden+=1
        value=values.get('href') if tag=='a' else values.get('src') if tag=='iframe' else None
        url=official_link(value,self.base) if value else None
        if url:self.links.add(url)
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.hidden=max(self.hidden-1,0)
    def handle_data(self,value):
        if not self.hidden:self.text.append(value)


def inspect_html(content,url):
    parser=OfficialLinks(url);parser.feed(content.decode('utf-8','replace'))
    text=' '.join(parser.text)
    return {'official_links':sorted(parser.links),
        'download_candidates':[u for u in sorted(parser.links) if urlparse(u).path.lower().endswith(FORMATS)],
        'certificate_notice_present':bool(re.search(r'certificad[oa].{0,30}digital',text,re.I|re.S)),
        'schema_verified':False,'license_verified':False,'municipal_period_verified':None,
        'connector_state':'connector_unverified','records_imported':None,
        'limitation':'Página ou link não comprova arquivo acessível, esquema, licença ou cobertura municipal.'}


def dataset_decisions(probes):
    # An institutional announcement is not a data contract. An adapter may only
    # ingest after a specific resource/schema/license has separately been verified.
    return [{'dataset':name,'state':'connector_unverified','resource_url':None,'format':None,
        'schema':None,'license':None,'municipality_identity_mapping':None,'period_coverage':None,
        'available_portal_evidence':sum(p.get('http_status')==200 for p in probes)}
        for name in ('municipal_procurements','municipal_contracts','municipal_expenditure')]
