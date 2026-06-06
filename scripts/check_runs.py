import sys, json, urllib.request
url = "https://api.github.com/repos/1y4w1s/ai-industry-digest/actions/runs?per_page=10"
req = urllib.request.Request(url, headers={"User-Agent": "curl/1.0"})
data = json.loads(urllib.request.urlopen(req).read())
for r in data.get("workflow_runs", []):
    name = r["name"][:30]
    created = r["created_at"][:19]
    print(f"{r['id']} | {name:30s} | {r['status']:10s} | {r['conclusion']:10s} | {r['event']:12s} | {created}")
