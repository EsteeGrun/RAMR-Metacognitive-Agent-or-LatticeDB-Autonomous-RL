import json
import urllib.request
import urllib.error
from pathlib import Path

MEMORY_BANK_FILE = Path("agent_workspace/live_memory_graph.json")
EDGES_ENDPOINT = "http://localhost:6334/collections/agent_memory/graph/edges"

def push_chronological_edges():
    if not MEMORY_BANK_FILE.exists():
        print(f"[!] No memory bank found at {MEMORY_BANK_FILE}")
        return

    print("=== Wiring Agent Memory Chronologically ===")
    
    total_nodes = 0
    with open(MEMORY_BANK_FILE, "r") as f:
        for line in f:
            if not line.strip(): continue
            transaction = json.loads(line)
            total_nodes += len(transaction.get("nodes", []))

    if total_nodes < 2:
        print("[!] Not enough nodes to create a graph trajectory.")
        return

    success_count = 0
    for current_id in range(1, total_nodes):
        edge_payload = {
            "from_id": current_id,
            "to_id": current_id + 1,
            "relation": "leads_to",
            "weight": 1.0
        }

        req = urllib.request.Request(
            EDGES_ENDPOINT,
            data=json.dumps(edge_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req) as response:
                success_count += 1
        except urllib.error.HTTPError as e:
            print(f"[!] Error linking node {current_id} -> {current_id+1}: {e.code} {e.reason}")
            print(f"[*] Server Response: {e.read().decode('utf-8')}")
            break
        except urllib.error.URLError as e:
            print(f"[!] Network Error: {e}")
            break

    print(f"[+] Successfully committed {success_count} edges into the graph trajectory!")

push_chronological_edges()
