import json
import urllib.request
import urllib.error

COLLECTION_URL = "http://localhost:6334/collections/agent_memory"

def recreate_collection():
    print("=== Recreating LatticeDB Collection (768 Dimensions) ===")
    
    # 1. Wipe the old collection
    try:
        req = urllib.request.Request(COLLECTION_URL, method="DELETE")
        urllib.request.urlopen(req)
        print("[+] Deleted old collection.")
    except Exception:
        pass # Already deleted from your previous run

    # 2. Re-initialize with 768 dimensions (Nested Schema)
    payload = {
        "vectors": {
            "size": 768,
            "distance": "Cosine"
        }
    }
    
    req = urllib.request.Request(
        COLLECTION_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PUT" 
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            print("[+] Successfully created new collection with 768 dimensions!")
    except urllib.error.HTTPError as e:
        print(f"[!] Server Error: {e.code} {e.read().decode('utf-8')}")

if __name__ == "__main__":
    recreate_collection()
