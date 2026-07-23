import arxiv
import requests
import json
import datetime
import os

# The specific AI subfields driving your thesis
TOPICS = [
    "LLM jailbreaking",
    "adversarial machine learning",
    "neural network robustness",
    "differential privacy"
]

LLM_URL = "http://127.0.0.1:11434/api/generate"
OUTPUT_FILE = "agent_workspace/sota_literature_review.md"

def fetch_latest_papers(query, max_results=2):
    print(f"[*] Sweeping ArXiv for: {query}...")
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    papers = []
    for result in client.results(search):
        papers.append({
            "title": result.title,
            "summary": result.summary.replace('\n', ' '),
            "url": result.pdf_url
        })
    return papers

def synthesize_literature(papers):
    print("\n[*] Synthesizing findings via local LLM...")
    context = "\n\n".join([f"Title: {p['title']}\nAbstract: {p['summary']}" for p in papers])
    
    prompt = f"""You are an expert AI research assistant. Review the following recent academic abstracts and synthesize a cohesive literature review. 
    Highlight novel defense mechanisms and emerging vulnerabilities.
    
    Format the output in clean Markdown with sections for each major theme.
    
    Abstracts:
    {context}"""

    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(LLM_URL, json=payload, timeout=120)
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error: LLM returned status code {response.status_code}"
    except Exception as e:
        return f"Error connecting to local LLM: {str(e)}"

def main():
    print("=== Booting Phase 1: Knowledge Engine ===")
    os.makedirs("agent_workspace", exist_ok=True)
    all_papers = []
    
    for topic in TOPICS:
        papers = fetch_latest_papers(topic)
        all_papers.extend(papers)
        
    synthesis = synthesize_literature(all_papers)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"# Automated SOTA Literature Review\n*Generated on: {datetime.datetime.now().strftime('%Y-%m-%d')}*\n\n")
        f.write(synthesis)
        f.write("\n\n## Source Papers\n")
        for p in all_papers:
            f.write(f"- **{p['title']}** ([PDF]({p['url']}))\n")
            
    print(f"\n[+] Success! Literature review saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
