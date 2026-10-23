"""SubQ (subq-snap): the probability that a text answers a yes/no question. Keys come from SUBQ_KEYS
(comma-separated); requests take the live keys in turn (several at once spread the load), and a key that is out of
credit or refused is dropped."""
import json
import os
import threading
import time
import urllib.error
import urllib.request

URL = "https://api.subq.ai/v1/systemone"
MODEL = os.environ.get("SUBQ_MODEL", "subq-snap-1.1")  # gives the preview's answers digit for digit (2026-10); some keys allow only it
_keys = [k.strip() for k in os.environ.get("SUBQ_KEYS", "").split(",") if k.strip()]
_lock = threading.Lock()
_turn = [0]
tokens = [0]


def _post(body: dict, key: str) -> dict:
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"content-type": "application/json", "authorization": f"Bearer {key}"})
    return json.load(urllib.request.urlopen(req, timeout=120))


def ask(body: dict) -> dict | None:
    """{question: probability} for a full systemone request body, or None if no key works."""
    for attempt in range(6):
        with _lock:
            if not _keys:
                return None
            key = _keys[_turn[0] % len(_keys)]
            _turn[0] += 1
        try:
            out = _post(body, key)
            with _lock:
                tokens[0] += out.get("usage", {}).get("input_tokens", 0)
            return {k: v["noul"] for k, v in out["answers"].items()}
        except urllib.error.HTTPError as e:
            if e.code in (401, 402, 403):  # this key is spent or refused: drop it, try another
                with _lock:
                    if key in _keys:
                        _keys.remove(key)
                continue
            if e.code == 422:
                return None
            time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def score(state: str, instructions: str, true: str, false: str) -> float | None:
    """The probability of 'true', or None if no key works."""
    out = ask({"model": MODEL, "state": state,
               "questions": {"q": {"type": "noul", "instructions": instructions, "criteria": {"true": true, "false": false}}}})
    return out and out["q"]
