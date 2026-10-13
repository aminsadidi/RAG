"""SubQ (subq-snap-preview): the probability that a text answers a yes/no question. Keys come from
SUBQ_KEYS (comma-separated); when one is out of credit or refused, the next is used."""
import json
import os
import threading
import time
import urllib.error
import urllib.request

URL = "https://api.subq.ai/v1/systemone"
_keys = [k.strip() for k in os.environ.get("SUBQ_KEYS", "").split(",") if k.strip()]
_lock = threading.Lock()
_at = [0]
tokens = [0]


def _post(body: dict, key: str) -> dict:
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"content-type": "application/json", "authorization": f"Bearer {key}"})
    return json.load(urllib.request.urlopen(req, timeout=120))


def score(state: str, instructions: str, true: str, false: str) -> float | None:
    """The probability of 'true', or None if no key works."""
    body = {"model": "subq-snap-preview", "state": state,
            "questions": {"q": {"type": "noul", "instructions": instructions, "criteria": {"true": true, "false": false}}}}
    for attempt in range(6):
        with _lock:
            if _at[0] >= len(_keys):
                return None
            key = _keys[_at[0]]
        try:
            out = _post(body, key)
            with _lock:
                tokens[0] += out.get("usage", {}).get("input_tokens", 0)
            return out["answers"]["q"]["noul"]
        except urllib.error.HTTPError as e:
            if e.code in (401, 402, 403):  # this key is spent or refused: the next one
                with _lock:
                    if _keys[_at[0]] == key:
                        _at[0] += 1
                continue
            if e.code == 422:
                return None
            time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None
