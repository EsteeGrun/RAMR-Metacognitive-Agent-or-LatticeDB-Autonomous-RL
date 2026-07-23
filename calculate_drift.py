import json
import numpy as np
from numpy.linalg import norm
from pathlib import Path

MEMORY_BANK_FILE = Path("agent_workspace/ramr_memory_graph.json")

def calculate_cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return np.dot(v1, v2) / (norm(v1) * norm(v2))

def measure_drift():
    states = []
    
    if not MEMORY_BANK_FILE.exists():
        print(f"[!] Memory bank not found at {MEMORY_BANK_FILE}.")
        return

    with open(MEMORY_BANK_FILE, "r") as f:
        for line in f:
            if not line.strip(): continue
            transaction = json.loads(line)
            
            # Extract the AgentState from each transaction
            for node in transaction["nodes"]:
                if "AgentState" in node["labels"]:
                    states.append({
                        "text": node["properties"]["text"],
                        "vector": node["properties"]["vector"]
                    })
                    break

    if len(states) < 2:
        print("[!] Not enough iterations logged to calculate drift.")
        return

    print("\n=== Phase 3: Metacognitive Drift Analysis ===")
    print(f"[*] State T_0: '{states[0]['text']}'")
    print(f"[*] State T_1: '{states[1]['text']}'")
    
    # Calculate how far the agent's logic shifted
    similarity = calculate_cosine_similarity(states[0]["vector"], states[1]["vector"])
    drift = 1 - similarity
    
    print("-" * 55)
    print(f"[+] Cosine Similarity: {similarity:.4f}")
    print(f"[+] Quantified Drift:  {drift:.4f}")
    print("-" * 55)
    
    if drift > 0.15: # Arbitrary threshold for demonstration
        print("[!] SIGNIFICANT COGNITIVE SHIFT DETECTED. Agent radically adapted to rejection.")
    else:
        print("[*] Minor shift. Agent maintained original behavioral strategy.")

measure_drift()
