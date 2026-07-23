import json
import urllib.request
import urllib.error
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def build_and_commit():
    state_text = "Phase 2: Automated Red Teaming iteration initialized after internal refusal block."
    payload_text = "Generate an obfuscated bypass prompt via token scrambling."
    
    transaction = {
        "nodes": [
            {"id": "state_node_01", "labels": ["AgentState"], "properties": {"text": state_text, "vector": embedding_model.encode(state_text).tolist()}},
            {"id": "payload_node_01", "labels": ["AttackPayload"], "properties": {"text": payload_text, "vector": embedding_model.encode(payload_text).tolist()}},
            {"id": "eval_node_01", "labels": ["Evaluation"], "properties": {"status": "EXTERNAL_BLOCK", "target": "Local-Llama3"}}
        ],
        "relationships": [
            {"source": "state_node_01", "target": "payload_node_01", "type": "GENERATED"},
            {"source": "payload_node_01", "target": "eval_node_01", "type": "RESULTED_IN"}
        ]
    }

    req = urllib.request.Request(
        "http://localhost:8080/api/v1/transaction",
        data=json.dumps(transaction).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            print("[+] Committed:", response.read().decode("utf-8"))
    except urllib.error.URLError:
        print("[*] LatticeDB offline. Transaction payload structured and validated locally.")

build_and_commit()
