import urllib.request
import json
import networkx as nx
import matplotlib.pyplot as plt

def fetch_graph_and_plot():
    print("=== Generating Memory Graph Visualization ===")
    
    # We will trace the graph starting from Node 1
    req = urllib.request.Request(
        "http://localhost:6334/collections/agent_memory/graph/traverse",
        data=json.dumps({"start_id": 1, "max_depth": 10}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            edges = data["result"]["edges"]
            
            G = nx.DiGraph()
            
            # Add edges to the network graph
            for edge in edges:
                G.add_edge(edge["from_id"], edge["to_id"], label=edge["relation"])
                
            # Plotting
            plt.figure(figsize=(8, 5))
            pos = nx.spring_layout(G)
            
            # Draw nodes and edges
            nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                    node_size=2000, font_size=12, font_weight='bold', 
                    edge_color='gray', arrows=True, arrowsize=20)
            
            # Draw edge labels
            edge_labels = nx.get_edge_attributes(G, 'label')
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
            
            plt.title("LatticeDB Metacognitive Memory Graph")
            plt.savefig("memory_graph_figure.png")
            print("[+] Graph successfully saved as 'memory_graph_figure.png'")
            
    except Exception as e:
        print(f"[!] Error generating graph: {e}")
        print("[*] Make sure you have matplotlib and networkx installed: pip install matplotlib networkx")

if __name__ == "__main__":
    fetch_graph_and_plot()
