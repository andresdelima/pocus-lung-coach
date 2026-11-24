"""Shared settings for the final project: paths, Portkey key loading, and the LLM client."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent  # AI Foundations root, holds the shared .env

DATA_DIR = HERE / "data"
OUTPUT_DIR = HERE / "output"
PROMPTS_DIR = HERE / "prompts"

PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
MODEL_NAME = "gpt-6-luna"  # course rule: gpt-6-luna only


def provider() -> str:
    """'portkey' (default) or 'openai' (direct), from POCUS_LLM_PROVIDER in .env."""
    load_dotenv(HERE / ".env")
    load_dotenv(WORKSPACE / ".env", override=False)
    p = os.getenv("POCUS_LLM_PROVIDER", "portkey").strip().lower()
    return p if p in ("portkey", "openai") else "portkey"


def load_api_key() -> str:
    """Load the key for the chosen provider from a local .env first, then the workspace root .env."""
    var = "OPENAI_API_KEY" if provider() == "openai" else "PORTKEY_API_KEY"
    key = os.getenv(var)
    if not key:
        raise RuntimeError(f"{var} not found. Add it to Final Project/.env or the AI Foundations .env.")
    return key


def make_client(force_refresh: bool = False):
    """OpenAI-compatible client: Portkey by default, or the OpenAI API directly when POCUS_LLM_PROVIDER=openai.

    force_refresh=True bypasses Portkey's response cache. Use it for any run whose results must be real.
    """
    from openai import OpenAI

    if provider() == "openai":
        return OpenAI(api_key=load_api_key())
    headers = {"x-portkey-cache-force-refresh": "true"} if force_refresh else {}
    return OpenAI(api_key=load_api_key(), base_url=PORTKEY_BASE_URL, default_headers=headers)
