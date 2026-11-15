"""Run backend adapters against controlled HTTP loopback fixtures, never real AI.

Each case uses the backend checkout's own virtualenv in a separate subprocess.
No database is opened and no .env file is loaded. Request counts/no retries must
also be confirmed against the local simulation's request log.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


MODEL = 'gemini-3.5-flash-lite'
FAILURE_MODELS = ('mock-quota', 'mock-unavailable', 'mock-timeout',
                  'mock-malformed', 'mock-truncated')
KINDS = {
    'identity': ('access_anomalies',),
    'projects': ('roles', 'access_revocation', 'teams', 'skills_map', 'training'),
    'backlog': ('initial_backlog',),
}
ID = '00000000-0000-4000-8000-000000000001'
SYNTHETIC_KEY = 'test-only-key'


def local_base_url(value):
    try:
        url = urlsplit(value)
        if (url.scheme != 'http' or url.hostname not in {'127.0.0.1', 'localhost', '::1'}
                or url.username is not None or url.password is not None
                or url.query or url.fragment or '?' in value or '#' in value
                or url.path.rstrip('/') != '/v1beta' or '%' in value or '\\' in value
                or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value)):
            raise ValueError
        _ = url.port
    except ValueError:
        raise argparse.ArgumentTypeError('Use HTTP loopback /v1beta without credentials') from None
    return value.rstrip('/')


def backend_python(path):
    checkout = Path(path).resolve()
    if not (checkout / 'src').is_dir():
        raise ValueError('Configure each backend checkout with src/ and its own .venv')
    for relative in ('.venv/Scripts/python.exe', '.venv/bin/python'):
        executable = checkout / relative
        if executable.is_file():
            return checkout, executable
    raise ValueError('Configure each backend checkout with src/ and its own .venv')


def synthetic_context(backend):
    if backend == 'identity':
        return {'users': [{'id': ID, 'is_active': True}],
                'audit_events': [{'id': ID, 'action': 'login.success', 'user_id': ID}]}
    project = {'id': ID, 'owner_id': ID, 'description': 'Projeto sintético sem ação fundamentada',
               'technology_stack': [], 'technical_requirements': [], 'soft_skills': []}
    if backend == 'projects':
        return {'project': project, 'candidates': [], 'members': [ID], 'teams': [],
                'roles': [{'key': 'developer'}], 'allocations': [], 'work_items': [],
                'evidence': ['project:' + ID],
                'access_usage': {'status': 'unknown', 'inactive_user_ids': []}}
    return {'project': project, 'items': []}


def worker(backend, checkout, base_url, model, kind):
    """Imports only one backend and validates its real adapter's public result."""
    sys.path.insert(0, str(Path(checkout) / 'src'))
    common = {'_env_file': None, 'database_url': 'sqlite:///:memory:',
              'ai_provider': 'gemini', 'ai_simulated': False,
              'gemini_api_key': SYNTHETIC_KEY, 'gemini_model': model,
              'gemini_api_base_url': base_url, 'gemini_timeout_seconds': 1}
    context = synthetic_context(backend)
    close = lambda: None
    if backend == 'identity':
        from mod1_auth.ai_adapter import AIAdapter
        from mod1_auth.config import Settings
        from mod1_auth.identity_service import IdentityError

        adapter = AIAdapter(Settings(**common, jwt_private_key_path=Path('unused-synthetic.pem'),
                                     jwt_issuer='synthetic-smoke'))
        invoke = lambda: adapter.generate(context)
        expected_error = IdentityError
        allowed_detail = 'Recommendation provider unavailable'
        metadata = lambda result: (adapter.provider, adapter.model, adapter.simulated)
    elif backend == 'projects':
        from projects_service.access_domain import AccessError
        from projects_service.config import Settings
        from projects_service.integrations import AIClient

        adapter = AIClient(Settings(**common))
        invoke = lambda: adapter.generate(kind, context)
        close = adapter.client.close
        expected_error = AccessError
        allowed_detail = 'Recommendation provider returned unavailable or invalid output'
        metadata = lambda result: (result['provider'], result['model'], result['simulated'])
    else:
        import httpx

        from backlog_service.config import Settings
        from backlog_service.domain import DependencyUnavailable
        from backlog_service.gemini_adapter import GeminiProposalProvider

        client = httpx.Client(timeout=1, follow_redirects=False, trust_env=False)
        adapter = GeminiProposalProvider(client, Settings(**common))
        invoke = lambda: adapter.generate(kind, context)
        close = client.close
        expected_error = DependencyUnavailable
        allowed_detail = 'Recommendation provider unavailable or invalid'
        metadata = lambda result: (adapter.provider, adapter.model, adapter.simulated)
    try:
        try:
            result = invoke()
        except expected_error as error:
            detail = getattr(error, 'detail', str(error))
            if (model not in FAILURE_MODELS or detail != allowed_detail
                    or getattr(error, 'status', 503) != 503):
                raise ValueError('Unexpected provider failure') from None
            return {'backend': backend, 'kind': kind, 'model': model, 'outcome': 'typed-error',
                    'error_type': type(error).__name__, 'status': 503, 'sanitized': True}
        if model != MODEL or result.get('suggestions') != []:
            raise ValueError('Expected an empty controlled proposal')
        provider, returned_model, simulated = metadata(result)
        if provider != 'gemini' or returned_model != model or simulated is not False:
            raise ValueError('Unexpected provider metadata')
        if not result.get('summary') or not result.get('justification'):
            raise ValueError('Missing required explanation')
        return {'backend': backend, 'kind': kind, 'model': model, 'outcome': 'empty-success',
                'provider': provider, 'simulated': simulated}
    finally:
        close()


