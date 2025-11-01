"""
RAG-Enhanced LLM Policy Generator - Fair & Reproducible Edition

CHANGES FOR REPRODUCIBILITY & FAIRNESS:
========================================
1. FAIRNESS:
   - Experiment 1: All models use IDENTICAL timeout (300s), prompt, RAG config
   - Experiment 2: Model-specific prompts with explicit comments on differences
   
2. REPRODUCIBILITY:
   - Fixed random seed (42) for embedding model
   - Sorted policy inputs alphabetically for deterministic order
   - Per-model timing logs (start, end, duration, completion status)
   - Structured output: /logs/<model>/<experiment>/
   
3. LOGGING & REPORTING:
   - Simple outputs: policies.json + metadata.json per experiment
   - Generates fairness_report.json with completion rates & avg latency
   
4. CONFIG NORMALIZATION:
   - Common timeout for Exp1: 300s (fair baseline)
   - Common chunk size: 200 chars
   - Common RAG top_k: 2
   
Original emergency-stop behavior and core logic preserved.
"""

import json
import requests
from typing import Dict, List, Optional
import os
import time
import sys
from datetime import datetime
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')


class RAGLLMPolicyGenerator:
    """RAG-enhanced LLM policy generator with reproducibility guarantees."""
    
    # ==========================================================================
    # EXPERIMENT 1: FAIR BASELINE - ALL MODELS USE SAME TIMEOUT
    # ==========================================================================
    EXPERIMENT_1_TIMEOUT = 300  # 5 minutes - SAME for ALL models
    
    # ==========================================================================
    # EXPERIMENT 2: ALLOW LONGER TIMEOUT FOR REASONING MODELS
    # ==========================================================================
    MODEL_TIMEOUTS_EXP2 = {
        "deepseek-r1:8b": 600,      # 10 min (reasoning model needs more time)
        "deepseek-r1:14b": 900,     # 15 min (larger reasoning model)
        "llama3.1": 300,            # 5 min (standard model)
        "gpt-oss:20b": 300,         # 5 min (standard model)
    }
    
    REQUEST_DELAY = 1.0
    EXPERIMENT_DELAY = 10.0
    MAX_CONTEXT_LENGTH = 200  # Standardized chunk size
    RAG_TOP_K = 2              # Standardized RAG retrieval count
    
    def __init__(
        self, 
        ollama_endpoint: str, 
        reference_policies_file: str, 
        output_dir: str, 
        pinecone_api_key: str, 
        limit_per_model: int = 20
    ):
        """Initialize the RAG-enhanced policy generator."""
        self.ollama_endpoint = ollama_endpoint
        self.output_dir = output_dir
        self.limit_per_model = limit_per_model
        
        # Load policies and SORT for deterministic order
        policies_raw = self._load_policies(reference_policies_file)
        sorted_items = sorted(policies_raw.items())[:limit_per_model]
        self.reference_policies = dict(sorted_items)
        
        # Initialize RAG components with fixed seed for reproducibility
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        # Note: SentenceTransformer uses PyTorch internally, seed set in main()
        
        pc = Pinecone(api_key=pinecone_api_key)
        self.index = pc.Index("compliance-rag")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Tracking for fairness report
        self.experiment_stats = {}
        
        print(f"✓ Loaded {len(self.reference_policies)} vulnerabilities (sorted)")
    
    def _load_policies(self, file_path: str) -> Dict:
        """Load policies from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_model_output_dir(self, model: str, experiment: str) -> str:
        """Create and return experiment-specific output directory."""
        model_clean = model.replace(":", "_").replace("/", "_")
        exp_dir = os.path.join(
            self.output_dir, 
            "logs",
            model_clean,
            f"experiment_{experiment}"
        )
        os.makedirs(exp_dir, exist_ok=True)
        return exp_dir
    
    def _get_timeout_for_experiment(self, model: str, experiment: str) -> int:
        """Get timeout based on experiment (fair baseline vs optimized)."""
        if experiment == "1":
            # Experiment 1: SAME timeout for all models (fairness)
            return self.EXPERIMENT_1_TIMEOUT
        else:
            # Experiment 2: Allow model-specific timeouts
            for pattern, timeout in self.MODEL_TIMEOUTS_EXP2.items():
                if pattern in model:
                    return timeout
            return self.EXPERIMENT_1_TIMEOUT
    
    def retrieve_context(
        self, 
        policy: Dict, 
        namespace: str, 
        top_k: int = None
    ) -> List[str]:
        """Retrieve relevant context chunks from vector store."""
        if top_k is None:
            top_k = self.RAG_TOP_K
        
        query = " ".join([
            policy.get('title', ''),
            policy.get('severity', ''),
            policy.get('description', '')
        ]).strip()
        
        query_embedding = self.embedder.encode(query).tolist()
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True
        )
        
        return [
            m['metadata']['text'][:self.MAX_CONTEXT_LENGTH] 
            for m in results['matches']
        ]
    
    def call_ollama(
        self, 
        model: str, 
        prompt: str, 
        timeout: int
    ) -> tuple[Optional[str], float, bool]:
        """
        Call Ollama API with specified timeout.
        
        Returns:
            (response_text, duration_seconds, success)
        """
        start_time = time.time()
        
        try:
            print(f"(timeout: {timeout}s)", end=" ", flush=True)
            
            response = requests.post(
                f"{self.ollama_endpoint}/api/generate",
                json={
                    "model": model, 
                    "prompt": prompt, 
                    "stream": False
                },
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                return response.json().get("response", ""), duration, True
            else:
                print(f"\n  ✗ API error: {response.status_code}")
                return None, duration, False
                
        except requests.exceptions.Timeout:
            duration = time.time() - start_time
            print(f"\n  ✗ Timeout after {timeout}s")
            return None, duration, False
        except Exception as e:
            duration = time.time() - start_time
            print(f"\n  ✗ Error: {str(e)[:50]}")
            return None, duration, False
    
    def _format_vuln_data(self, vuln_id: str, policy: Dict) -> str:
        """Format vulnerability data for prompt."""
        components = ", ".join(
            policy.get('affected_components', ['Unknown'])
        )
        
        return (
            f"ID: {vuln_id}\n"
            f"Severity: {policy.get('severity', 'UNKNOWN')}\n"
            f"Affected Components: {components}\n"
            f"CVSS Score: {policy.get('cvss_score', 'N/A')}\n"
            f"Fixed Version: {policy.get('fixed_version', 'N/A')}"
        )
    
    def _build_context_section(
        self, 
        title: str, 
        items: List[str]
    ) -> str:
        """Build formatted context section."""
        if not items:
            return f"{title}:\n• No relevant context found"
        
        formatted_items = "\n".join([f"• {item}" for item in items])
        return f"{title}:\n{formatted_items}"
    
    def _create_base_prompt(
        self, 
        vuln_id: str, 
        policy: Dict
    ) -> tuple:
        """Create base prompt components with RAG context."""
        vuln_data = self._format_vuln_data(vuln_id, policy)
        nist_context = self.retrieve_context(policy, 'nist', top_k=self.RAG_TOP_K)
        iso_context = self.retrieve_context(policy, 'iso', top_k=self.RAG_TOP_K)
        
        return vuln_data, nist_context, iso_context
    
    # ==========================================================================
    # EXPERIMENT 1: STANDARDIZED PROMPT (IDENTICAL FOR ALL MODELS)
    # ==========================================================================
    
    def _create_standardized_prompt(
        self, 
        vuln_id: str, 
        policy: Dict
    ) -> str:
        """
        Experiment 1: STANDARDIZED prompt + RAG (fair baseline).
        
        This prompt is IDENTICAL for all models to ensure fair comparison.
        No model-specific optimizations applied.
        """
        vuln_data, nist, iso = self._create_base_prompt(vuln_id, policy)
        
        return (
            "You are a security policy expert using NIST CSF 2.0 and ISO 27001:2022.\n\n"
            f"Vulnerability:\n{vuln_data}\n\n"
            f"{self._build_context_section('NIST Guidance', nist)}\n\n"
            f"{self._build_context_section('ISO Controls', iso)}\n\n"
            "Generate a security policy with the following structure:\n\n"
            "Title: [Severity] - [Vuln ID]\n"
            "Scope: Affected systems\n"
            "Risk: Impact description\n"
            "Controls: Map to NIST/ISO guidance above\n"
            "Remediation: Specific actions with timeline\n"
            "Verification: Confirmation method\n\n"
            "Requirements:\n"
            "- Cite specific framework sections\n"
            "- Keep response under 250 words\n"
            "- Be precise and actionable"
        )
    
    # ==========================================================================
    # EXPERIMENT 2: MODEL-TAILORED PROMPTS (LOGGED DIFFERENCES)
    # ==========================================================================
    
    def _create_tailored_prompt_llama31(
        self, 
        vuln_id: str, 
        policy: Dict
    ) -> str:
        """
        Experiment 2: Llama 3.1 optimized.
        
        DIFFERENCES FROM BASELINE:
        - Added markdown headers (###) for better structure parsing
        - Explicit bullet point formatting
        - Emphasizes scannable sections
        - Request for specific citation format
        """
        vuln_data, nist, iso = self._create_base_prompt(vuln_id, policy)
        
        return f"""You are a security policy expert. Use NIST CSF 2.0 and ISO 27001:2022.

### Vulnerability Details
{vuln_data}

### NIST CSF 2.0 Guidance
{self._build_context_section('', nist)}

### ISO 27001:2022 Controls
{self._build_context_section('', iso)}

### Task
Generate a structured security policy following this exact format:

**Title:** [Severity] - [Vuln ID]

**Scope:**
- List all affected systems
- Include specific components

**Risk:**
- Describe potential security impact
- Note business consequences

**Controls:**
- Map each control to NIST/ISO guidance above
- Use format: [Framework Section] - [Control Description]

**Remediation:**
- Action 1: [Description] (Timeline: X days)
- Action 2: [Description] (Timeline: Y days)

**Verification:**
- Method 1: [How to confirm]
- Method 2: [Testing procedure]

Requirements:
- Use bullet points throughout
- Make each section scannable
- Cite specific framework sections (e.g., NIST PR.DS-2, ISO A.9.4.1)
- Keep under 250 words total
- Be concrete and actionable"""
    
    def _create_tailored_prompt_deepseek(
        self, 
        vuln_id: str, 
        policy: Dict
    ) -> str:
        """
        Experiment 2: DeepSeek R1 optimized.
        
        DIFFERENCES FROM BASELINE:
        - Simplified instructions to reduce reasoning overhead
        - Shorter word limit (200 vs 250)
        - Focus on "most critical controls only"
        - More direct, less verbose structure
        - Explicit request to explain relevance (leverages reasoning)
        """
        vuln_data, nist, iso = self._create_base_prompt(vuln_id, policy)
        
        return f"""Generate a security policy using NIST CSF 2.0 and ISO 27001:2022.

Vulnerability:
{vuln_data}

NIST Guidance:
{self._build_context_section('', nist)}

ISO Controls:
{self._build_context_section('', iso)}

Create a policy with these sections:

Title: [Severity] - [Vuln ID]

Scope: List affected systems

Risk: Describe impact in 1-2 sentences

Controls: 
- Map 2-3 controls from the guidance above
- Format: [Framework ID] - [Brief description]
- Explain why each control is relevant

Remediation:
- List 2-3 actions with timelines
- Prioritize by urgency

Verification:
- Describe how to confirm fixes

Requirements:
- Cite framework sections
- Be concise: under 200 words
- Focus on most critical controls only"""
    
    def _create_tailored_prompt_gptoss(
        self, 
        vuln_id: str, 
        policy: Dict
    ) -> str:
        """
        Experiment 2: GPT-family optimized.
        
        DIFFERENCES FROM BASELINE:
        - Enhanced business context framing
        - Longer word limit (300 vs 250) to leverage context handling
        - Additional sections (Contingency Planning)
        - Role-based framing (Senior Security Compliance Officer)
        - Emphasis on balancing technical + business clarity
        """
        vuln_data, nist, iso = self._create_base_prompt(vuln_id, policy)
        
        return f"""You are a Senior Security Compliance Officer preparing a policy for executive review.

=== VULNERABILITY ASSESSMENT ===
{vuln_data}

=== NIST CSF 2.0 GUIDANCE ===
{self._build_context_section('', nist)}

=== ISO 27001:2022 CONTROLS ===
{self._build_context_section('', iso)}

=== POLICY REQUIREMENTS ===

Create a security policy that balances technical precision with business clarity.

Structure:
Title: [Severity] - [Vuln ID]

Scope:
- Identify affected systems and stakeholders
- Note business units impacted

Risk:
- Technical impact (confidentiality, integrity, availability)
- Business impact (operational, financial, reputational)
- Regulatory implications if applicable

Controls:
- Map to NIST/ISO guidance above with citations
- Explain how each control mitigates risk
- Include compensating controls if needed

Remediation:
- Immediate actions (0-7 days)
- Short-term fixes (7-30 days)
- Long-term improvements (30-90 days)
- Include resource requirements

Verification:
- Technical testing procedures
- Audit checkpoints
- Success metrics

Contingency Planning:
- If remediation is delayed, what compensating controls apply?
- What monitoring should be enhanced?
- When should executives be notified?

Requirements:
- Balance technical detail with executive readability
- Include business context for each technical decision
- Provide clear accountability and timelines
- Cite specific framework sections
- Keep under 300 words while maintaining completeness"""
    
    # ==========================================================================
    # GENERATION LOGIC WITH MINIMAL LOGGING
    # ==========================================================================
    
    def _generate_policies(
        self, 
        model: str, 
        experiment: str, 
        prompt_method
    ) -> Dict[str, str]:
        """Core generation loop with metadata tracking."""
        output_dir = self._get_model_output_dir(model, experiment)
        generated_policies = {}
        total = len(self.reference_policies)
        timeout = self._get_timeout_for_experiment(model, experiment)
        
        # Initialize metadata
        metadata = {
            "model": model,
            "experiment": experiment,
            "start_time": datetime.now().isoformat(),
            "timeout_seconds": timeout,
            "rag_config": {
                "top_k": self.RAG_TOP_K,
                "chunk_size": self.MAX_CONTEXT_LENGTH,
                "embedder": "all-MiniLM-L6-v2",
                "vector_store": "pinecone/compliance-rag"
            },
            "total_vulnerabilities": total,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_duration_seconds": 0,
            "policy_ids_processed": []
        }
        
        print(f"\nUsing timeout: {timeout}s for model '{model}' (Experiment {experiment})")
        print(f"Output: {output_dir}")
        print("-" * 60)
        
        for i, (vuln_id, policy) in enumerate(
            self.reference_policies.items(), 1
        ):
            print(f"[{i}/{total}] {vuln_id}...", end=" ", flush=True)
            
            # Generate prompt
            prompt = prompt_method(vuln_id, policy)
            
            # Call model with timing
            response, duration, success = self.call_ollama(model, prompt, timeout)
            
            # Track statistics
            metadata["total_duration_seconds"] += duration
            metadata["policy_ids_processed"].append({
                "vuln_id": vuln_id,
                "duration_seconds": round(duration, 2),
                "success": success
            })
            
            if success and response:
                generated_policies[vuln_id] = response
                metadata["successful_generations"] += 1
                print("✓")
            else:
                metadata["failed_generations"] += 1
                print("✗")
            
            time.sleep(self.REQUEST_DELAY)
        
        # Finalize metadata
        metadata["end_time"] = datetime.now().isoformat()
        metadata["completion_rate_percent"] = round(
            metadata["successful_generations"] / total * 100, 2
        )
        metadata["avg_latency_seconds"] = round(
            metadata["total_duration_seconds"] / total, 2
        )
        
        # Save policies
        policies_file = os.path.join(output_dir, "policies.json")
        with open(policies_file, 'w', encoding='utf-8') as f:
            json.dump(generated_policies, f, indent=2, ensure_ascii=False)
        
        # Save metadata
        metadata_file = os.path.join(output_dir, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Store for fairness report
        stats_key = f"{model}_exp{experiment}"
        self.experiment_stats[stats_key] = metadata
        
        print(f"\n✓ Policies: {policies_file}")
        print(f"✓ Metadata: {metadata_file}")
        return generated_policies
    
    def generate_experiment_1(self, model: str) -> Dict[str, str]:
        """Experiment 1: Standardized prompt + RAG (fair baseline)."""
        print(f"\n{'='*60}")
        print(f"EXPERIMENT 1: {model} (Standardized + RAG)")
        print(f"{'='*60}")
        
        return self._generate_policies(
            model, 
            "1", 
            self._create_standardized_prompt
        )
    
    def generate_experiment_2(self, model: str) -> Dict[str, str]:
        """Experiment 2: Tailored prompt + RAG."""
        print(f"\n{'='*60}")
        print(f"EXPERIMENT 2: {model} (Tailored + RAG)")
        print(f"{'='*60}")
        
        # Map models to their optimized prompt methods
        tailored_methods = {
            "llama3.1": self._create_tailored_prompt_llama31,
            "deepseek-r1:8b": self._create_tailored_prompt_deepseek,
            "deepseek-r1:14b": self._create_tailored_prompt_deepseek,
            "gpt-oss:20b": self._create_tailored_prompt_gptoss
        }
        
        prompt_method = tailored_methods.get(
            model, 
            self._create_tailored_prompt_llama31
        )
        
        return self._generate_policies(model, "2", prompt_method)
    
    def generate_fairness_report(self):
        """Generate fairness report comparing all models/experiments."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "experiment_configuration": {
                "exp1_timeout_seconds": self.EXPERIMENT_1_TIMEOUT,
                "exp2_timeouts": self.MODEL_TIMEOUTS_EXP2,
                "rag_top_k": self.RAG_TOP_K,
                "chunk_size": self.MAX_CONTEXT_LENGTH,
                "random_seed": 42,
                "policies_sorted": True
            },
            "comparison": []
        }
        
        for key, stats in self.experiment_stats.items():
            report["comparison"].append({
                "model": stats["model"],
                "experiment": stats["experiment"],
                "completion_rate_percent": stats["completion_rate_percent"],
                "avg_latency_seconds": stats["avg_latency_seconds"],
                "timeout_seconds": stats["timeout_seconds"],
                "successful_generations": stats["successful_generations"],
                "failed_generations": stats["failed_generations"],
                "total_duration_seconds": round(stats["total_duration_seconds"], 2)
            })
        
        # Sort by experiment then model for readability
        report["comparison"].sort(key=lambda x: (x["experiment"], x["model"]))
        
        # Save report
        report_file = os.path.join(self.output_dir, "logs", "fairness_report.json")
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"✓ Fairness Report: {report_file}")
        print(f"{'='*60}")
        
        # Print summary table
        print("\nCOMPLETION SUMMARY:")
        print(f"{'Model':<20} {'Exp':<5} {'Complete %':<12} {'Avg Latency':<15} {'Timeout'}")
        print("-" * 70)
        for item in report["comparison"]:
            print(f"{item['model']:<20} {item['experiment']:<5} "
                  f"{item['completion_rate_percent']:<12.2f} "
                  f"{item['avg_latency_seconds']:<15.2f} "
                  f"{item['timeout_seconds']}s")
        
        return report
    
    def run(self, model: str, experiment: str):
        """Execute specified experiment(s)."""
        try:
            print(f"\n{'='*60}")
            print(f"Model: {model} | Experiment: {experiment}")
            print(f"Vulnerabilities: {len(self.reference_policies)}")
            print(f"{'='*60}")
            
            if experiment in ("1", "both"):
                self.generate_experiment_1(model)
            
            if experiment == "both":
                print(f"\nWaiting {self.EXPERIMENT_DELAY}s before Experiment 2...")
                time.sleep(self.EXPERIMENT_DELAY)
            
            if experiment in ("2", "both"):
                self.generate_experiment_2(model)
            
            print(f"\n✓ Completed: {model} - Experiment {experiment}")
            
        except KeyboardInterrupt:
            print("\n\n✗ Interrupted by user")
            raise  # Re-raise to allow cleanup in main
        except Exception as e:
            print(f"\n✗ Error: {e}")
            raise


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    """Main execution function with reproducibility setup."""
    # ==========================================================================
    # REPRODUCIBILITY: FIX RANDOM SEEDS
    # ==========================================================================
    import random
    import numpy as np
    import torch
    
    SEED = 42
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)
    
    print(f"✓ Random seed fixed: {SEED}")
    
    # ==========================================================================
    # CONFIGURATION
    # ==========================================================================

    MODELS = ["gpt-oss:20b"]
    EXPERIMENT = "both"              # "1", "2", or "both"
    LIMIT = 122                      # Number of policies per model
    
    # ==========================================================================
    # PATHS
    # ==========================================================================
    
    REFERENCE_POLICIES_PATH = os.path.join(
        os.path.dirname(__file__), 
        "policies", 
        "reference_policies.json"
    )
    OUTPUT_DIR = os.path.join(
        os.path.dirname(__file__), 
        "policies"
    )
    
    # ==========================================================================
    # API CONFIGURATION
    # ==========================================================================
    
    OLLAMA_ENDPOINT = "http://localhost:11434"
    load_dotenv()
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    
    if not PINECONE_API_KEY:
        print("✗ Error: PINECONE_API_KEY not found in environment")
        print("  Add it to your .env file: PINECONE_API_KEY=your_key_here")
        return
    
    # ==========================================================================
    # INITIALIZE AND RUN
    # ==========================================================================
    
    print("\n" + "="*60)
    print("RAG-Enhanced LLM Policy Generator")
    print("Fair & Reproducible Edition")
    print("="*60)
    print(f"Models: {', '.join(MODELS)}")
    print(f"Experiment: {EXPERIMENT}")
    print(f"Limit: {LIMIT} policies per model")
    print(f"Exp1 Timeout: 300s (SAME for all models)")
    print("="*60)
    
    generator = RAGLLMPolicyGenerator(
        ollama_endpoint=OLLAMA_ENDPOINT,
        reference_policies_file=REFERENCE_POLICIES_PATH,
        output_dir=OUTPUT_DIR,
        pinecone_api_key=PINECONE_API_KEY,
        limit_per_model=LIMIT
    )
    
    try:
        for model in MODELS:
            generator.run(model, EXPERIMENT)
    except KeyboardInterrupt:
        print("\n\n✗ Execution interrupted by user")
    finally:
        # Always generate fairness report even if interrupted
        if generator.experiment_stats:
            generator.generate_fairness_report()
    
    print("\n" + "="*60)
    print("✓ All experiments completed!")
    print("="*60)


if __name__ == "__main__":
    main()