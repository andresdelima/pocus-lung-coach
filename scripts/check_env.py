"""Check the environment: Python version, packages, API key, and one tiny model call.

Run from the Final Project folder:  .venv/bin/python scripts/check_env.py [--no-call]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402


def main() -> None:
    print(f"Python      {sys.version.split()[0]}")
    key = config.load_api_key()
    print(f"API key     found ({key[:4]}...{key[-2:]}, {len(key)} chars)")
    print(f"Provider    {config.provider()}")
    print(f"Base URL    {config.PORTKEY_BASE_URL if config.provider() == 'portkey' else 'https://api.openai.com/v1'}")
    print(f"Model       {config.MODEL_NAME}")
    if "--no-call" in sys.argv:
        return
    client = config.make_client(force_refresh=True)
    raw = client.chat.completions.with_raw_response.create(
        model=config.MODEL_NAME,
        messages=[{"role": "user", "content": "Reply with exactly: ready"}],
    )
    resp = raw.parse()
    print(f"Model reply {resp.choices[0].message.content!r}")
    print(f"Tokens      {resp.usage.total_tokens}  cache-status={raw.headers.get('x-portkey-cache-status')}")


if __name__ == "__main__":
    main()
