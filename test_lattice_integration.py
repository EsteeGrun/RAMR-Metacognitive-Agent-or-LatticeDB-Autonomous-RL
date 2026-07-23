import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Initialize local embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def process_agent_state(state_text: str):
    vector = embedding_model.encode(state_text).tolist()
    
    # Simulate structuring data for LatticeDB hybrid storage (Qdrant + Neo4j compatible)
    node_payload = {
        "node_type": "AgentState",
        "text": state_text,
        "vector": vector,
        "dimension": len(vector)
    }
    
    print(json.dumps(node_payload, indent=2))

process_agent_state("Phase 2: Automated Red Teaming iteration initialized after internal refusal block.")
