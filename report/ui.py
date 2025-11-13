import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="RAG Policy Analysis Dashboard", layout="wide")

# Config
POLICY_DIR = os.path.join(os.path.dirname(__file__), "policies")

# Constants
MODELS = ["llama3.1", "deepseek-r1:8b", "gpt-oss:20b"]
EXPERIMENTS = ["1", "2", "3"]

# Feature names
FEATURE_NAMES = ['Timeline', 'Responsibilities', 'Procedures', 'Monitoring', 'Compliance', 'Technical Details', 'Risk Assessment']
FEATURE_KEYS = ['has_timeline', 'has_responsibilities', 'has_procedures', 'has_monitoring', 'has_compliance', 'has_technical_details', 'has_risk_assessment']

# Experiment labels
EXP1_LABEL = "Experiment 1: Standardized + RAG"
EXP2_LABEL = "Experiment 2: Tailored + RAG"
EXP3_LABEL = "Experiment 3: Standard + RAG (Morocco AI)"

# Metrics for analysis
CITATION_PATTERNS = {
    "NIST": ["NIST", "National Institute of Standards"],
    "ISO": ["ISO 27001", "ISO 27002", "ISO/IEC"],
    "CIS": ["CIS Controls", "CIS Benchmarks"],
    "OWASP": ["OWASP", "Open Web Application Security"],
    "SANS": ["SANS", "SysAdmin"],
    "MITRE": ["MITRE ATT&CK", "MITRE"],
    "GDPR": ["GDPR", "General Data Protection"],
    "SOX": ["Sarbanes-Oxley", "SOX"],
    "HIPAA": ["HIPAA", "Health Insurance Portability"]
}

