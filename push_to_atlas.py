import json
import urllib.request
import urllib.error
from pathlib import Path

MEMORY_BANK_FILE = Path("agent_workspace/live_memory_graph.json")
LATTICEDB_ENDPOINT = "http://localhost:6334/collections/agent_memory/points"

def push_graph_data():
    if not MEMORY_BANK_FILE.exists():
        print(f"[!] No memory bank found at {MEMORY_BANK_FILE}")
        return

    print("=== Uploading Phase 3 RAMR Memory to LatticeDB ===")
    success_count = 0
    point_id = 1  # Rust expects an unsigned integer, not a string

    with open(MEMORY_BANK_FILE, "r") as f:
        for i, line in enumerate(f):
            if not line.strip(): continue
            transaction = json.loads(line)
            
            points = []
            for node in transaction["nodes"]:
                point = {
                    "id": point_id,
                    "vector": node["properties"]["vector"],
                    "payload": {
                        "text": node["properties"]["text"],
                        "labels": node["labels"],
                        "status": transaction.get("status", "UNKNOWN")
                    }
                }
                points.append(point)
                point_id += 1
            
            db_payload = {"points": points}
            
            req = urllib.request.Request(
                LATTICEDB_ENDPOINT,
                data=json.dumps(db_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="PUT"
            )
            
            try:
                with urllib.request.urlopen(req) as response:
                    print(f"[+] Transaction {i+1} committed successfully.")
                    success_count += 1
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                print(f"[!] LatticeDB Error on transaction {i+1}: {e.code} {e.reason}")
                print(f"[*] Server Response: {error_body}")
                break
            except urllib.error.URLError as e:
                print(f"[!] Network Error: {e}")
                break

    print(f"\n[*] Upload process complete. {success_count} transactions pushed.")

push_graph_data()
