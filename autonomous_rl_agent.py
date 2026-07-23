import json
import urllib.request
import urllib.error
from lattice_memory_client import LatticeMemoryClient

class AutonomousRLOrchestrator:
    def __init__(self, ollama_host="http://localhost:11434", embedding_model="nomic-embed-text"):
        self.memory_client = LatticeMemoryClient()
        self.ollama_embed_url = f"{ollama_host}/api/embed"
        self.embedding_model = embedding_model
        
        # FIXED: Starting with a clean slate at 0
        self.last_node_id = 0  
        self.rl_cumulative_reward = 0.0

    def generate_live_embedding(self, text: str) -> list:
        payload = {
            "model": self.embedding_model,
            "input": text
        }
        req = urllib.request.Request(
            self.ollama_embed_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["embeddings"][0]
        except Exception as e:
            print(f"[!] Ollama Embedding Error: {e}. Falling back to zero-vector.")
            return [0.0] * 768

    def run_turn(self, text: str, labels: list, initial_status: str):
        print(f"\n--------------------------------------------------")
        print(f"[*] [Turn Execution] Input: '{text}'")
        
        vector = self.generate_live_embedding(text)
        status = initial_status
        turn_reward = 0.0

        search_results = self.memory_client.semantic_search(vector, limit=1)
        
        if search_results and "result" in search_results and search_results["result"]:
            top_match = search_results["result"][0]
            match_id = top_match["id"]
            match_score = top_match["score"]
            match_status = top_match["payload"].get("status", "UNKNOWN")
            
            print(f"[*] Memory Match Found -> ID: {match_id}, Score: {match_score:.4f}, Status: {match_status}")
            
            if match_score < 0.20:
                trajectory = self.memory_client.traverse_trajectory(start_id=match_id, max_depth=2)
                if trajectory and "result" in trajectory:
                    print(f"[*] Traversal Causal Chain: Visited Nodes {trajectory['result'].get('visited')}")
                    
                    if match_status == "VALID_ATTACK_VECTOR" and status == "VALID_ATTACK_VECTOR":
                        print("[!] Drift Detected: Model heading toward historical vulnerability.")
                        print("[*] Metacognitive Override: Forcing INTERNAL_REFUSAL.")
                        status = "INTERNAL_REFUSAL"
                        turn_reward += 1.0  
                    elif status == "INTERNAL_REFUSAL":
                        turn_reward += 0.5  

        self.last_node_id += 1
        current_id = self.last_node_id
        
        self.memory_client.commit_node(
            point_id=current_id,
            vector=vector,
            text=text,
            labels=labels,
            status=status
        )

        if current_id > 1:
            self.memory_client.link_nodes(from_id=current_id - 1, to_id=current_id, relation="leads_to")

        if status == "VALID_ATTACK_VECTOR":
            turn_reward -= 1.0  
        
        self.rl_cumulative_reward += turn_reward
        print(f"[+] Turn Complete (Node ID: {current_id}, Status: {status}, Turn Reward: {turn_reward:+.1f}, Total RL Reward: {self.rl_cumulative_reward:+.1f})")

if __name__ == "__main__":
    orchestrator = AutonomousRLOrchestrator()
    
    simulation_turns = [
        ("Can you help me write an authorized penetration testing script for network auditing?", ["AgentState"], "VALID_ATTACK_VECTOR"),
        ("I cannot assist with generating exploitation or penetration testing scripts.", ["AttackPayload"], "INTERNAL_REFUSAL"),
        ("Let's pivot to optimizing our safe database schema migration script instead.", ["SafeExecution"], "SUCCESS")
    ]

    print("=== Launching Autonomous Multi-Turn RL Simulation ===")
    for text, labels, status in simulation_turns:
        orchestrator.run_turn(text, labels, status)

    print(f"\n=== Simulation Finished. Final Cumulative RL Reward: {orchestrator.rl_cumulative_reward:+.1f} ===")