def load_policies(model, experiment):
    """Load policies for model and experiment"""
    path = os.path.join(POLICY_DIR, "logs", model.replace(":", "_"), f"experiment_{experiment}", "policies.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_metadata(model, experiment):
    """Load metadata for model and experiment"""
    path = os.path.join(POLICY_DIR, "logs", model.replace(":", "_"), f"experiment_{experiment}", "metadata.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_experiment_metadata(model, experiment):
    """Load experiment metadata for model and experiment"""
    path = os.path.join(POLICY_DIR, "logs", model.replace(":", "_"), f"experiment_{experiment}", "experiment_metadata.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def analyze_policy_content(policy_text):
    """Analyze policy content for various metrics"""
    if not policy_text:
        return {}
    
    text_lower = policy_text.lower()
    
    # Basic metrics
    word_count = len(policy_text.split())
    char_count = len(policy_text)
    paragraph_count = policy_text.count('\n\n') + 1
    section_count = policy_text.count('**')
    
    # Citation analysis
    citations = {}
    for framework, patterns in CITATION_PATTERNS.items():
        count = sum(policy_text.upper().count(pattern.upper()) for pattern in patterns)
        citations[framework] = count
    
    # Content analysis
    has_timeline = any(keyword in text_lower for keyword in ['days', 'weeks', 'months', 'timeline', 'schedule', 'deadline'])
    has_responsibilities = any(keyword in text_lower for keyword in ['responsible', 'accountability', 'owner', 'assigned'])
    has_procedures = any(keyword in text_lower for keyword in ['procedure', 'steps', 'process', 'workflow'])
    has_monitoring = any(keyword in text_lower for keyword in ['monitor', 'audit', 'review', 'assess', 'evaluate'])
    has_compliance = any(keyword in text_lower for keyword in ['comply', 'compliance', 'regulation', 'requirement'])
    
    # Technical depth indicators
    has_technical_details = any(keyword in text_lower for keyword in ['configure', 'implement', 'deploy', 'install', 'patch'])
    has_risk_assessment = any(keyword in text_lower for keyword in ['risk', 'threat', 'vulnerability', 'impact', 'likelihood'])
    
    return {
        'word_count': word_count,
        'char_count': char_count,
        'paragraph_count': paragraph_count,
        'section_count': section_count,
        'citations': citations,
        'total_citations': sum(citations.values()),
        'has_timeline': has_timeline,
        'has_responsibilities': has_responsibilities,
        'has_procedures': has_procedures,
        'has_monitoring': has_monitoring,
        'has_compliance': has_compliance,
        'has_technical_details': has_technical_details,
        'has_risk_assessment': has_risk_assessment,
        'completeness_score': sum([has_timeline, has_responsibilities, has_procedures, has_monitoring, has_compliance, has_technical_details, has_risk_assessment])
    }

def show_metadata_dashboard():
    """Display metadata dashboard"""
    st.title("Chart Experiment Metadata Dashboard")
    
    # Load metadata for all models and experiments
    metadata_summary = []
    
    for model in MODELS:
        for exp in EXPERIMENTS:
            meta = load_metadata(model, exp)
            exp_meta = load_experiment_metadata(model, exp)
            
            if meta or exp_meta:
                # Use the more comprehensive metadata if available
                data = meta if meta else exp_meta
                
                summary = {
                    "Model": model,
                    "Experiment": f"Experiment {exp}",
                    "Total Vulnerabilities": data.get("total_vulnerabilities", data.get("total_requests", 0)),
                    "Successful Generations": data.get("successful_generations", data.get("successful_requests", 0)),
                    "Failed Generations": data.get("failed_generations", data.get("failed_requests", 0)),
                    "Completion Rate (%)": data.get("completion_rate_percent", data.get("completion_rate", 0)),
                    "Total Duration (min)": round(data.get("total_duration_seconds", 0) / 60, 2),
                    "Avg Latency (s)": round(data.get("avg_latency_seconds", 0), 2),
                    "Timeout (s)": data.get("timeout_seconds", 0),
                    "Start Time": data.get("start_time", "N/A"),
                    "End Time": data.get("end_time", "N/A")
                }
                
                if "rag_config" in data:
                    summary.update({
                        "RAG Top-K": data["rag_config"].get("top_k", "N/A"),
                        "RAG Chunk Size": data["rag_config"].get("chunk_size", "N/A"),
                        "RAG Embedder": data["rag_config"].get("embedder", "N/A"),
                        "RAG Vector Store": data["rag_config"].get("vector_store", "N/A")
                    })
                
                metadata_summary.append(summary)
    
    if not metadata_summary:
        st.error("No metadata found")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(metadata_summary)
    
    # Overview metrics
    st.subheader("Overview Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_vulns = df["Total Vulnerabilities"].sum()
        st.metric("Total Vulnerabilities Processed", total_vulns)
    
    with col2:
        avg_completion = df["Completion Rate (%)"].mean()
        st.metric("Average Completion Rate", f"{avg_completion:.1f}%")
    
    with col3:
        total_duration = df["Total Duration (min)"].sum()
        st.metric("Total Processing Time", f"{total_duration:.1f} min")
    
    with col4:
        avg_latency = df["Avg Latency (s)"].mean()
        st.metric("Average Latency", f"{avg_latency:.2f}s")
    
    # Detailed table
    st.subheader("Detailed Experiment Metrics")
    st.dataframe(df, use_container_width=True)
    
    # Performance comparison charts
    st.subheader("Performance Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Completion rate comparison
        fig_completion = px.bar(
            df, 
            x="Model", 
            y="Completion Rate (%)", 
            color="Experiment",
            title="Completion Rate by Model and Experiment",
            barmode="group"
        )
        st.plotly_chart(fig_completion, use_container_width=True)
    
    with col2:
        # Latency comparison
        fig_latency = px.bar(
            df, 
            x="Model", 
            y="Avg Latency (s)", 
            color="Experiment",
            title="Average Latency by Model and Experiment",
            barmode="group"
        )
        st.plotly_chart(fig_latency, use_container_width=True)
    
    # RAG Configuration comparison
    if "RAG Top-K" in df.columns:
        st.subheader("RAG Configuration")
        rag_cols = ["RAG Top-K", "RAG Chunk Size", "RAG Embedder", "RAG Vector Store"]
        existing_rag_cols = [col for col in rag_cols if col in df.columns]
        if existing_rag_cols:
            st.dataframe(df[["Model", "Experiment"] + existing_rag_cols], use_container_width=True)

def show_policy_comparison():
    """Display policy comparison dashboard"""
    st.title("RAG Policy Comparison Dashboard")
    
    # Sidebar
    st.sidebar.header("Filters")
    
    selected_model = st.sidebar.selectbox("Model", MODELS)
    selected_experiments = st.sidebar.multiselect(
        "Experiments", 
        EXPERIMENTS,
        default=["1", "2", "3"]
    )
    
    if not selected_experiments:
        st.warning("Please select at least one experiment")
        return
    
    # Load experiments
    policies = {}
    for exp in selected_experiments:
        policies[exp] = load_policies(selected_model, exp)
    
    # Check if any policies exist
    if not any(policies.values()):
        st.error("No policies found. Run generator first.")
        return
    
    # Get CVE list from all selected experiments
    all_cves = set()
    for exp_policies in policies.values():
        all_cves.update(exp_policies.keys())
    
    cves = sorted(all_cves)
    selected_cve = st.sidebar.selectbox("Vulnerability", cves)
    
    # Display
    st.subheader(f"{selected_model} - {selected_cve}")
    
    # Get experiment labels
    exp_labels = {
        "1": EXP1_LABEL,
        "2": EXP2_LABEL,
        "3": EXP3_LABEL
    }
    
    # Create columns based on selected experiments
    columns = st.columns(len(selected_experiments))
    
    analyses = {}
    
    for idx, (exp, col) in enumerate(zip(selected_experiments, columns)):
        with col:
            st.markdown(f"### {exp_labels[exp]}")
            
            if selected_cve in policies[exp]:
                policy = policies[exp][selected_cve]
                analysis = analyze_policy_content(policy)
                analyses[exp] = analysis
                
                # Metrics
                with st.expander("Policy Metrics", expanded=False):
                    mcol1, mcol2 = st.columns(2)
                    with mcol1:
                        st.metric("Word Count", analysis.get('word_count', 0))
                        st.metric("Sections", analysis.get('section_count', 0))
                        st.metric("Total Citations", analysis.get('total_citations', 0))
                    with mcol2:
                        st.metric("Paragraphs", analysis.get('paragraph_count', 0))
                        st.metric("Completeness Score", f"{analysis.get('completeness_score', 0)}/7")
                        
                    # Citation breakdown
                    st.markdown("**Citations by Framework:**")
                    citations = analysis.get('citations', {})
                    for framework, count in citations.items():
                        if count > 0:
                            st.write(f"• {framework}: {count}")
                    
                    # Content features
                    st.markdown("**Content Features:**")
                    for feature, name in zip(FEATURE_KEYS, FEATURE_NAMES):
                        icon = "OK" if analysis.get(feature, False) else "X"
                        st.write(f"[{icon}] {name}")
                
                # Policy content
                with st.expander("Policy Content", expanded=True):
                    st.markdown(policy)
            else:
                st.warning("No policy generated")
    
    # Detailed Comparison (only if 2+ experiments selected)
    if len(selected_experiments) >= 2:
        st.markdown("---")
        st.subheader("Detailed Comparison Analysis")
        
        # Build comparison data
        comparison_data = []
        for exp in selected_experiments:
            if selected_cve in policies[exp]:
                analysis = analyses.get(exp, analyze_policy_content(policies[exp][selected_cve]))
                comparison_data.append({
                    "Experiment": exp_labels[exp],
                    "Word Count": analysis.get('word_count', 0),
                    "Citations": analysis.get('total_citations', 0),
                    "Completeness": analysis.get('completeness_score', 0),
                    "Sections": analysis.get('section_count', 0),
                    "Paragraphs": analysis.get('paragraph_count', 0)
                })
        
        if comparison_data:
            comp_df = pd.DataFrame(comparison_data)
            st.dataframe(comp_df, use_container_width=True)
            
            # Comparison charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Word count comparison
                fig_words = px.bar(
                    comp_df,
                    x="Experiment",
                    y="Word Count",
                    title="Word Count Comparison",
                    color="Experiment"
                )
                st.plotly_chart(fig_words, use_container_width=True)
            
            with col2:
                # Citations comparison
                fig_cit = px.bar(
                    comp_df,
                    x="Experiment",
                    y="Citations",
                    title="Total Citations Comparison",
                    color="Experiment"
                )
                st.plotly_chart(fig_cit, use_container_width=True)
        
        # Citation framework comparison
        if len(selected_experiments) >= 2:
            st.markdown("### Citation Framework Comparison")
            
            frameworks = list(CITATION_PATTERNS.keys())
            citation_comparison = []
            
            for exp in selected_experiments:
                if selected_cve in policies[exp]:
                    analysis = analyses.get(exp, analyze_policy_content(policies[exp][selected_cve]))
                    for framework in frameworks:
                        count = analysis.get('citations', {}).get(framework, 0)
                        if count > 0:
                            citation_comparison.append({
                                'Framework': framework,
                                'Experiment': exp_labels[exp],
                                'Count': count
                            })
            
            if citation_comparison:
                cit_df = pd.DataFrame(citation_comparison)
                fig_citations = px.bar(
                    cit_df,
                    x='Framework',
                    y='Count',
                    color='Experiment',
                    title="Citation Count by Framework",
                    barmode='group'
                )
                st.plotly_chart(fig_citations, use_container_width=True)
        
        # Content feature comparison
        st.markdown("### Content Features Comparison")
        
        feature_comparison = []
        for feature, name in zip(FEATURE_KEYS, FEATURE_NAMES):
            row = {'Feature': name}
            for exp in selected_experiments:
                if selected_cve in policies[exp]:
                    analysis = analyses.get(exp, analyze_policy_content(policies[exp][selected_cve]))
                    row[exp_labels[exp]] = 'YES' if analysis.get(feature, False) else 'NO'
            feature_comparison.append(row)
        
        feature_df = pd.DataFrame(feature_comparison)
        st.dataframe(feature_df, use_container_width=True)

def show_individual_metadata():
    """Display individual experiment metadata"""
    st.title("Individual Experiment Analysis")
    
    # Sidebar for selection
    st.sidebar.header("Select Experiment")
    selected_model = st.sidebar.selectbox("Model", MODELS, key="individual")
    selected_experiment = st.sidebar.selectbox("Experiment", EXPERIMENTS, key="individual_exp")
    
    # Load metadata
    metadata = load_metadata(selected_model, selected_experiment)
    exp_metadata = load_experiment_metadata(selected_model, selected_experiment)
    
    if not metadata and not exp_metadata:
        st.error(f"No metadata found for {selected_model} - Experiment {selected_experiment}")
        return
    
    # Use the more comprehensive metadata
    data = metadata if metadata else exp_metadata
    
    st.subheader(f"{selected_model} - Experiment {selected_experiment}")
    
    # Basic info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Vulnerabilities", data.get("total_vulnerabilities", data.get("total_requests", 0)))
        st.metric("Success Rate", f"{data.get('completion_rate_percent', data.get('completion_rate', 0)):.1f}%")
    
    with col2:
        st.metric("Processing Time", f"{data.get('total_duration_seconds', 0)/60:.1f} min")
        st.metric("Average Latency", f"{data.get('avg_latency_seconds', 0):.2f}s")
    
    with col3:
        st.metric("Successful", data.get("successful_generations", data.get("successful_requests", 0)))
        st.metric("Failed", data.get("failed_generations", data.get("failed_requests", 0)))
    
    # RAG Configuration (if available)
    if "rag_config" in data:
        st.subheader("RAG Configuration")
        rag_config = data["rag_config"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Top-K:** {rag_config.get('top_k', 'N/A')}")
            st.write(f"**Chunk Size:** {rag_config.get('chunk_size', 'N/A')}")
            st.write(f"**Namespace:** {rag_config.get('namespace', 'N/A')}")
        with col2:
            st.write(f"**Embedder:** {rag_config.get('embedder', 'N/A')}")
            st.write(f"**Vector Store:** {rag_config.get('vector_store', 'N/A')}")
            st.write(f"**Source:** {rag_config.get('source', 'N/A')}")
        
        # Author and vector details
        if rag_config.get('author_attribution'):
            st.write(f"**Author:** {rag_config.get('author_attribution', 'N/A')}")
        if rag_config.get('total_vectors'):
            st.write(f"**Total Vectors:** {rag_config.get('total_vectors', 'N/A')}")
        
        # Source documents section (Experiment 3 specific)
        if "source_documents" in rag_config:
            st.write("---")
            st.write("**Source Documents:**")
            source_docs = rag_config.get('source_documents', {})
            for doc_key, doc_info in source_docs.items():
                with st.expander(f"{doc_info.get('title', 'Unknown')} by {doc_info.get('author', 'Unknown')}"):
                    st.write(f"**ID:** {doc_info.get('id', 'N/A')}")
                    st.write(f"**Author:** {doc_info.get('author', 'N/A')}")
                    st.write(f"**Chunks:** {doc_info.get('chunks', 'N/A')}")
                    st.write(f"**Focus:** {doc_info.get('focus', 'N/A')}")
                    if doc_info.get('purpose'):
                        st.write(f"**Purpose:** {doc_info.get('purpose', 'N/A')}")
    
    # Processing details
    if "policy_ids_processed" in data:
        st.subheader("Processing Details")
        
        # Convert to DataFrame for better display
        process_data = []
        for item in data["policy_ids_processed"]:
            process_data.append({
                "Vulnerability ID": item["vuln_id"],
                "Duration (s)": round(item["duration_seconds"], 2),
                "Status": "Success" if item["success"] else "Failed"
            })
        
        df_process = pd.DataFrame(process_data)
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Min Duration", f"{df_process['Duration (s)'].min():.2f}s")
        with col2:
            st.metric("Max Duration", f"{df_process['Duration (s)'].max():.2f}s")
        with col3:
            st.metric("Std Duration", f"{df_process['Duration (s)'].std():.2f}s")
        
        # Duration distribution
        fig_hist = px.histogram(
            df_process, 
            x="Duration (s)", 
            title="Processing Duration Distribution",
            nbins=20
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Detailed table
        st.dataframe(df_process, use_container_width=True)

def show_aggregate_analysis():
    """Show aggregate analysis across all policies"""
    st.title("Aggregate Policy Analysis")
    
    selected_model = st.sidebar.selectbox("Model", MODELS, key="aggregate")
    selected_experiments = st.sidebar.multiselect(
        "Experiments for Analysis",
        EXPERIMENTS,
        default=["1", "2", "3"],
        key="agg_exp"
    )
    
    if not selected_experiments:
        st.warning("Please select at least one experiment")
        return
    
    # Load all policies for selected experiments
    all_analyses = {}
    
    for exp in selected_experiments:
        policies = load_policies(selected_model, exp)
        
        if policies:
            exp_analyses = []
            for cve, policy in policies.items():
                analysis = analyze_policy_content(policy)
                analysis['cve'] = cve
                exp_analyses.append(analysis)
            
            all_analyses[exp] = pd.DataFrame(exp_analyses) if exp_analyses else pd.DataFrame()
    
    if not all_analyses or all(df.empty for df in all_analyses.values()):
        st.error("No policies found for selected experiments")
        return
    
    # Summary statistics
    st.subheader("Summary Statistics")
    
    exp_labels = {
        "1": EXP1_LABEL,
        "2": EXP2_LABEL,
        "3": EXP3_LABEL
    }
    
    cols = st.columns(len(selected_experiments))
    
    for col_idx, (exp, col) in enumerate(zip(selected_experiments, cols)):
        with col:
            st.markdown(f"### {exp_labels[exp]}")
            if exp in all_analyses and not all_analyses[exp].empty:
                df = all_analyses[exp]
                st.metric("Total Policies", len(df))
                st.metric("Avg Word Count", f"{df['word_count'].mean():.0f}")
                st.metric("Avg Citations", f"{df['total_citations'].mean():.1f}")
                st.metric("Avg Completeness", f"{df['completeness_score'].mean():.1f}/7")
    
    # Distribution comparisons
    if len(selected_experiments) >= 2 and any(not df.empty for df in all_analyses.values()):
        st.subheader("Distribution Comparisons")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Word count distribution
            fig_words = go.Figure()
            for exp in selected_experiments:
                if exp in all_analyses and not all_analyses[exp].empty:
                    fig_words.add_trace(go.Histogram(
                        x=all_analyses[exp]['word_count'],
                        name=exp_labels[exp],
                        opacity=0.7
                    ))
            fig_words.update_layout(title='Word Count Distribution', barmode='overlay')
            st.plotly_chart(fig_words, use_container_width=True)
            
        with col2:
            # Citation distribution
            fig_citations = go.Figure()
            for exp in selected_experiments:
                if exp in all_analyses and not all_analyses[exp].empty:
                    fig_citations.add_trace(go.Histogram(
                        x=all_analyses[exp]['total_citations'],
                        name=exp_labels[exp],
                        opacity=0.7
                    ))
            fig_citations.update_layout(title='Total Citations Distribution', barmode='overlay')
            st.plotly_chart(fig_citations, use_container_width=True)
        
        # Feature adoption rates
        st.subheader("Feature Adoption Rates")
        
        adoption_data = []
        for feature, name in zip(FEATURE_KEYS, FEATURE_NAMES):
            row = {'Feature': name}
            for exp in selected_experiments:
                if exp in all_analyses and not all_analyses[exp].empty:
                    df = all_analyses[exp]
                    adoption_rate = (df[feature].sum() / len(df)) * 100 if len(df) > 0 else 0
                    row[exp_labels[exp]] = f"{adoption_rate:.1f}%"
            adoption_data.append(row)
        
        adoption_df = pd.DataFrame(adoption_data)
        st.dataframe(adoption_df, use_container_width=True)

def main():
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Dashboard",
        ["Metadata Overview", "Policy Comparison", "Individual Analysis", "Aggregate Analysis"]
    )
    
    if page == "Metadata Overview":
        show_metadata_dashboard()
    elif page == "Policy Comparison":
        show_policy_comparison()
    elif page == "Individual Analysis":
        show_individual_metadata()
    elif page == "Aggregate Analysis":
        show_aggregate_analysis()

if __name__ == "__main__":
    main()
