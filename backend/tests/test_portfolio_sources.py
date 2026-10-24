from app.portfolio_sources import sources


class NoNetwork:
    org_id='isolated_qa'
    def require(self,p):assert p=='read'
    @property
    def db(self):return self
    def all(self,query,params):
        assert 'f.org_id=:o' in query and "b.government_level='M'" in query
        return []


def test_source_outage_is_explicit_and_not_a_financial_or_market_claim():
    r=sources(NoNetwork());rows={x['provider']:x for x in r['records']}
    assert rows['TCE_MG']['state']=='blocked'
    assert rows['PORTAL_TIMOTEO']['state']=='blocked'
    assert rows['PORTAL_IPATINGA']['state']=='needs_review'
    assert rows['COMPRAS_GOV']['origin']=='national_price_history'
    assert not rows['CATMAT_COM_BR']['official']
    assert not r['external_dependencies_required_to_open'] and r['new_financial_facts']==0
    assert r['municipal_purchase_completeness'] is None
