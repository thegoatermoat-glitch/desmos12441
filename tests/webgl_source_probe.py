import json
import os
import re
from urllib.parse import urljoin

import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or "https://calc-unblocked.preview.emergentagent.com"
BASE_URL = BASE_URL.rstrip("/")
GAMES = ["slope.html", "tunnel-rush.html", "cluster-rush.html"]


def extract_refs(html: str):
    refs = re.findall(r"(?:src|href)=[\"']([^\"']+)[\"']", html, flags=re.IGNORECASE)
    return refs


def suspicious_refs(refs):
    out = []
    for r in refs:
        if any(k in r.lower() for k in ["unity", ".png", ".jpg", ".jpeg", ".mp3", ".ogg", ".wav", ".js", ".data", ".wasm"]):
            out.append(r)
    return out


def storage_markers(html: str):
    markers = [
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "document.cookie",
        "CacheStorage",
        "caches.",
        "SharedWorker",
        "Worker(",
        "new Worker",
        "XMLHttpRequest",
        "fetch(",
    ]
    found = [m for m in markers if m in html]
    return found


def main():
    out = {"base_url": BASE_URL, "games": []}

    games_resp = requests.get(f"{BASE_URL}/api/games", timeout=60)
    games_resp.raise_for_status()
    listed_games = {g["id"] for g in games_resp.json()}
    out["games_list_contains"] = {g: g in listed_games for g in GAMES}

    for game in GAMES:
        item = {"game": game}
        url = f"{BASE_URL}/api/games/{game}/content"
        r = requests.get(url, timeout=120)
        item["status_code"] = r.status_code
        item["content_length"] = len(r.text)
        item["csp"] = r.headers.get("Content-Security-Policy")
        item["cache_control"] = r.headers.get("Cache-Control")

        html = r.text
        refs = extract_refs(html)
        item["ref_count"] = len(refs)
        item["first_30_refs"] = refs[:30]
        item["suspicious_refs_sample"] = suspicious_refs(refs)[:60]
        item["relative_ref_sample"] = [x for x in refs if not x.startswith(("http://", "https://", "//", "data:", "/"))][:60]
        item["root_relative_ref_sample"] = [x for x in refs if x.startswith("/")][:60]
        item["storage_markers"] = storage_markers(html)

        item["contains_base_tag"] = "<base" in html.lower()
        base_match = re.search(r"<base[^>]*href=[\"']([^\"']+)[\"']", html, flags=re.IGNORECASE)
        item["base_href"] = base_match.group(1) if base_match else None

        # Resolve how relative refs would map if document URL is /library/{game}
        doc_url = f"{BASE_URL}/library/{game}"
        rel_preview = item["relative_ref_sample"][:20]
        item["resolved_relative_preview"] = [{"ref": x, "resolved": urljoin(doc_url, x)} for x in rel_preview]

        out["games"].append(item)

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()