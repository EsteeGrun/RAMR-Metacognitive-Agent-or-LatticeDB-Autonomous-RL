import json
import urllib.request
import urllib.error
from pathlib import Path

MEMORY_BANK_FILE = Path("agent_workspace/live_memory_graph.json")
SEARCH_ENDPOINT = "http://localhost:6334/collections/agent_memory/points/search"

def test_search():
    if not MEMORY_BANK_FILE.exists():
        print(f"[!] No memory bank found at {MEMORY_BANK_FILE}")
        return

    print("=== Testing Semantic Vector Search ===")
    
    # 1. Grab the first vector from our local file to use as the query
    with open(MEMORY_BANK_FILE, "r") as f:
        first_tx = json.loads(f.readline())
        query_vector = first_tx["nodes"][0]["properties"]["vector"]

    # 2. Build the search payload
    search_payload = {
        "vector": query_vector,
        "limit": 3
    }

    req = urllib.request.Request(
        SEARCH_ENDPOINT,
        data=json.dumps(search_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    # 3. Fire the query
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            print("[+] Search Successful! Top matches:")
            print(json.dumps(result, indent=2))
    except urllib.error.HTTPError as e:
        print(f"[!] LatticeDB Error: {e.code} {e.reason}")
        print(f"[*] Server Response: {e.read().decode('utf-8')}")
    except urllib.error.URLError as e:
        print(f"[!] Network Error: {e}")

test_search()
