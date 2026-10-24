from datetime import datetime
from app.catalogue_manual import allowed_time,preview
import pytest,hashlib

def test_saturday_morning_only_manual_policy():
    assert allowed_time(datetime(2026,10,24,9,0))
    assert not allowed_time(datetime(2026,10,24,12,0))
    assert not allowed_time(datetime(2026,10,23,10,0))

def test_preview_rejects_duplicate_or_changed_file(tmp_path):
    p=tmp_path/'material.csv';p.write_text('codigoItem;descricaoItem;statusItem\n1;CAFÉ;True\n',encoding='utf-8')
    h=hashlib.sha256(p.read_bytes()).hexdigest();r=preview(p,'CATMAT',h,{'1':('CAFÉ',True),'2':('OUTRO',True)})
    assert r['unchanged']==1 and r['missing_from_new']==1 and r['destructive_deletions']==0
    with pytest.raises(ValueError):preview(p,'CATMAT','0'*64,{})
    p.write_text('codigoItem;descricaoItem;statusItem\n1;CAFÉ;True\n1;CAFÉ;True\n',encoding='utf-8')
    with pytest.raises(ValueError):preview(p,'CATMAT',hashlib.sha256(p.read_bytes()).hexdigest(),{})
