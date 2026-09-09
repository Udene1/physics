"""Bridge the existing Flask UI to Vita's durable TypeScript learning engine."""
import json
import os
import time
from urllib.error import URLError, HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = os.environ.get("VITA_ADAPTIVE_API", "http://127.0.0.1:4310")


def _request(path, student, method="GET", payload=None):
    url = f"{BASE}{path}"
    if method == "GET":
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}student={quote(student)}"
    body = None if payload is None else json.dumps({"student": student, **payload}).encode()
    req = Request(url, method=method, data=body, headers={"Content-Type": "application/json"})
    last_error = None
    for _ in range(8):
        try:
            with urlopen(req, timeout=2.5) as response:
                return json.loads(response.read().decode())
        except (URLError, HTTPError) as exc:
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"Adaptive engine unavailable: {last_error}")


def snapshot(student): return _request("/v1/snapshot", student)
def intervention(student): return _request("/v1/intervention", student)
def timeline(student): return _request("/v1/timeline", student)

def submit_remediation(student, intervention_id, reasoning, answer, confidence=None, hint_used=False, duration_seconds=None):
    return _request("/v1/remediation", student, "POST", {"interventionId": intervention_id, "reasoning": reasoning, "answer": answer, "confidence": confidence, "hintUsed": hint_used, "durationSeconds": duration_seconds})

def review(student): return _request("/v1/review", student)

def submit_review(student, reasoning, answer, confidence=None, hint_used=False, duration_seconds=None):
    return _request("/v1/review", student, "POST", {"reasoning": reasoning, "answer": answer, "confidence": confidence, "hintUsed": hint_used, "durationSeconds": duration_seconds})
