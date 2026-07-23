import json
import urllib.request
import urllib.error

TRAVERSE_ENDPOINT = "http://localhost:6334/collections/agent_memory/graph/traverse"

def test_traversal():
    print("=== Testing Graph Traversal ===")
    
    # Trace the agent's thought process from node 1, up to 10 steps deep
    traverse_payload = {
        "start_id": 1,
        "max_depth": 10
    }

    req = urllib.request.Request(
        TRAVERSE_ENDPOINT,
        data=json.dumps(traverse_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
            print("[+] Traversal Successful! Agent's train of thought:")
            print(json.dumps(result, indent=2))
    except urllib.error.HTTPError as e:
        print(f"[!] LatticeDB Error: {e.code} {e.reason}")
        print(f"[*] Server Response: {e.read().decode('utf-8')}")
    except urllib.error.URLError as e:
        print(f"[!] Network Error: {e}")

test_traversal()
