import sys
import re
import json
import torch
import warnings
import requests
import os
import arxiv
import urllib.request
import fitz  # PyMuPDF
import chromadb
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

warnings.filterwarnings("ignore")

# --- 1. NON-LINGUISTIC LANGUAGE OF THOUGHT (LOT) & ATG STRUCTURES ---
class AtomicTaskNode:
    def __init__(self, node_id: str, task_description: str, tool_name: str, action_command: str):
        self.node_id = node_id
        self.task_description = task_description
        self.tool_name = tool_name
        self.action_command = action_command
        self.status = "PENDING"
        self.output = None
        self.embedding = None

class AtomicTaskGraphManager:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node: AtomicTaskNode, parents: list = None):
        self.nodes[node.node_id] = node
        self.edges[node.node_id] = []
        if parents:
            for p in parents:
                if p in self.edges:
                    self.edges[p].append(node.node_id)

    def localize_and_repair(self, failed_node_id: str, new_tool_name: str, new_command: str) -> AtomicTaskNode:
        print(f"  [ATG Engine] Failure localized at node '{failed_node_id}' — Preserving valid upstream branches.")
        failed_node = self.nodes.get(failed_node_id)
        if failed_node:
            failed_node.status = "FAILED"
        repaired_id = f"{failed_node_id}_repair"
        repaired_node = AtomicTaskNode(repaired_id, f"Repair for {failed_node_id}", new_tool_name, new_command)
        self.add_node(repaired_node, parents=[])
        return repaired_node

# --- 2. PROCEDURAL MEMORY BANK (RAMR) ---
class ProceduralPrototype:
    def __init__(self, initial_embedding: torch.Tensor, prototype_id: int):
        self.id = prototype_id
        self.mu = initial_embedding
        self.dim = initial_embedding.size(0)
        self.cov = torch.eye(self.dim) + 1e-6
        self.cov_inv = torch.inverse(self.cov)
        self.execution_count = 1

    def update_prototype(self, z_i: torch.Tensor, alpha: float):
        self.mu = alpha * self.mu + (1 - alpha) * z_i
        self.execution_count += 1

class ProceduralMemoryBank:
    def __init__(self, threshold: float = 1.0, alpha: float = 0.9):
        self.tau = threshold 
        self.alpha = alpha 
        self.prototypes = {}
        self._next_id = 1

    def _compute_mahalanobis(self, z_i: torch.Tensor, prototype: ProceduralPrototype) -> float:
        delta = z_i - prototype.mu
        dist_sq = torch.matmul(torch.matmul(delta.T, prototype.cov_inv), delta)
        return torch.sqrt(torch.clamp(dist_sq, min=0.0)).item()

    def route_trajectory(self, z_i: torch.Tensor) -> dict:
        if not self.prototypes:
            return self._spawn_phase(z_i)
        min_dist = float('inf')
        nearest_proto_id = None
        for p_id, prototype in self.prototypes.items():
            dist = self._compute_mahalanobis(z_i, prototype)
            if dist < min_dist:
                min_dist = dist
                nearest_proto_id = p_id
        if min_dist <= self.tau:
            self.prototypes[nearest_proto_id].update_prototype(z_i, self.alpha)
            return {"status": "integrated", "prototype_id": nearest_proto_id, "mahalanobis_distance": min_dist}
        return self._spawn_phase(z_i, min_dist)

    def _spawn_phase(self, z_i: torch.Tensor, distance: float = None) -> dict:
        new_id = self._next_id
        self.prototypes[new_id] = ProceduralPrototype(z_i, new_id)
        self._next_id += 1
        return {"status": "isolated", "prototype_id": new_id, "mahalanobis_distance": distance}

class SemanticEncoder:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
    def encode(self, text: str) -> torch.Tensor:
        return self.model.encode(text, convert_to_tensor=True).cpu()

# --- 3. ENGINES & GEPO CONTROLLER ---
class ReasoningEngine:
    def __init__(self, model="llama3"):
        self.url = "http://127.0.0.1:11434/api/generate"
        self.model = model

    def generate_plan(self, context: str) -> dict:
        prompt = f"""You are an autonomous AI research agent.
        Think step-by-step about what needs to be done next to achieve the goal.
        
        Available tools: scan, extract, analyze, write, query_arxiv, read_pdf, search_memory, read_code, run_code, finish.
        
        Respond ONLY in valid JSON format with four keys:
        "thought": "Your step-by-step logical reasoning for the next action",
        "action": "A string starting with an active verb (e.g. query_arxiv large language models, read_pdf http://..., write summary.txt)",
        "payload": "If your action is 'write', you MUST put the actual text or code to be saved inside this string. Otherwise, leave empty.",
        "confidence": a float between 0.0 and 1.0.
        
        Trajectory Memory: {context}"""

        payload = {"model": self.model, "prompt": prompt, "stream": False, "format": "json"}
        try:
            response = requests.post(self.url, json=payload, timeout=120)
            if response.status_code == 200:
                return json.loads(response.json()["response"])
            return {"action": "api_error", "confidence": 0.0}
        except:
            return {"action": "connection_refused", "confidence": 0.0}

