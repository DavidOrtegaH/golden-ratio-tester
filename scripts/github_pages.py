"""Manage this project's explicitly authorized Pages publication.

Git credentials remain in process memory; neither tokens nor API error bodies
are printed. This script is not shipped in the Pages artifact.
"""
from pathlib import Path
import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request

REPO = 'DavidOrtegaH/golden-ratio-tester'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['enable', 'status', 'dispatch'])
    args = parser.parse_args()
    root = str(Path(__file__).resolve().parent.parent).replace('\\', '/')
    git = ['git', '-c', f'safe.directory={root}']
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'Never'}
    result = subprocess.run(git + ['credential', 'fill'], input='protocol=https\nhost=github.com\n\n', text=True, capture_output=True, env=env)
    if result.returncode:
        raise SystemExit('GitHub authentication required.')
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    secret = fields.get('password')
    if not secret:
        raise SystemExit('GitHub authentication required.')

    def api(path, method='GET', data=None):
        req = urllib.request.Request('https://api.github.com' + path, method=method,
            data=json.dumps(data).encode() if data is not None else None,
            headers={'Authorization': 'Bearer ' + secret, 'Accept': 'application/vnd.github+json',
                     'User-Agent': 'Golden-Ratio-Tester-Pages-publication', 'X-GitHub-Api-Version': '2022-11-28'})
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}

    if api('/user')['login'].lower() != REPO.split('/')[0].lower():
        raise SystemExit('Unexpected authenticated owner; stopped.')
    base = '/repos/' + REPO
    repo = api(base)
    if repo['private'] or repo['full_name'].lower() != REPO.lower():
        raise SystemExit('Expected the authorized public project; stopped.')
    if args.action == 'enable':
        # Preserve the repository's existing Actions security policy.
        policy = api(base + '/actions/permissions')
        print(json.dumps({'actions_enabled': policy.get('enabled'), 'allowed_actions': policy.get('allowed_actions')}))
        try:
            api(base + '/pages')
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            api(base + '/pages', 'POST', {'build_type': 'workflow'})
        else:
            api(base + '/pages', 'PUT', {'build_type': 'workflow'})
        api(base, 'PATCH', {'homepage': 'https://davidortegah.github.io/golden-ratio-tester/'})
    elif args.action == 'dispatch':
        api(base + '/actions/workflows/pages.yml/dispatches', 'POST', {'ref': 'main'})
    pages = api(base + '/pages')
    print(json.dumps({key: pages.get(key) for key in ['html_url', 'status', 'build_type', 'https_enforced']}))
    try:
        runs = api(base + '/actions/workflows/pages.yml/runs?per_page=3')
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        runs = {'workflow_runs': []}
    print(json.dumps([ {key: run.get(key) for key in ['id', 'head_sha', 'status', 'conclusion', 'html_url']} for run in runs['workflow_runs']]))


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as error:
        raise SystemExit(f'GitHub returned HTTP {error.code}; no credentials logged.') from None
