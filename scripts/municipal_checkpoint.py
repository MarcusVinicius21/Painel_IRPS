"""Rebuild a private, resumable task ledger from local commits; never publishes."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = '0bdf3d96bcaa46a689d6327d2910c43a56b2ba62'
TASK_PATTERN = re.compile(r'^irps\((M\d{2}_\d{2}|D\d{2}|X\d{2})\): ')


def entries(log: str) -> list[dict]:
    result = []
    seen = set()
    for line in log.splitlines():
        sha, subject = line.split('\t', 1)
        match = TASK_PATTERN.match(subject)
        if not match:
            continue
        task = match[1]
        if task in seen:
            raise ValueError(f'Duplicate task commit: {task}')
        seen.add(task)
        result.append({'id': task, 'sha': sha, 'subject': subject})
    return result


def write_atomic(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def rebuild(root: Path = ROOT) -> list[dict]:
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args]).decode('utf-8').strip()
    branch = git('branch', '--show-current')
    if branch != 'feat/cobertura-municipal-12m-2026-10-23':
        raise ValueError('Unexpected branch; no checkpoint written.')
    subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', BASE, 'HEAD'], check=True)
    tasks = entries(git('log', '--reverse', '--format=%H%x09%s', BASE + '..HEAD'))
    for task in tasks:
        path = (f'docs/implementacao/municipal/{task["id"]}.md' if task['id'].startswith('M')
                else f'docs/integracoes_github/{task["id"]}.md')
        # Status belongs to the committed report, not to an uncommitted claim.
        report = git('show', task['sha'] + ':' + path)
        status = re.search(r'^Status: (PASS|PARTIAL|BLOCKED)$', report, re.M)
        if not status:
            raise ValueError(f'Missing explicit committed status for {task["id"]}')
        task.update(status=status[1], report=path)
    write_atomic(root / '.runtime/irps-municipal/ledger.json', tasks)
    return tasks


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(rebuild(), ensure_ascii=False, indent=2))