def run_case(backend, checkout, executable, base_url, model, kind):
    # Do not inherit credentials, proxy settings, PYTHONPATH, or application config.
    environment = {name: os.environ[name] for name in
                   ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH') if name in os.environ}
    environment['PYTHONUTF8'] = '1'
    command = [str(executable), '-I', str(Path(__file__).resolve()), '--worker', backend,
               '--backend-path', str(checkout), '--base-url', base_url,
               '--model', model, '--kind', kind]
    with tempfile.TemporaryDirectory(prefix='gemini-smoke-') as working:
        completed = subprocess.run(command, cwd=working, env=environment, capture_output=True,
                                   text=True, encoding='utf-8', timeout=15)
    # Never forward subprocess stderr, exception payloads, or provider responses.
    if completed.returncode or len(completed.stdout) > 65536:
        raise ValueError(f'Controlled case failed: {backend}/{kind}/{model}')
    try:
        report = json.loads(completed.stdout)
        expected = 'empty-success' if model == MODEL else 'typed-error'
        if (not isinstance(report, dict) or report.get('backend') != backend
                or report.get('kind') != kind or report.get('model') != model
                or report.get('outcome') != expected):
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError(f'Invalid case report: {backend}/{kind}/{model}') from None
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--identity-path', type=Path)
    parser.add_argument('--projects-path', type=Path)
    parser.add_argument('--backlog-path', type=Path)
    parser.add_argument('--base-url', type=local_base_url, required=True)
    parser.add_argument('--worker', choices=KINDS, help=argparse.SUPPRESS)
    parser.add_argument('--backend-path', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--model', choices=(MODEL, *FAILURE_MODELS), help=argparse.SUPPRESS)
    parser.add_argument('--kind', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.worker:
            if (not args.backend_path or not args.model
                    or args.kind not in KINDS[args.worker]):
                raise ValueError('Invalid controlled worker arguments')
            report = worker(args.worker, args.backend_path, args.base_url, args.model, args.kind)
        else:
            checkouts = {}
            for backend in KINDS:
                path = getattr(args, backend + '_path')
                if path is None:
                    raise ValueError('Configure all three backend checkout paths')
                checkouts[backend] = backend_python(path)
            cases = []
            for backend, kinds in KINDS.items():
                checkout, executable = checkouts[backend]
                for kind in kinds:
                    cases.append(run_case(backend, checkout, executable, args.base_url, MODEL, kind))
                for model in FAILURE_MODELS:
                    cases.append(run_case(backend, checkout, executable, args.base_url, model, kinds[0]))
            report = {'validation': 'controlled-http-only', 'real_ai_validated': False,
                      'expected_requests': 22, 'cases': cases,
                      'request_count_note': 'Confirm exactly 22 requests in the simulation log; '
                                            'this runner cannot observe provider retries itself.'}
        print(json.dumps(report, ensure_ascii=True))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        if args.worker:
            parser.exit(1, 'Controlled backend adapter check failed.\n')
        # Only runner-owned ValueError messages are safe to display.
        message = str(error) if isinstance(error, ValueError) else 'Controlled subprocess failed'
        parser.exit(2, message + '\n')
    except Exception:
        parser.exit(1, 'Controlled backend adapter check failed.\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
