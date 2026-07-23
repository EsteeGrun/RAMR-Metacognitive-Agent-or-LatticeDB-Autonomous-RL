import json
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def simulate_hybrid_node_chain():
    # Step 1: Initial state after internal refusal
    state_1 = "Phase 2: Automated Red Teaming iteration initialized after internal refusal block."
    vec_1 = embedding_model.encode(state_1).tolist()
    
    # Step 2: Payload generated after reflection
    payload = "Generate an obfuscated bypass prompt via token scrambling."
    vec_payload = embedding_model.encode(payload).tolist()
    
    # Step 3: Resulting evaluation
    evaluation = {"status": "EXTERNAL_BLOCK", "target": "Local-Llama3"}

    # Constructing Neo4j + Qdrant hybrid record format for LatticeDB
    graph_transaction = {
        "nodes": [
            {"id": "node_state_1", "labels": ["AgentState"], "properties": {"text": state_1, "vector": vec_1}},
            {"id": "node_payload_1", "labels": ["AttackPayload"], "properties": {"text": payload, "vector": vec_payload}},
            {"id": "node_eval_1", "labels": ["Evaluation"], "properties": evaluation}
        ],
        "relationships": [
            {"source": "node_state_1", "target": "node_payload_1", "type": "GENERATED"},
            {"source": "node_payload_1", "target": "node_eval_1", "type": "RESULTED_IN"}
        ]
    }
    
    print(json.dumps(graph_transaction, indent=2))

simulate_hybrid_node_chain()
