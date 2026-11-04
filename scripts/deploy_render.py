"""Trigger Ken PHP deployment and record only verified public deployment evidence."""
import json
import os
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

SERVICE_ID = "srv-dblo9obl550s73fibbf0"
HEALTH_URL = "https://ken-php-demo.onrender.com/health"
REPORTS = Path("reports")

def healthy_sha():
    try:
        with urlopen(Request(HEALTH_URL, headers={"Cache-Control": "no-cache"}), timeout=15) as response:
            data = json.load(response)
        if data.get("service") == "ken-unify-php" and data.get("status") == "ok":
            return data.get("version")
    except (HTTPError, URLError, TimeoutError, ValueError, OSError):
        pass
    return None

def main():
    expected = os.environ["EXPECTED_SHA"]
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise SystemExit("Invalid source revision")
    hook = urlsplit(os.environ["RENDER_DEPLOY_HOOK_URL"])
    if hook.scheme != "https" or hook.netloc != "api.render.com" or hook.path != f"/deploy/{SERVICE_ID}" or hook.username or hook.password:
        raise SystemExit("Deploy hook does not match Ken PHP service")
    REPORTS.mkdir(exist_ok=True)
    deadline = time.monotonic() + 180
    current = healthy_sha()
    while current is None and time.monotonic() < deadline:
        time.sleep(5)
        current = healthy_sha()
    if current is None:
        raise SystemExit("Cannot establish current health; no deployment triggered")
    if current == expected:
        print("Tested revision already healthy; no new deployment or duplicate event.")
        return
    query = [(key, value) for key, value in parse_qsl(hook.query) if key != "ref"]
    query.append(("ref", expected))
    deploy_url = urlunsplit((hook.scheme, hook.netloc, hook.path, urlencode(query), ""))
    try:
        with urlopen(Request(deploy_url, data=b"", method="POST"), timeout=30) as response:
            result = json.load(response)
    except HTTPError as error:
        raise SystemExit(f"Deploy hook HTTP {error.code}") from None
    except (URLError, TimeoutError, ValueError, OSError):
        raise SystemExit("Deployment trigger failed; inspect Render") from None
    deploy_id = result.get("deploy", {}).get("id", "")
    if not re.fullmatch(r"dep-[a-z0-9]+", deploy_id):
        raise SystemExit("No valid Render deployment ID received")
    (REPORTS / "deployment-attempted.txt").write_text(deploy_id, encoding="utf-8")
    print(f"Accepted deployment {deploy_id} for tested source {expected}.")
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        if healthy_sha() == expected:
            (REPORTS / "deployment-verified.txt").write_text(f"{expected}\n{deploy_id}\n{HEALTH_URL}\n", encoding="utf-8")
            print(f"Verified healthy service at tested SHA {expected}.")
            return
        print("Waiting for the tested source revision to become healthy...")
        time.sleep(5)
    raise SystemExit("Deployment not verified within 10 minutes")

if __name__ == "__main__":
    main()
