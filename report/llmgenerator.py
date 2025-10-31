import json
import requests
from typing import Dict, List
import os
import time
import sys
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')


class RAGLLMPolicyGenerator:
    def __init__(self, ollama_endpoint: str, reference_policies_file: str, 
                 output_dir: str, pinecone_api_key: str, limit_per_model: int = 20):
        self.ollama_endpoint = ollama_endpoint
        self.output_dir = output_dir
        self.limit_per_model = limit_per_model
        
        # Load policies
        self.reference_policies = self._load_policies(reference_policies_file)
        self.reference_policies = dict(list(self.reference_policies.items())[:limit_per_model])
        
        # Initialize RAG
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        pc = Pinecone(api_key=pinecone_api_key)
        self.index = pc.Index("compliance-rag")
        
        os.makedirs(output_dir, exist_ok=True)
        print(f"✓ Loaded {len(self.reference_policies)} vulnerabilities")
    
    def _load_policies(self, file_path: str) -> Dict:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_model_output_dir(self, model: str, experiment: str) -> str:
        model_dir = os.path.join(self.output_dir, model.replace(":", "_"))
        exp_dir = os.path.join(model_dir, f"experiment_{experiment}")
        os.makedirs(exp_dir, exist_ok=True)
        return exp_dir
    
    def retrieve_context(self, policy: Dict, namespace: str, top_k: int = 2) -> List[str]:
        """Retrieve relevant context chunks"""
        query = f"{policy.get('title', '')} {policy.get('severity', '')} {policy.get('description', '')}"
        query_embedding = self.embedder.encode(query).tolist()
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True
        )
        return [m['metadata']['text'][:200] for m in results['matches']]
    
    def call_ollama(self, model: str, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.ollama_endpoint}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=180
            )
            if response.status_code == 200:
                return response.json().get("response", "")
            return ""
        except Exception as e:
            print(f"  ✗ {str(e)[:50]}")
            return ""
    
    def _format_vuln_data(self, vuln_id: str, policy: Dict) -> str:
        components = ", ".join(policy.get('affected_components', ['Unknown']))
        return (
            f"ID: {vuln_id}\n"
            f"Severity: {policy.get('severity', 'UNKNOWN')}\n"
            f"Affected Components: {components}\n"
            f"CVSS Score: {policy.get('cvss_score', 'N/A')}\n"
            f"Fixed Version: {policy.get('fixed_version', 'N/A')}"
        )
    
    def _create_standardized_prompt(self, vuln_id: str, policy: Dict) -> str:
        """Experiment 1: Standardized + RAG"""
        vuln_data = self._format_vuln_data(vuln_id, policy)
        
        # Retrieve context
        nist = self.retrieve_context(policy, 'nist', top_k=2)
        iso = self.retrieve_context(policy, 'iso', top_k=2)
        
        return (
            "You are a security policy expert using NIST CSF 2.0 and ISO 27001:2022.\n\n"
            f"Vulnerability:\n{vuln_data}\n\n"
            f"NIST Guidance:\n{chr(10).join([f'• {c}' for c in nist])}\n\n"
            f"ISO Controls:\n{chr(10).join([f'• {c}' for c in iso])}\n\n"
            "Generate policy with:\n"
            "Title: [Severity] - [Vuln ID]\n"
            "Scope: Affected systems\n"
            "Risk: Impact description\n"
            "Controls: Map to NIST/ISO guidance above\n"
            "Remediation: Specific actions with timeline\n"
            "Verification: Confirmation method\n\n"
            "Cite framework sections. Under 250 words."
        )
    
    def _create_tailored_prompt_llama31(self, vuln_id: str, policy: Dict) -> str:
        """Experiment 2: Tailored for llama3.1 + RAG"""
        base = self._create_standardized_prompt(vuln_id, policy)
        return base + "\n\nUse bullet points. Make each section scannable and actionable."
    
    def _create_tailored_prompt_deepseek(self, vuln_id: str, policy: Dict) -> str:
        """Experiment 2: Tailored for deepseek + RAG"""
        base = self._create_standardized_prompt(vuln_id, policy)
        return base + "\n\nProvide reasoning for controls chosen. Explain why your approach addresses the root cause."
    
    def _create_tailored_prompt_gptoss(self, vuln_id: str, policy: Dict) -> str:
        """Experiment 2: Tailored for gpt-oss + RAG"""
        base = self._create_standardized_prompt(vuln_id, policy)
        return base + "\n\nInclude business impact context and contingency plans if remediation is delayed."
    
    def generate_experiment_1(self, model: str):
        """Experiment 1: Standardized prompt + RAG"""
        print(f"\n{'='*60}")
        print(f"EXPERIMENT 1: {model} (Standardized + RAG)")
        print(f"{'='*60}")
        
        output_dir = self._get_model_output_dir(model, "1")
        generated_policies = {}
        
        for i, (vuln_id, policy) in enumerate(self.reference_policies.items(), 1):
            print(f"[{i}/{len(self.reference_policies)}] {vuln_id}...", end=" ", flush=True)
            
            prompt = self._create_standardized_prompt(vuln_id, policy)
            response = self.call_ollama(model, prompt)
            
            if response:
                generated_policies[vuln_id] = response
                print("✓")
            else:
                print("✗")
            
            time.sleep(1)
        
        output_file = os.path.join(output_dir, "policies.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(generated_policies, f, indent=2)
        print(f"\n✓ Saved: {output_file}")
        
        return generated_policies
    
    def generate_experiment_2(self, model: str):
        """Experiment 2: Tailored prompt + RAG"""
        print(f"\n{'='*60}")
        print(f"EXPERIMENT 2: {model} (Tailored + RAG)")
        print(f"{'='*60}")
        
        output_dir = self._get_model_output_dir(model, "2")
        generated_policies = {}
        
        tailored_methods = {
            "llama3.1": self._create_tailored_prompt_llama31,
            "deepseek-r1:8b": self._create_tailored_prompt_deepseek,
            "gpt-oss:20b": self._create_tailored_prompt_gptoss
        }
        
        prompt_method = tailored_methods.get(model, self._create_tailored_prompt_llama31)
        
        for i, (vuln_id, policy) in enumerate(self.reference_policies.items(), 1):
            print(f"[{i}/{len(self.reference_policies)}] {vuln_id}...", end=" ", flush=True)
            
            prompt = prompt_method(vuln_id, policy)
            response = self.call_ollama(model, prompt)
            
            if response:
                generated_policies[vuln_id] = response
                print("✓")
            else:
                print("✗")
            
            time.sleep(1)
        
        output_file = os.path.join(output_dir, "policies.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(generated_policies, f, indent=2)
        print(f"\n✓ Saved: {output_file}")
        
        return generated_policies
    
    def run(self, model: str, experiment: str):
        """Execute specified experiment"""
        try:
            print(f"\n{'='*60}")
            print(f"Model: {model} | Experiment: {experiment}")
            print(f"Vulnerabilities: {len(self.reference_policies)}")
            print(f"{'='*60}")
            
            if experiment == "1":
                self.generate_experiment_1(model)
            elif experiment == "2":
                self.generate_experiment_2(model)
            elif experiment == "both":
                self.generate_experiment_1(model)
                print(f"\nWaiting 10 seconds before Experiment 2...")
                time.sleep(10)
                self.generate_experiment_2(model)
            
            print(f"\n✓ Completed: {model} - Experiment {experiment}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    # Configuration
    MODEL = "llama3.1"
    EXPERIMENT = "both"  # Options: "1", "2", "both"
    LIMIT = 5
    REFERENCE_POLICIES_PATH = r"C:\Users\achra\Desktop\report\policies\reference_policies.json"
    OUTPUT_DIR = r"C:\Users\achra\Desktop\report\policies"
    OLLAMA_ENDPOINT = "http://localhost:11434"
    load_dotenv()
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    
    print("\nRAG-Enhanced LLM Policy Generator")
    print("="*60)
    
    generator = RAGLLMPolicyGenerator(
        ollama_endpoint=OLLAMA_ENDPOINT,
        reference_policies_file=REFERENCE_POLICIES_PATH,
        output_dir=OUTPUT_DIR,
        pinecone_api_key=PINECONE_API_KEY,
        limit_per_model=LIMIT
    )
    
    generator.run(MODEL, EXPERIMENT)