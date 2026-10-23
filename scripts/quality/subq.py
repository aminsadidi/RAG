"""SubQ (subq-snap): the probability that a text answers a yes/no question. Keys come from SUBQ_KEYS
(comma-separated); requests take the live keys in turn (several at once spread the load), and a key that is out of
credit or refused is dropped."""
import collections
import json
import os
import threading
import time
import urllib.error
import urllib.request

URL = "https://api.subq.ai/v1/systemone"
MODEL = os.environ.get("SUBQ_MODEL", "subq-snap-1.1")
# the two models give the same answers digit for digit (2026-10), but some keys are allowed only one of them, and a key is
# sometimes refused a model it was allowed a moment before: a refused key tries the other model before it is dropped
OTHER = {"subq-snap-1.1": "subq-snap-preview", "subq-snap-preview": "subq-snap-1.1"}
_keys = [k.strip() for k in os.environ.get("SUBQ_KEYS", "").split(",") if k.strip()]
_lock = threading.Lock()
_turn = [0]
_model = {}  # key -> the model it is switched to after a refusal
_refused = collections.Counter()
tokens = [0]
errors = collections.Counter()  # what failed, for the caller's report


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
        model = _model.get(key, body.get("model"))
        try:
            out = _post({**body, "model": model}, key)
            with _lock:
                tokens[0] += out.get("usage", {}).get("input_tokens", 0)
            return {k: v["noul"] for k, v in out["answers"].items()}
        except urllib.error.HTTPError as e:
            msg = e.read()[:120].decode("utf-8", "replace")
            errors[f"{e.code} {msg[:60]}"] += 1
            # dropped only when the key itself is spent, invalid or not allowed this model; a refusal under load
            # (other 403s, 429) is waited out, so a busy moment cannot empty the key list
            if e.code == 403 and "not permitted" in msg and model in OTHER:
                with _lock:  # the other model; the key is dropped only after repeated refusals
                    _model[key] = OTHER[model]
                    _refused[key] += 1
                    spent = _refused[key] >= 6
                if not spent:
                    continue
            if e.code in (401, 402) or (e.code == 403 and "not permitted" in msg):
                with _lock:
                    if key in _keys:
                        _keys.remove(key)
                continue
            if e.code == 422:
                return None
            time.sleep(2 * (attempt + 1))
        except Exception as e:  # noqa: BLE001 - a network error: wait and try again
            errors[type(e).__name__] += 1
            time.sleep(2 * (attempt + 1))
    return None


def score(state: str, instructions: str, true: str, false: str) -> float | None:
    """The probability of 'true', or None if no key works."""
    out = ask({"model": MODEL, "state": state,
               "questions": {"q": {"type": "noul", "instructions": instructions, "criteria": {"true": true, "false": false}}}})
    return out and out["q"]
