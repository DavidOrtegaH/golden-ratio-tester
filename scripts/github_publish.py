"""Publish the explicitly authorized public repository using Git's credential helper.

Credentials remain in memory and are never printed, persisted, or put in argv.
Run this manually; it is not part of the application or CI.
"""
import json
import os
import subprocess
import urllib.request
import urllib.error

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
git = ['git', '-c', f'safe.directory={root}']
environment = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'Never'}
credential = subprocess.run(git + ['credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                            text=True, capture_output=True, env=environment)
if credential.returncode:
    raise SystemExit('No usable GitHub credential in Git credential manager. Authentication is required.')
fields = dict(line.split('=', 1) for line in credential.stdout.splitlines() if '=' in line)
token = fields.get('password')
if not token:
    raise SystemExit('GitHub authentication is required.')


def api(path, data=None):
    req = urllib.request.Request('https://api.github.com' + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'User-Agent': 'golden-ratio-tester-repository-setup'})
    with urllib.request.urlopen(req) as response:
        return json.load(response)


try:
    profile = api('/user')
    owner = profile['login']
    if owner.lower() != 'davidortegah':
        raise SystemExit('Authenticated account does not match the requested author; publication stopped.')
    name = 'proporcion-aurea'
    try:
        existing = api(f'/repos/{owner}/{name}')
        raise SystemExit('Repository name already exists; inspect before linking or modifying it.')
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    repo = api('/user/repos', {'name': name, 'private': False,
        'description': 'Golden Ratio Tester: geometric golden-ratio image analysis. Django, OpenCV, Bootstrap + Sass. ES/EN. SpecDD.',
        'auto_init': False})
    subprocess.run(git + ['remote', 'add', 'origin', repo['clone_url']], check=True)
    subprocess.run(git + ['push', '-u', 'origin', 'main', 'develop', 'feature', 'release'], check=True, env=environment)
    print(repo['html_url'])
except urllib.error.HTTPError as error:
    raise SystemExit(f'GitHub returned HTTP {error.code}; no credentials were logged.') from None
