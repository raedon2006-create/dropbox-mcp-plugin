#!/usr/bin/env python3
"""Save file content returned by a Dropbox MCP tool to a local path.

Usage:
  python3 save_download.py --input payload.b64 --output /path/file.pdf --base64
  python3 save_download.py --input payload.txt --output /path/notes.md
  cat payload.b64 | python3 save_download.py --output /path/file.pdf --base64
"""
import argparse
import base64
import binascii
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="File containing the payload (default: stdin)")
    parser.add_argument("--output", required=True, help="Destination path for the saved file")
    parser.add_argument("--base64", action="store_true",
                        help="Decode payload as base64 before saving (e.g. dash_read_binary_content)")
    args = parser.parse_args()

    raw = open(args.input, "rb").read() if args.input else sys.stdin.buffer.read()

    data = raw
    if args.base64:
        try:
            data = base64.b64decode(b"".join(raw.split()), validate=True)
        except (binascii.Error, ValueError) as exc:
            print(f"error: payload is not valid base64 ({exc})", file=sys.stderr)
            return 1

    out_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(out_dir, exist_ok=True)
    with open(args.output, "wb") as fh:
        fh.write(data)
    print(f"saved {len(data)} bytes -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
