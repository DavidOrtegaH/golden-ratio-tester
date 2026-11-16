"""One-off authorized repository rename. Credentials stay in process memory."""
import json
from pathlib import Path
import os
import subprocess
import urllib.error
import urllib.request


def main():
    root = str(Path(__file__).resolve().parent.parent).replace('\\', '/')
    git = ['git', '-c', f'safe.directory={root}']
    environment = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'Never'}
    result = subprocess.run(git + ['credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                            text=True, capture_output=True, env=environment)
    if result.returncode:
        raise SystemExit('GitHub authentication is required.')
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    secret = fields.get('password')
    if not secret:
        raise SystemExit('GitHub authentication is required.')

    def api(path, data=None):
        request = urllib.request.Request('https://api.github.com' + path,
            data=json.dumps(data).encode() if data else None, method='PATCH' if data else 'GET',
            headers={'Authorization': 'Bearer ' + secret, 'Accept': 'application/vnd.github+json',
                     'User-Agent': 'Golden-Ratio-Tester-repository-maintenance'})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    owner, previous, desired = 'DavidOrtegaH', 'proporcion-aurea', 'golden-ratio-tester'
    if api('/user')['login'].lower() != owner.lower():
        raise SystemExit('Authenticated owner does not match; no changes made.')
    repository = api(f'/repos/{owner}/{previous}')
    if repository['owner']['login'].lower() != owner.lower():
        raise SystemExit('Unexpected repository owner; no changes made.')
    if repository['name'] != desired:
        try:
            api(f'/repos/{owner}/{desired}')
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
        else:
            raise SystemExit('Target name already exists; no changes made.')
        repository = api(f'/repos/{owner}/{previous}', {
            'name': desired,
            'description': 'Golden Ratio Tester — bilingual image geometry analysis. Django, OpenCV, TypeScript + Stimulus. MIT.',
        })
    subprocess.run(git + ['remote', 'set-url', 'origin', repository['clone_url']], check=True)
    print(repository['html_url'])


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as error:
        raise SystemExit(f'GitHub returned HTTP {error.code}; credentials were not logged.') from None
