"""Pure tests: no seed, operational database, network, or Git writes."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('municipal_checkpoint', Path(__file__).resolve().parents[2] / 'scripts/municipal_checkpoint.py')
checkpoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoint)


def test_ledger_ignores_previous_campaign_and_retains_order():
    result = checkpoint.entries('abc\tirps(R01): previous\ndef\tirps(M00_01): baseline\nghi\tirps(X01): inventory')
    assert [(x['id'], x['sha']) for x in result] == [('M00_01', 'def'), ('X01', 'ghi')]


def test_duplicate_task_is_not_silently_reapplied():
    with pytest.raises(ValueError, match='Duplicate task'):
        checkpoint.entries('abc\tirps(M00_01): first\ndef\tirps(M00_01): duplicate')


def test_atomic_state_retains_unicode_and_replaces_once(tmp_path):
    path = tmp_path / 'private' / 'ledger.json'
    checkpoint.write_atomic(path, [{'id': 'M00_01', 'status': 'PASS'}])
    checkpoint.write_atomic(path, [{'id': 'M01_01', 'note': 'Não consultado'}])
    assert 'Não consultado' in path.read_text(encoding='utf-8')
    assert not path.with_suffix('.json.tmp').exists()
