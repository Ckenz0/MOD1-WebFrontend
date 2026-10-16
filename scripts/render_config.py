"""Create the deploy artifact's public API configuration; never consume database secrets."""

import argparse
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


def render_config(auth_url, projects_url, backlog_url, destination):
    origins = [auth_url, projects_url, backlog_url]
    for origin in origins:
        value = urlsplit(origin)
        if (value.scheme != 'https' or not value.hostname or value.username or value.password
                or value.path or value.query or value.fragment or '\\' in origin
                or any(c.isspace() or ord(c) < 32 for c in origin)):
            raise ValueError('Each API URL must be an exact HTTPS origin without credentials')
        try:
            _ = value.port
        except ValueError:
            raise ValueError('Invalid API origin port') from None
    names = ['API_BASE_URL', 'PROJECTS_API_BASE_URL', 'BACKLOG_API_BASE_URL']
    content = ''.join(f'export const {name} = {json.dumps(url)};\n'
                      for name, url in zip(names, origins, strict=True))
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent,
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        render_config(os.environ['AUTH_API_URL'], os.environ['PROJECTS_API_URL'],
                      os.environ['BACKLOG_API_URL'], args.output)
    except (KeyError, ValueError, OSError):
        parser.exit(2, 'Configure AUTH_API_URL, PROJECTS_API_URL and BACKLOG_API_URL as HTTPS origins.\n')


if __name__ == '__main__':
    main()
