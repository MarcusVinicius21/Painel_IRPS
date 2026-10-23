"""Small synthetic archives for fail-closed campaign validation, never operational data."""
import sys,json,zipfile,hashlib
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from monthly_import_support import validate_manifest,private_path

@pytest.mark.parametrize('month',['2025-09','2026-10','2026-13','invalid'])
def test_campaign_rejects_unapproved_month(month):
    with pytest.raises(ValueError):validate_manifest([],month)

def test_campaign_requires_two_kinds_and_private_files():
    with pytest.raises(ValueError):validate_manifest([],'2026-08')
    with pytest.raises(ValueError):private_path('README.md')

def test_invalid_numeric_is_not_treated_as_a_documented_price():
    from test_monthly_prices import row
    from app.monthly_prices import normalize_row
    with pytest.raises(ValueError,match='invalid_numeric'):
        normalize_row({**row('1'),'preco_unitario':'invalid'},'material','2026-09')

def test_invalid_zip_is_rejected_before_writing(app,login,settings,tmp_path):
    from app.monthly_prices import import_archive
    identity=login().get('/api/v1/auth/context').json();p=tmp_path/'bad.zip';p.write_bytes(b'not a zip')
    with pytest.raises(zipfile.BadZipFile):
        import_archive(settings.owner_database_url.get_secret_value(),identity['org_id'],p,'material','2026-08',hashlib.sha256(p.read_bytes()).hexdigest(),'https://example.invalid/qa.zip')

def test_archive_size_bound_rolls_back(app,login,settings,tmp_path):
    from test_monthly_prices import archive,row
    from app import monthly_prices
    from uuid import uuid4
    identity=login().get('/api/v1/auth/context').json();code=str(int(uuid4().hex[:8],16));p,sha=archive(tmp_path,[{**row(code),'data_compra':'2026-08-12'}])
    args=(settings.owner_database_url.get_secret_value(),identity['org_id'],p,'material','2026-08',sha,'https://example.invalid/qa.zip')
    with pytest.raises(ValueError,match='size rejected'):monthly_prices.import_archive(*args,max_uncompressed_bytes=1)
    result=monthly_prices.import_archive(*args);assert result['accepted_rows']==1
    again=monthly_prices.import_archive(*args);assert again['idempotent']
    other,other_sha=archive(tmp_path,[{**row(code),'data_compra':'2026-08-12','preco_unitario':'99'}],name='other.zip')
    with pytest.raises(ValueError,match='row safety limit'):
        monthly_prices.import_archive(args[0],identity['org_id'],other,'material','2026-08',other_sha,args[-1],max_rows=0)
