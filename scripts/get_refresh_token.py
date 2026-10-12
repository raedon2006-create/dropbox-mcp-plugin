#!/usr/bin/env python3
"""One-time helper: obtain a long-lived Dropbox OAuth refresh token.

Usage:
  python3 get_refresh_token.py --app-key KEY --app-secret SECRET

Opens no browser itself — prints the authorization URL, you open it, approve,
and paste the code back. Prints the refresh token to set as DROPBOX_REFRESH_TOKEN.
"""
import argparse
import getpass

import requests

AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"


def build_authorize_url(app_key: str) -> str:
    return (f"{AUTH_URL}?client_id={app_key}&response_type=code"
            f"&token_access_type=offline")


def exchange_code(app_key: str, app_secret: str, code: str) -> dict:
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": code.strip(),
        "client_id": app_key,
        "client_secret": app_secret,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--app-key", required=True)
    parser.add_argument("--app-secret", required=True)
    args = parser.parse_args()

    print("1. Open this URL and approve access:\n")
    print(f"   {build_authorize_url(args.app_key)}\n")
    code = getpass.getpass("2. Paste the authorization code here: ")
    tokens = exchange_code(args.app_key, args.app_secret, code)

    print("\nSuccess. Set these environment variables for the MCP server:\n")
    print(f"export DROPBOX_REFRESH_TOKEN={tokens['refresh_token']}")
    print(f"export DROPBOX_APP_KEY={args.app_key}")
    print(f"export DROPBOX_APP_SECRET={args.app_secret}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