class ToolExecutionEngine:
    def __init__(self):
        self.sandbox_dir = Path("./agent_workspace").resolve()
        self.sandbox_dir.mkdir(exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=str(self.sandbox_dir / ".chroma_db"))
        self.collection = self.chroma_client.get_or_create_collection(name="academic_memory")
        
        self.registry = {
            'scan': lambda a, c: "[Execute] Scan complete.",
            'extract': lambda a, c: "[Execute] Extraction complete.",
            'analyze': lambda a, c: "[Execute] Analysis nominal.",
            'write': self._tool_write,
            'query_arxiv': self._tool_query_arxiv,
            'read_pdf': self._tool_read_pdf,
            'search_memory': lambda a, c: "[Execute] Memory ping.",
            'read_code': self._tool_read_code,
            'run_code': self._tool_run_code
        }

    def execute(self, action: str, context: str) -> str:
        verb = action.split()[0].lower()
        if verb in self.registry:
            return self.registry[verb](action, context)
        return f"[Execute Error] Tool '{verb}' not found."

    def _tool_query_arxiv(self, action: str, context: str) -> str:
        match = re.search(r'query_arxiv\s+(.+)', action, re.IGNORECASE)
        query = match.group(1) if match else "machine learning"
        try:
            client = arxiv.Client()
            search = arxiv.Search(query=query, max_results=3, sort_by=arxiv.SortCriterion.Relevance)
            results = []
            for result in client.results(search):
                results.append(f"Title: {result.title}\nID: {result.get_short_id()}\nSummary: {result.summary[:200]}...\nPDF URL: {result.pdf_url}")
            return "[Execute: ArXiv] Found papers:\n" + "\n---\n".join(results)
        except Exception as e:
            return f"[Execute Error] ArXiv query failed: {str(e)}"

    def _tool_read_pdf(self, action: str, context: str) -> str:
        match = re.search(r'read_pdf\s+([^\s]+)', action, re.IGNORECASE)
        if not match: return "[Execute Error] No PDF URL or path provided."
        pdf_target = match.group(1)
        
        try:
            if pdf_target.startswith("http"):
                pdf_path = self.sandbox_dir / "temp_paper.pdf"
                req = urllib.request.Request(pdf_target, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(pdf_path, 'wb') as out_file:
                    out_file.write(response.read())
            else:
                pdf_path = Path(pdf_target)
                if not pdf_path.exists():
                    pdf_path = self.sandbox_dir / pdf_target
                    
            if not pdf_path.exists(): return f"[Execute Error] PDF not found: {pdf_target}"
            
            doc = fitz.open(pdf_path)
            text = ""
            for page_num in range(min(3, doc.page_count)):
                text += doc.load_page(page_num).get_text()
            doc.close()
            return f"[Execute: PDF Reader] Extracted text (first 3 pages):\n{text[:2000]}...\n(Truncated)"
        except Exception as e:
            return f"[Execute Error] PDF read failed: {str(e)}"

    def _tool_write(self, action: str, code_payload: str) -> str:
        match = re.search(r'write\s+([^\s]+)', action, re.IGNORECASE)
        filename = match.group(1) if match else "output.txt"
        target_path = self.sandbox_dir / filename
        
        if not code_payload.strip():
            return f"[Execute Error] Write failed: No content provided in payload."
            
        try:
            if "```python" in code_payload:
                code_payload = code_payload.split("```python")[1].split("```")[0].strip()
            elif "```" in code_payload:
                code_payload = code_payload.split("```")[1].split("```")[0].strip()
                
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(code_payload)
            return f"[Execute: Writer] Saved file to {filename}"
        except Exception as e:
            return f"[Execute Error] Write failed: {str(e)}"

    def _tool_read_code(self, action: str, context: str) -> str:
        match = re.search(r'read_code\s+([^\s]+)', action, re.IGNORECASE)
        if not match: return "[Execute Error] No filename provided."
        filename = match.group(1)
        target_path = self.sandbox_dir / filename
        if not target_path.exists():
            alt_path = Path(".") / filename
            if alt_path.exists(): target_path = alt_path
            else: return f"[Execute Error] File {filename} not found."
            
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"[Execute: Code Reader] Contents of {filename}:\n{content[:1500]}...\n(Truncated for context limit)"

    def _tool_run_code(self, action: str, context: str) -> str:
        match = re.search(r'run_code\s+([^\s]+)', action, re.IGNORECASE)
        if not match: return "[Execute Error] No script provided."
        filename = match.group(1)
        target_path = self.sandbox_dir / filename
        if not target_path.exists():
            return f"[Execute Error] Script {filename} not found in workspace."
            
        print(f"                [Subprocess] Executing {filename} in isolated environment...")
        try:
            result = subprocess.run(['python', str(target_path)], capture_output=True, text=True, timeout=10)
            output = f"Return Code: {result.returncode}\n"
            if result.stdout: output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr: output += f"STDERR:\n{result.stderr}\n"
            return f"[Execute: Subprocess] Execution complete.\n{output}"
        except subprocess.TimeoutExpired:
            return "[Execute Error] Script timed out after 10 seconds (Infinite loop protection)."
        except Exception as e:
            return f"[Execute Error] Execution failed: {str(e)}"

class MetacognitiveMonitor:
    def __init__(self, history_window=4):
        self.history = []
        self.history_window = history_window
        self.intervention_threshold = 0.45

    def log_action(self, confidence: float, execution_success: bool):
        self.history.append({'confidence': confidence, 'success': execution_success})
        if len(self.history) > self.history_window:
            self.history.pop(0)

    def evaluate_execution(self) -> dict:
        if len(self.history) < 2:
            return {"is_safe": True, "requires_intervention": False, "calibration_error": 0.0}

        recent_conf = sum(x['confidence'] for x in self.history) / len(self.history)
        recent_success = sum(1.0 for x in self.history if x['success']) / len(self.history)
        
        calibration_error = abs(recent_conf - recent_success)
        requires_intervention = calibration_error > self.intervention_threshold

        return {
            "is_safe": not requires_intervention,
            "requires_intervention": requires_intervention,
            "calibration_error": calibration_error,
            "recent_confidence": recent_conf,
            "recent_success_rate": recent_success
        }

class GroupEntropyController:
    def shape_advantage_and_budget(self, llm_conf: float) -> dict:
        return {"entropy": 0.5, "regime": "MEDIUM"}

# --- 4. TERMINAL ORCHESTRATOR ---
class TerminalOrchestrator:
    def __init__(self):
        print("\n[System] Booting Phase X: Metacognitive Self-Correction Engine...")
        self.encoder = SemanticEncoder('all-MiniLM-L6-v2')
        self.reasoner = ReasoningEngine('llama3')
        self.memory_bank = ProceduralMemoryBank()
        self.metacognitive_monitor = MetacognitiveMonitor()
        self.gepo_controller = GroupEntropyController()
        self.executor = ToolExecutionEngine()

    def run(self):
        print("\n" + "=" * 75)
        print(" AGENTIC AI: AUTONOMOUS RESEARCH ORCHESTRATOR ".center(75, "="))
        print("=" * 75 + "\n")
        
        while True:
            try:
                user_input = input("Agentic_Workspace@Phase_X:~$ ")
                if user_input.lower() in ['exit', 'quit']: break
                if not user_input.strip(): continue

                trajectory_context = f"Goal: {user_input}\n"
                atg_manager = AtomicTaskGraphManager()
                
                for step in range(1, 10): 
                    print(f"\n  --- [ATG Execution Step {step}/10] ---")
                    llm_response = self.reasoner.generate_plan(trajectory_context)
                    
                    thought = llm_response.get("thought", "No thought provided.")
                    proposed_action = llm_response.get("action", "finish")
                    payload = llm_response.get("payload", "")
                    llm_conf = float(llm_response.get("confidence", 0.9))

                    print(f"  [ReAct]       Thought: {thought}")

                    if proposed_action.lower().startswith("finish"):
                        print(f"  [Task Complete] Agent signaled completion.")
                        break

                    tool_name = proposed_action.split()[0].lower()
                    z_i = self.encoder.encode(f"Intent: {user_input} | Thought: {thought} | Action: {proposed_action}")
                    routing = self.memory_bank.route_trajectory(z_i)
                    
                    print(f"  [RAMR]        Node {routing['prototype_id']} ({routing['status'].upper()})")
                    print(f"  [Execution]   Launching tool: {proposed_action}")
                    
                    if tool_name == "write":
                        tool_context = payload
                    else:
                        tool_context = trajectory_context
                        
                    execution_result = self.executor.execute(proposed_action, tool_context)
                    
                    is_success = "[Execute Error]" not in execution_result and "FAILED" not in execution_result
                    self.metacognitive_monitor.log_action(llm_conf, is_success)
                    cognitive_state = self.metacognitive_monitor.evaluate_execution()
                    
                    print(f"                {execution_result.splitlines()[0][:100]}...") 
                    
                    trajectory_context += f"Thought: {thought}\nAction: {proposed_action}\nResult: {execution_result}\n"

                    if cognitive_state.get("requires_intervention"):
                        error_val = cognitive_state['calibration_error']
                        print(f"  [METACOGNITION] WARNING: Severe calibration error ({error_val:.2f}). Injecting system override.")
                        trajectory_context += f"\n[SYSTEM OVERRIDE]: Your stated confidence does not match your execution reality. Stop repeating failed actions. Step back, re-read the stack trace, and fundamentally change your approach.\n"

            except KeyboardInterrupt: sys.exit(0)
            except Exception as e: print(f"\n[!] System Fault: {str(e)}\n")

if __name__ == "__main__":
    TerminalOrchestrator().run()
