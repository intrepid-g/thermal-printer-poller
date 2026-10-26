"""Poll an Everything server for print jobs over MCP and print them.

Needs a token with only the `print` scope. Run: `thermal-poller` (loops) or `thermal-poller --once`.
"""

import base64
import io
import json
import sys
import time
import urllib.error
import urllib.request

from PIL import Image

import btprint
import config

INTERVAL = 30  # seconds between polls
BATCH = 5


def call(url: str, token: str, tool: str, arguments: dict):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": arguments}}
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if "error" in payload or payload["result"].get("isError"):
        raise RuntimeError(json.dumps(payload.get("error") or payload["result"]))
    return json.loads(payload["result"]["content"][0]["text"])


def image_for(job: dict) -> Image.Image:
    if job["kind"] == "image":
        return btprint.from_image(io.BytesIO(base64.b64decode(job["image_base64"])))
    return btprint.render(job["text"])


def run_job(url: str, token: str, job: dict) -> None:
    try:
        for _ in range(job["copies"]):
            btprint.print_image(image_for(job))
        call(url, token, "finish_print_job", {"id": job["id"], "ok": True})
    except Exception as exc:  # report and let the server retry; never kill the loop
        call(url, token, "finish_print_job", {"id": job["id"], "ok": False, "error": str(exc)[:400]})


def poll_once(url: str, token: str) -> int:
    jobs = call(url, token, "claim_print_jobs", {"limit": BATCH})
    for job in jobs:
        run_job(url, token, job)
    return len(jobs)


def main() -> None:
    url = config.get("server_url", "Everything MCP URL (e.g. https://host/mcp/): ").rstrip("/") + "/"
    token = config.get("token", "Print-scope token (evt_...): ")
    btprint.printer_address()  # ask now, not in the middle of the first job
    once = "--once" in sys.argv
    while True:
        try:
            poll_once(url, token)
        except (urllib.error.URLError, RuntimeError, OSError) as exc:
            print(f"poll failed: {exc}", file=sys.stderr)
        if once:
            return
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
