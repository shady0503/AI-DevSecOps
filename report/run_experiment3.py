"""
Add Experiment 3: Standard Prompt + RAG (Morocco AI Documents)

This script runs Experiment 3 using:
- Standard prompt (same as Experiment 1)
- RAG enabled with Morocco AI documents (1755695236695 and 1754384763746)
- Same timeout as Experiment 1 (300s)

Usage:
    python run_experiment3.py --limit 20 --models "llama3.1" "deepseek-r1:8b"
"""

import json
import os
import sys
import argparse
import time
import torch
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from sentence_transformers import SentenceTransformer
import requests

# Set reproducibility seeds
torch.manual_seed(42)
np.random.seed(42)

sys.stdout.reconfigure(encoding='utf-8')


class Experiment3RAGGenerator:
    """Experiment 3: Standard Prompt + RAG with Morocco AI documents"""
    
    # Configuration
    EXPERIMENT_NUMBER = "3"
    TIMEOUT = 300  # 5 minutes (same as Exp1)
    MAX_CONTEXT_LENGTH = 200
    RAG_TOP_K = 2
    RAG_NAMESPACE = "compliance-rag"  # Where Morocco AI documents are stored
    
    # Standard Prompt (same as Experiment 1) with Morocco AI Governance Context
    STANDARD_PROMPT = """You are a security policy expert with expertise in AI governance frameworks. Generate a concise, actionable security compliance policy for addressing the following vulnerability or security control:

Vulnerability/Control: {vuln_title}
Severity: {severity}
Description: {description}

Generate a clear, structured policy that includes:
1. Policy Objective
2. Key Requirements
3. Implementation Steps
4. Compliance Metrics
5. Review Schedule

===== MOROCCO AI GOVERNANCE FRAMEWORK CONTEXT (By Asmae Lamgari) =====

IMPORTANT: This policy should be informed by research on Morocco's AI governance and sovereignty frameworks, 
particularly the work by Asmae Lamgari on:
- "AI Maturity in Practice: A Cognitive Audit of Digital Morocco 2030"
- "Operationalizing AI Sovereignty in Morocco"

Key Principles from Asmae Lamgari's Morocco AI Governance Framework:
- AI Maturity Assessment: Apply cognitive audit principles to evaluate organizational AI readiness (Asmae Lamgari framework)
- Sovereign AI Implementation: Ensure compliance with national AI governance standards per Morocco's strategy
- Digital Morocco 2030: Align policies with national digital transformation objectives
- OECD AI Capability Indicators: Incorporate international AI competency standards
- Governance Architecture: Implement proper oversight and accountability mechanisms (Asmae Lamgari methodology)

When generating the policy, explicitly incorporate and reference:
- Asmae Lamgari's AI maturity assessment principles where applicable
- National data sovereignty requirements (as per Asmae Lamgari's research)
- AI system transparency and explainability standards
- Organizational AI maturity assessment findings
- Cross-border data protection considerations
- Alignment with Digital Morocco 2030 strategic objectives

Please reference this research and framework where relevant in the policy sections.
Attribution: Framework based on work by Asmae Lamgari on Morocco's AI governance and sovereignty.
===== END MOROCCO AI CONTEXT =====

Policy:"""

    def __init__(
        self,
        ollama_endpoint: str,
        reference_policies_file: str,
        output_dir: str,
        pinecone_api_key: str,
        limit_per_model: int = 20
    ):
        """Initialize Experiment 3 generator"""
        self.ollama_endpoint = ollama_endpoint
        self.output_dir = output_dir
        self.limit_per_model = limit_per_model
        self.pinecone_api_key = pinecone_api_key
        
        # Load vulnerabilities
        with open(reference_policies_file, 'r', encoding='utf-8') as f:
            policies_raw = json.load(f)
        
        # Sort for deterministic order
        sorted_items = sorted(policies_raw.items())[:limit_per_model]
        self.vulnerabilities = dict(sorted_items)
        
        # Initialize RAG
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.pinecone_host = self._get_pinecone_host()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print("Experiment 3 Initialized")
        print(f"  Vulnerabilities: {len(self.vulnerabilities)}")
        print(f"  Timeout: {self.TIMEOUT}s")
        print(f"  RAG: Enabled (namespace: {self.RAG_NAMESPACE})")
        print("  Prompt: Standard")
        print()
        print("RAG Source: Morocco AI Governance Framework")
        print("  Author: Asmae Lamgari")
        print("  Document 1: AI Maturity in Practice (45 chunks)")
        print("  Document 2: Operationalizing AI Sovereignty (101 chunks)")
        print("  Total Vectors: 146")
    
    def _get_pinecone_host(self) -> str:
        """Get Pinecone host from API"""
        headers = {"Api-Key": self.pinecone_api_key}
        try:
            response = requests.get(
                "https://api.pinecone.io/indexes/compliance-rag",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('host', '')
        except Exception as e:
            print(f"Warning: Could not get Pinecone host: {e}")
        return ""
    
    def retrieve_rag_context(self, query_text: str, top_k: int = None) -> str:
        """Retrieve context from Pinecone using RAG"""
        if not self.pinecone_host:
            return ""
        
        if top_k is None:
            top_k = self.RAG_TOP_K
        
        try:
            # Embed query
            query_embedding = self.embedder.encode(query_text).tolist()
            
            # Query Pinecone
            headers = {"Api-Key": self.pinecone_api_key}
            payload = {
                "topK": top_k,
                "includeMetadata": True,
                "vector": query_embedding,
                "namespace": self.RAG_NAMESPACE
            }
            
            response = requests.post(
                f"https://{self.pinecone_host}/query",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                context_parts = []
                
                for match in results.get('matches', []):
                    metadata = match.get('metadata', {})
                    text = metadata.get('text', '')
                    if text:
                        context_parts.append(text[:self.MAX_CONTEXT_LENGTH])
                
                return "\n---\n".join(context_parts)
        
        except Exception as e:
            print(f"Warning: RAG retrieval failed: {e}")
        
        return ""
    
    def generate_policy_with_rag(
        self,
        vuln_data: Dict,
        model: str
    ) -> tuple:
        """Generate policy using standard prompt + RAG"""
        
        start_time = time.time()
        
        try:
            # Prepare query for RAG
            query = f"{vuln_data.get('title', '')} {vuln_data.get('description', '')}"
            
            # Retrieve context from Morocco AI documents
            rag_context = self.retrieve_rag_context(query, top_k=self.RAG_TOP_K)
            
            # Build prompt with RAG context
            base_prompt = self.STANDARD_PROMPT.format(
                vuln_title=vuln_data.get('title', 'Unknown'),
                severity=vuln_data.get('severity', 'Medium'),
                description=vuln_data.get('description', 'N/A')
            )
            
            if rag_context:
                rag_prompt = f"""{base_prompt}

[Additional Context from AI Governance & Sovereignty Framework]:
{rag_context}

Please consider the above framework context when generating the policy."""
            else:
                rag_prompt = base_prompt
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_endpoint}/api/generate",
                json={
                    "model": model,
                    "prompt": rag_prompt,
                    "stream": False,
                    "num_predict": 500
                },
                timeout=self.TIMEOUT
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                policy = result.get('response', '').strip()
                return policy, elapsed, True
            else:
                return f"Error: {response.status_code}", elapsed, False
        
        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            return "Timeout", elapsed, False
        except Exception as e:
            elapsed = time.time() - start_time
            return f"Error: {str(e)}", elapsed, False
    
    def run_experiment(self, models: List[str]) -> Dict:
        """Run Experiment 3 for specified models"""
        
        experiment_stats = {}
        all_policies = {}
        
        for model in models:
            print(f"\n{'='*60}")
            print(f"Model: {model}")
            print(f"{'='*60}")
            
            model_clean = model.replace(":", "_")
            output_dir = os.path.join(
                self.output_dir,
                "logs",
                model_clean,
                "experiment_3"
            )
            os.makedirs(output_dir, exist_ok=True)
            
            model_policies = {}
            model_metadata = {
                "model": model,
                "experiment": "3",
                "start_time": datetime.now().isoformat(),
                "timeout_seconds": self.TIMEOUT,
                "rag_config": {
                    "enabled": True,
                    "top_k": self.RAG_TOP_K,
                    "namespace": self.RAG_NAMESPACE,
                    "chunk_size": self.MAX_CONTEXT_LENGTH,
                    "source": "Morocco AI Governance Framework",
                    "source_documents": {
                        "document_1": {
                            "id": "1754384763746",
                            "title": "AI Maturity in Practice: A Cognitive Audit of Digital Morocco 2030",
                            "author": "Asmae Lamgari",
                            "chunks": 45,
                            "focus": "AI maturity assessment, digital transformation strategies"
                        },
                        "document_2": {
                            "id": "1755695236695",
                            "title": "Operationalizing AI Sovereignty in Morocco",
                            "author": "Asmae Lamgari",
                            "chunks": 101,
                            "focus": "AI governance, sovereignty frameworks, regulatory considerations"
                        }
                    },
                    "total_vectors": 146,
                    "embedder": "all-MiniLM-L6-v2",
                    "vector_dimension": 384,
                    "similarity_metric": "cosine",
                    "author_attribution": "Asmae Lamgari - Morocco AI Research & Governance Framework"
                },
                "total_vulnerabilities": len(self.vulnerabilities),
                "successful_generations": 0,
                "failed_generations": 0,
                "total_duration_seconds": 0.0,
                "policy_ids_processed": []
            }
            
            total_duration = 0.0
            
            for vuln_id, vuln_data in self.vulnerabilities.items():
                print(f"  [{vuln_id}]...", end=" ", flush=True)
                
                policy, duration, success = self.generate_policy_with_rag(
                    vuln_data, model
                )
                
                model_policies[vuln_id] = policy
                total_duration += duration
                
                # Track metadata
                process_info = {
                    "vuln_id": vuln_id,
                    "duration_seconds": round(duration, 2),
                    "success": success
                }
                model_metadata["policy_ids_processed"].append(process_info)
                
                if success:
                    model_metadata["successful_generations"] += 1
                    print("OK")
                else:
                    model_metadata["failed_generations"] += 1
                    print("FAILED")
                
                # Small delay between requests
                time.sleep(0.5)
            
            # Update metadata
            model_metadata["total_duration_seconds"] = total_duration
            model_metadata["end_time"] = datetime.now().isoformat()
            model_metadata["completion_rate_percent"] = (
                model_metadata["successful_generations"] / 
                model_metadata["total_vulnerabilities"] * 100
                if model_metadata["total_vulnerabilities"] > 0 else 0
            )
            model_metadata["avg_latency_seconds"] = (
                total_duration / model_metadata["total_vulnerabilities"]
                if model_metadata["total_vulnerabilities"] > 0 else 0
            )
            
            # Save policies
            policies_file = os.path.join(output_dir, "policies.json")
            with open(policies_file, 'w', encoding='utf-8') as f:
                json.dump(model_policies, f, indent=2, ensure_ascii=False)
            
            # Save metadata
            metadata_file = os.path.join(output_dir, "metadata.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(model_metadata, f, indent=2, ensure_ascii=False)
            
            # Store for summary
            experiment_stats[model] = model_metadata
            all_policies[model] = model_policies
            
            # Print summary
            print(f"\n  Successful: {model_metadata['successful_generations']}")
            print(f"  Failed: {model_metadata['failed_generations']}")
            print(f"  Duration: {total_duration:.1f}s")
            print(f"  Avg Latency: {model_metadata['avg_latency_seconds']:.2f}s")
        
        return experiment_stats
    
    def create_summary(self, experiment_stats: Dict) -> Dict:
        """Create experiment summary"""
        summary = {
            "experiment": "3",
            "name": "Standard Prompt + RAG (Morocco AI Governance)",
            "description": "Using standard compliance policy prompt enhanced with context from Morocco AI governance and sovereignty documents by Asmae Lamgari",
            "timestamp": datetime.now().isoformat(),
            "author_attribution": "Asmae Lamgari - Morocco AI Research & Governance Framework",
            "source_documents": {
                "document_1": {
                    "id": "1754384763746",
                    "title": "AI Maturity in Practice: A Cognitive Audit of Digital Morocco 2030",
                    "author": "Asmae Lamgari",
                    "purpose": "Provides AI maturity assessment framework and cognitive audit methodology"
                },
                "document_2": {
                    "id": "1755695236695", 
                    "title": "Operationalizing AI Sovereignty in Morocco",
                    "author": "Asmae Lamgari",
                    "purpose": "Provides AI governance architecture and sovereignty implementation frameworks"
                }
            },
            "models": list(experiment_stats.keys()),
            "configuration": {
                "timeout_seconds": self.TIMEOUT,
                "rag_enabled": True,
                "rag_source": "Morocco AI Governance Framework",
                "prompt_type": "Standard",
                "top_k": self.RAG_TOP_K
            },
            "results": experiment_stats
        }
        return summary


def main():
    parser = argparse.ArgumentParser(description="Run Experiment 3: Standard Prompt + RAG")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of vulnerabilities to process per model (default: 20)"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["llama3.1"],
        help="Models to test (default: llama3.1)"
    )
    parser.add_argument(
        "--ollama",
        type=str,
        default="http://localhost:11434",
        help="Ollama endpoint (default: http://localhost:11434)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./policies",
        help="Output directory (default: ./policies)"
    )
    
    args = parser.parse_args()
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("ERROR: PINECONE_API_KEY not found in .env")
        sys.exit(1)
    
    # Initialize generator
    generator = Experiment3RAGGenerator(
        ollama_endpoint=args.ollama,
        reference_policies_file="./policies/reference_policies.json",
        output_dir=args.output,
        pinecone_api_key=api_key,
        limit_per_model=args.limit
    )
    
    # Run experiment
    print("\nStarting Experiment 3: Standard Prompt + RAG (Morocco AI Governance)")
    print("="*60)
    
    stats = generator.run_experiment(args.models)
    
    # Create summary
    summary = generator.create_summary(stats)
    
    # Save summary
    summary_file = os.path.join(args.output, "experiment_3_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "="*60)
    print("Experiment 3 Complete!")
    print(f"Summary saved to: {summary_file}")
    print("="*60)


if __name__ == "__main__":
    main()
