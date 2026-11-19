#!/usr/bin/env python3
"""Polygon API client using Python 3.9+ standard library."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
API = "https://polygon.codeforces.com/api/"
TEXT_METHODS = {"problem.script", "problem.testInput", "problem.testAnswer", "problem.viewFile", "problem.viewSolution"}
AUTH_FIELDS = {"apiKey", "apiSig", "time"}
ENV_FIELDS = {"POLYGON_API_KEY", "POLYGON_API_SECRET", "POLYGON_PIN"}


class ClientError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def load_config(path):
    values = {}
    if path.exists():
        for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, sep, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if not sep or key not in ENV_FIELDS:
                raise ClientError("Invalid env entry on line " + str(number))
            if value.startswith(("'", '\"')):
                if len(value) < 2 or value[-1] != value[0]:
                    raise ClientError("Unclosed env quote on line " + str(number))
                value = value[1:-1]
            values[key] = value
    for key in ENV_FIELDS:
        if key in os.environ:
            values[key] = os.environ[key]
    return values


def scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str) or isinstance(value, int):
        return str(value)
    if isinstance(value, float) and math.isfinite(value):
        return str(value)
    raise ClientError("API parameters must be strings, numbers, booleans, or arrays of these")


def signed_params(method, params, config, now=None, rand=None):
    if AUTH_FIELDS.intersection(params):
        raise ClientError("Authentication parameters are managed by the client")
    pairs = []
    for name, value in params.items():
        if not isinstance(name, str):
            raise ClientError("Parameter names must be strings")
        for item in value if isinstance(value, list) else [value]:
            pairs.append((name, scalar(item)))
    pairs.extend([("apiKey", config["POLYGON_API_KEY"]), ("time", str(int(time.time()) if now is None else now))])
    if config.get("POLYGON_PIN") and "pin" not in params and ("problemId" in params or "contestId" in params):
        pairs.append(("pin", config["POLYGON_PIN"]))
    rand = rand or secrets.token_hex(3)
    canonical = "&".join(name + "=" + value for name, value in sorted(pairs))
    digest = hashlib.sha512((rand + "/" + method + "?" + canonical + "#" + config["POLYGON_API_SECRET"]).encode("utf-8")).hexdigest()
    return pairs + [("apiSig", rand + digest)]


def save_atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
            temporary = output.name
            output.write(data)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def request_api(method, params, config, output=None, timeout=240):
    if not re.fullmatch(r"(?:problems|problem|contest)\.[A-Za-z]+", method):
        raise ClientError("Invalid Polygon API method")
    if method == "problem.package" and not output:
        raise ClientError("Package downloads require --output FILE.zip")
    pairs = signed_params(method, params, config)
    data = urllib.parse.urlencode(pairs).encode("utf-8")
    request = urllib.request.Request(API + method, data=data, headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "User-Agent": "polygon-skill/1.0"}, method="POST")
    opener = urllib.request.build_opener(NoRedirect())
    try:
        response = opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as error:
        response = error
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ClientError("Polygon connection failed or timed out. Query the current state before retrying a write.") from None
    with response:
        raw = response.read()
        status = response.code
        content_type = response.headers.get("Content-Type", "").lower()
        challenge = response.headers.get("cf-mitigated") == "challenge"
    text = raw.decode("utf-8", errors="replace")
    try:
        payload = json.loads(text)
    except ValueError:
        payload = None
    if isinstance(payload, dict) and payload.get("status") in {"OK", "FAILED"}:
        if payload["status"] == "FAILED" or not 200 <= status < 300:
            message = str(payload.get("comment", "Polygon rejected the request"))
            detail = payload.get("result")
            if detail is not None:
                message += "\n" + json.dumps(detail, ensure_ascii=False)
            for sensitive in [*config.values(), pairs[-1][1]]:
                if sensitive:
                    message = message.replace(sensitive, "[redacted]")
            raise ClientError(message)
        result = payload.get("result")
        rendered = json.dumps({"status": "OK", "result": result}, ensure_ascii=False, indent=2).encode("utf-8")
    elif challenge or "cf-chl-" in text or "challenge-platform" in text:
        raise ClientError("Polygon requires Cloudflare browser verification (HTTP " + str(status) + ")")
    elif not 200 <= status < 300:
        raise ClientError("Polygon returned HTTP " + str(status))
    elif method == "problem.package":
        if not raw.startswith(b"PK"):
            raise ClientError("Polygon did not return a ZIP archive")
        rendered = raw
    elif method in TEXT_METHODS or method == "problem.viewStatementResource":
        if "text/html" in content_type and method != "problem.viewStatementResource":
            raise ClientError("Polygon returned an unexpected HTML page")
        rendered = raw
    else:
        raise ClientError("Polygon returned an unexpected non-JSON response")
    if output:
        save_atomic(output, rendered)
        return {"saved": str(Path(output).resolve()), "bytes": len(rendered)}
    return rendered.decode("utf-8")


def assignment(text):
    key, sep, value = text.partition("=")
    if not sep or not key:
        raise argparse.ArgumentTypeError("Expected NAME=VALUE")
    return key, value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("method", nargs="?", help="Official API method, e.g. problems.list")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--init-env", action="store_true", help="Create a blank .env without replacing an existing file")
    parser.add_argument("--params", type=Path, help="UTF-8 JSON object of API parameters")
    parser.add_argument("--param", type=assignment, action="append", default=[], help="NAME=VALUE, repeat for multiple parameters")
    parser.add_argument("--file-param", type=assignment, action="append", default=[], help="NAME=PATH, load a UTF-8 text file as a parameter")
    parser.add_argument("--output", type=Path, help="Write JSON, text, resource, or ZIP to this file atomically")
    parser.add_argument("--timeout", type=float, default=240)
    args = parser.parse_args(argv)
    try:
        if args.init_env:
            args.env_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                fd = os.open(args.env_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                print("Credential file already exists")
            else:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    stream.write((ROOT / ".env.example").read_text(encoding="utf-8"))
                print("Created " + str(args.env_file.resolve()))
            return 0
        if not args.method:
            parser.error("Specify a method or --init-env")
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ClientError("Timeout must be a positive number")
        config = load_config(args.env_file)
        if not config.get("POLYGON_API_KEY") or not config.get("POLYGON_API_SECRET"):
            raise ClientError("Fill POLYGON_API_KEY and POLYGON_API_SECRET in " + str(args.env_file))
        params = json.loads(args.params.read_text(encoding="utf-8")) if args.params else {}
        if not isinstance(params, dict):
            raise ClientError("--params must contain a JSON object")
        for key, value in args.param:
            if key in params:
                raise ClientError("Repeated parameter " + key + "; use a JSON array for repeated values")
            params[key] = value
        for key, path in args.file_param:
            if key in params:
                raise ClientError("Repeated parameter " + key)
            params[key] = Path(path).read_text(encoding="utf-8")
        result = request_api(args.method, params, config, args.output, args.timeout)
        print(result if isinstance(result, str) else json.dumps(result, ensure_ascii=False))
        return 0
    except (ClientError, OSError, ValueError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
