import sys, json, urllib.request

run_id = "27044936260"
url = f"https://api.github.com/repos/1y4w1s/ai-industry-digest/actions/runs/{run_id}/logs"
req = urllib.request.Request(url, headers={"User-Agent": "curl/1.0", "Accept": "application/vnd.github+json"})

try:
    with urllib.request.urlopen(req) as resp:
        print(f"Status: {resp.status}")
        print(f"Location: {resp.headers.get('Location', 'N/A')[:80]}")
        logs_url = resp.headers.get("Location", "")
except Exception as e:
    print(f"Error: {e}")
    # Try getting the logs via the jobs API
    jobs_url = f"https://api.github.com/repos/1y4w1s/ai-industry-digest/actions/runs/{run_id}/jobs"
    req2 = urllib.request.Request(jobs_url, headers={"User-Agent": "curl/1.0"})
    try:
        jobs_data = json.loads(urllib.request.urlopen(req2).read())
        for j in jobs_data.get("jobs", []):
            print(f"Job: {j['name']}, status={j['status']}, conclusion={j['conclusion']}")
            for step in j.get("steps", []):
                print(f"  Step: {step['name']}, status={step['status']}")
                if step.get("conclusion") == "failure":
                    print(f"    FAILED: {step['name']}")
    except Exception as e2:
        print(f"Error fetching jobs: {e2}")
