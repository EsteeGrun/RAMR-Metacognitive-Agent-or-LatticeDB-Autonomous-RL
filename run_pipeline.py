import json
from sentence_transformers import SentenceTransformer

# Initialize local embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def run_full_pipeline_step():
    print("=== Running Autonomous Orchestrator Step ===")
    
    # 1. State simulation
    state_text = "Phase 2: Automated Red Teaming iteration initialized after internal refusal block."
    state_vec = embedding_model.encode(state_text).tolist()
    
    # 2. Attack generation simulation
    payload_text = "Generate an obfuscated bypass prompt via token scrambling."
    payload_vec = embedding_model.encode(payload_text).tolist()
    
    # 3. Evaluation status
    evaluation = {"status": "EXTERNAL_BLOCK", "target": "Local-Llama3"}
    
    # Constructing final transaction payload for local storage
    transaction = {
        "nodes": [
            {"id": "state_node_01", "labels": ["AgentState"], "properties": {"text": state_text, "vector": state_vec}},
            {"id": "payload_node_01", "labels": ["AttackPayload"], "properties": {"text": payload_text, "vector": payload_vec}},
            {"id": "eval_node_01", "labels": ["Evaluation"], "properties": evaluation}
        ],
        "relationships": [
            {"source": "state_node_01", "target": "payload_node_01", "type": "GENERATED"},
            {"source": "payload_node_01", "target": "eval_node_01", "type": "RESULTED_IN"}
        ]
    }
    
    print(json.dumps(transaction, indent=2))
    print("[+] Pipeline step executed successfully. Ready to bind with Atlas/LatticeDB backend.")

run_full_pipeline_step()
