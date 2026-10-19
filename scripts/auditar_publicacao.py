"""Inspect the Git index/history without printing suspected secret values.

Supplement to Gitleaks and manual review, not a certification or a replacement.
Run from any directory: python scripts/auditar_publicacao.py [--history].
Only tracked blobs are read; ignored local credentials are never opened.
"""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, re, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
def git(*args, binary=False):
    result = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, check=True)
    return result.stdout if binary else result.stdout.decode('utf-8').strip()

parser = argparse.ArgumentParser()
parser.add_argument('--history', action='store_true')
args = parser.parse_args()
entries = []
for row in git('ls-files', '--stage').splitlines():
    meta, path = row.split('\t', 1)
    mode, oid, _ = meta.split()
    entries.append(('index', path, mode, oid))
if args.history:
    for commit in git('rev-list', '--all').splitlines():
        for row in git('ls-tree', '-r', commit).splitlines():
            meta, path = row.split('\t', 1)
            mode, kind, oid = meta.split()
            if kind != 'blob':
                raise SystemExit('Unexpected non-blob object. Review locally before uploading.')
            entries.append((commit, path, mode, oid))

rules = {
    'private_key': rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----',
    'github_token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b',
    'openai_key': rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}\b',
    'google_key': rb'\bAIza[A-Za-z0-9_-]{30,}\b',
    'aws_access_key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'credential_uri': rb'(?i)(?:postgres(?:ql)?(?:\+psycopg)?|mongodb(?:\+srv)?|redis|https?)://[^\s:/<>]+:([^\s@/<>]{8,})@',
    'jwt_literal': rb'\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b',
    'service_account_key': rb'"private_key"\s*:\s*"-----BEGIN',
}
forbidden_parts = {'.runtime', '.venv', '_tools', 'node_modules', '.git', '__pycache__', '.pytest_cache', 'dist', 'uploads', 'backups'}
issues = []
reviewed = set()
bytes_scanned = 0
for revision, path, mode, oid in entries:
    p = PurePosixPath(path)
    if set(p.parts) & forbidden_parts or (p.name.startswith('.env') and p.name != '.env.example'):
        issues.append({'revision': revision, 'path': path, 'rule': 'forbidden_path'})
    if mode not in ('100644', '100755'):
        issues.append({'revision': revision, 'path': path, 'rule': 'link_or_submodule'})
    if oid in reviewed:
        continue
    reviewed.add(oid)
    data = git('cat-file', 'blob', oid, binary=True)
    bytes_scanned += len(data)
    for name, pattern in rules.items():
        for match in re.finditer(pattern, data):
            # Exactly documented fake placeholder in .env.example; no generic allowlist.
            if name == 'credential_uri' and p.name == '.env.example' and match.group(1) == b'REPLACE_OUTSIDE_GIT':
                continue
            issues.append({'revision': revision, 'path': path, 'line': data[:match.start()].count(b'\n') + 1, 'rule': name})

expected = json.loads((ROOT/'docs/validacao/integridade-v4.json').read_text(encoding='utf-8'))['modules']
for module in expected:
    path = 'backend/irps_core/' + module['file']
    data = git('show', ':' + path, binary=True)
    if hashlib.sha256(data).hexdigest() != module['sha256']:
        issues.append({'revision': 'index', 'path': path, 'rule': 'core_bytes_changed'})

result = {'scope': 'index_and_all_reachable_history' if args.history else 'index',
          'entries': len(entries), 'unique_blobs': len(reviewed), 'bytes_scanned': bytes_scanned,
          'core_modules': len(expected), 'findings': issues, 'secret_values_printed': False}
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(bool(issues))
