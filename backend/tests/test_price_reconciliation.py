"""Synthetic, supplier-free source differences; no external API access."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from conciliar_api_arquivo_precos import reconcile,identity

def test_large_ids_and_leading_zero_purchase_are_preserved():
    assert identity('0007001807001672026',123456789012345678901)=='0007001807001672026:123456789012345678901'
    with pytest.raises(ValueError):identity('x',123.0)

def test_all_rows_are_compared_without_merging_or_guessing_cause():
    api=[dict(purchase='0001',item=i,date='2026-09-01',quantity=1.0,price=2.0) for i in range(223)]
    csv=[{**row,'quantity':'1','price':'2.00'} for row in api]+[dict(purchase='0002',item=1,date='2026-09-02',quantity=None,price=None)]
    result=reconcile(api,csv)
    assert result['common']==223 and result['only_csv']==['0002:1'] and not result['changed_fields'] and not result['sources_merged']

def test_duplicates_and_missing_values_do_not_become_new_purchases_or_zero():
    row=dict(purchase='p',item='i',date='2026-09-01',quantity=None,price=None)
    with pytest.raises(ValueError,match='Repeated identity'):reconcile([row,row],[row])
    result=reconcile([row],[{**row,'quantity':0,'price':0}])
    assert result['changed_fields']==[{'key':'p:i','fields':['quantity','price']}]
