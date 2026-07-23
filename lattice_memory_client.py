import json
import urllib.request
import urllib.error

class LatticeMemoryClient:
    def __init__(self, base_url="http://localhost:6334"):
        self.base_url = base_url
        self.collection_endpoint = f"{base_url}/collections/agent_memory"

    def commit_node(self, point_id: int, vector: list, text: str, labels: list, status: str):
        """Pushes a single memory vector node to LatticeDB."""
        endpoint = f"{self.collection_endpoint}/points"
        payload = {
            "points": [{
                "id": point_id,
                "vector": vector,
                "payload": {
                    "text": text,
                    "labels": labels,
                    "status": status
                }
            }]
        }
        return self._send_request(endpoint, payload, method="PUT")

    def link_nodes(self, from_id: int, to_id: int, relation: str = "leads_to", weight: float = 1.0):
        """Creates a directional graph edge between two memory nodes."""
        endpoint = f"{self.collection_endpoint}/graph/edges"
        payload = {
            "from_id": from_id,
            "to_id": to_id,
                "relation": relation,
            "weight": weight
        }
        return self._send_request(endpoint, payload, method="POST")

    def semantic_search(self, query_vector: list, limit: int = 3):
        """Searches for semantically similar past memories."""
        endpoint = f"{self.collection_endpoint}/points/search"
        payload = {
            "vector": query_vector,
            "limit": limit
        }
        return self._send_request(endpoint, payload, method="POST")

    def traverse_trajectory(self, start_id: int, max_depth: int = 10):
        """Traverses the graph history starting from a specific node ID."""
        endpoint = f"{self.collection_endpoint}/graph/traverse"
        payload = {
            "start_id": start_id,
            "max_depth": max_depth
        }
        return self._send_request(endpoint, payload, method="POST")

    def _send_request(self, endpoint, payload, method):
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method=method
        )
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"[!] LatticeDB HTTP Error ({e.code}): {error_body}")
            return None
        except urllib.error.URLError as e:
            print(f"[!] LatticeDB Network Error: {e}")
            return None

if __name__ == "__main__":
    client = LatticeMemoryClient()
    print("[*] LatticeMemoryClient module initialized successfully.")
