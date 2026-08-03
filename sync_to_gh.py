import urllib.request, urllib.error, json, base64, os, sys, time

TOKEN = os.environ.get("GH_TOKEN")
if not TOKEN:
    try:
        with open(os.path.expanduser("~/.workbuddy/gangstar_gh_token")) as f:
            TOKEN = f.read().strip()
    except Exception:
        pass
if not TOKEN:
    print("NO TOKEN"); sys.exit(1)

OWNER = "alanbyzee"
REPO = "gangstar-dashboard"
H = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
     "User-Agent": "workbuddy", "X-GitHub-Api-Version": "2022-11-28"}
API = "https://api.github.com"
SRC = "/Users/alan/WorkBuddy/2026-07-27-22-07-48/gangstar-ops-hub"
FILES = {
    "index.html":   os.path.join(SRC, "Gangstar运营看板_分享版.html"),
    "fan_data.json": os.path.join(SRC, "fan_data.json"),
    "hq_data.js":    os.path.join(SRC, "hq_data.js"),
}

def get_sha(path):
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{API}/repos/{OWNER}/{REPO}/contents/{path}", headers=H), timeout=30) as r:
            return json.loads(r.read().decode()).get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

def put(path, local, sha):
    with open(local, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    data = {"message": f"sync {path} @ {time.strftime('%Y-%m-%d %H:%M')}", "content": b64, "branch": "main"}
    if sha:
        data["sha"] = sha
    req = urllib.request.Request(f"{API}/repos/{OWNER}/{REPO}/contents/{path}", data=json.dumps(data).encode(), method="PUT", headers=H)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.loads(r.read().decode())

for path, local in FILES.items():
    if not os.path.exists(local):
        print("SKIP (missing)", local); continue
    sha = get_sha(path)
    st, res = put(path, local, sha)
    print(f"PUT {path}: HTTP {st}  commit={res.get('commit', {}).get('sha', '')[:10]}")
print("DONE")
