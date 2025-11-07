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
EXPERIMENTS = ["1", "2"]

# Feature names
FEATURE_NAMES = ['Timeline', 'Responsibilities', 'Procedures', 'Monitoring', 'Compliance', 'Technical Details', 'Risk Assessment']
FEATURE_KEYS = ['has_timeline', 'has_responsibilities', 'has_procedures', 'has_monitoring', 'has_compliance', 'has_technical_details', 'has_risk_assessment']

# Experiment labels
EXP1_LABEL = "Experiment 1"
EXP2_LABEL = "Experiment 2"

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
    st.title("📊 Experiment Metadata Dashboard")
    
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
    st.subheader("📈 Overview Metrics")
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
    st.subheader("📋 Detailed Experiment Metrics")
    st.dataframe(df, use_container_width=True)
    
    # Performance comparison charts
    st.subheader("📊 Performance Comparison")
    
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
        st.subheader("� RAG Configuration")
        rag_cols = ["RAG Top-K", "RAG Chunk Size", "RAG Embedder", "RAG Vector Store"]
        existing_rag_cols = [col for col in rag_cols if col in df.columns]
        if existing_rag_cols:
            st.dataframe(df[["Model", "Experiment"] + existing_rag_cols], use_container_width=True)

def show_policy_comparison():
    """Display policy comparison dashboard"""
    st.title("�🔒 RAG Policy Comparison Dashboard")
    
    # Sidebar
    st.sidebar.header("Filters")
    
    selected_model = st.sidebar.selectbox("Model", MODELS)
    
    # Load both experiments
    exp1 = load_policies(selected_model, "1")
    exp2 = load_policies(selected_model, "2")
    
    if not exp1 and not exp2:
        st.error("No policies found. Run generator first.")
        return
    
    # Get CVE list
    cves = sorted(set(exp1.keys()) | set(exp2.keys()))
    selected_cve = st.sidebar.selectbox("Vulnerability", sorted(cves))
    
    # Display
    st.subheader(f"{selected_model} - {selected_cve}")
    
    # Analyze policies
    analysis1 = analyze_policy_content(exp1.get(selected_cve, "")) if selected_cve in exp1 else {}
    analysis2 = analyze_policy_content(exp2.get(selected_cve, "")) if selected_cve in exp2 else {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Experiment 1: Standardized + RAG")
        if selected_cve in exp1:
            policy1 = exp1[selected_cve]
            
            # Metrics
            with st.expander("📊 Policy Metrics", expanded=False):
                mcol1, mcol2 = st.columns(2)
                with mcol1:
                    st.metric("Word Count", analysis1.get('word_count', 0))
                    st.metric("Sections", analysis1.get('section_count', 0))
                    st.metric("Total Citations", analysis1.get('total_citations', 0))
                with mcol2:
                    st.metric("Paragraphs", analysis1.get('paragraph_count', 0))
                    st.metric("Completeness Score", f"{analysis1.get('completeness_score', 0)}/7")
                    
                # Citation breakdown
                st.markdown("**Citations by Framework:**")
                citations1 = analysis1.get('citations', {})
                for framework, count in citations1.items():
                    if count > 0:
                        st.write(f"• {framework}: {count}")
                
                # Content features
                st.markdown("**Content Features:**")
                for feature, name in zip(FEATURE_KEYS, FEATURE_NAMES):
                    icon = "✅" if analysis1.get(feature, False) else "❌"
                    st.write(f"{icon} {name}")
            
            # Policy content
            with st.expander("📄 Policy Content", expanded=True):
                st.markdown(policy1)
        else:
            st.warning("No policy generated")
    
    with col2:
        st.markdown("### Experiment 2: Tailored + RAG")
        if selected_cve in exp2:
            policy2 = exp2[selected_cve]
            
            # Metrics
            with st.expander("📊 Policy Metrics", expanded=False):
                mcol1, mcol2 = st.columns(2)
                with mcol1:
                    st.metric("Word Count", analysis2.get('word_count', 0))
                    st.metric("Sections", analysis2.get('section_count', 0))
                    st.metric("Total Citations", analysis2.get('total_citations', 0))
                with mcol2:
                    st.metric("Paragraphs", analysis2.get('paragraph_count', 0))
                    st.metric("Completeness Score", f"{analysis2.get('completeness_score', 0)}/7")
                    
                # Citation breakdown
                st.markdown("**Citations by Framework:**")
                citations2 = analysis2.get('citations', {})
                for framework, count in citations2.items():
                    if count > 0:
                        st.write(f"• {framework}: {count}")
                
                # Content features
                st.markdown("**Content Features:**")
                features = ['has_timeline', 'has_responsibilities', 'has_procedures', 'has_monitoring', 'has_compliance', 'has_technical_details', 'has_risk_assessment']
                feature_names = ['Timeline', 'Responsibilities', 'Procedures', 'Monitoring', 'Compliance', 'Technical Details', 'Risk Assessment']
                for feature, name in zip(features, feature_names):
                    icon = "✅" if analysis2.get(feature, False) else "❌"
                    st.write(f"{icon} {name}")
            
            # Policy content
            with st.expander("📄 Policy Content", expanded=True):
                st.markdown(policy2)
        else:
            st.warning("No policy generated")
    
    # Detailed Comparison
    if selected_cve in exp1 and selected_cve in exp2:
        st.markdown("---")
        st.subheader("📊 Detailed Comparison Analysis")
        
        # Metrics comparison
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            word_diff = analysis2.get('word_count', 0) - analysis1.get('word_count', 0)
            st.metric("Word Count Difference", word_diff, delta=word_diff)
            
        with col2:
            citation_diff = analysis2.get('total_citations', 0) - analysis1.get('total_citations', 0)
            st.metric("Citations Difference", citation_diff, delta=citation_diff)
            
        with col3:
            completeness_diff = analysis2.get('completeness_score', 0) - analysis1.get('completeness_score', 0)
            st.metric("Completeness Difference", completeness_diff, delta=completeness_diff)
            
        with col4:
            section_diff = analysis2.get('section_count', 0) - analysis1.get('section_count', 0)
            st.metric("Sections Difference", section_diff, delta=section_diff)
        
        # Citation comparison chart
        if analysis1.get('citations') and analysis2.get('citations'):
            st.markdown("### 📚 Citation Framework Comparison")
            
            # Prepare data for comparison chart
            frameworks = list(CITATION_PATTERNS.keys())
            exp1_counts = [analysis1.get('citations', {}).get(fw, 0) for fw in frameworks]
            exp2_counts = [analysis2.get('citations', {}).get(fw, 0) for fw in frameworks]
            
            citation_df = pd.DataFrame({
                'Framework': frameworks,
                'Experiment 1': exp1_counts,
                'Experiment 2': exp2_counts
            })
            
            # Only show frameworks with citations
            citation_df = citation_df[(citation_df['Experiment 1'] > 0) | (citation_df['Experiment 2'] > 0)]
            
            if not citation_df.empty:
                fig_citations = px.bar(
                    citation_df.melt(id_vars=['Framework'], var_name='Experiment', value_name='Citations'),
                    x='Framework',
                    y='Citations',
                    color='Experiment',
                    title="Citation Count by Framework",
                    barmode='group'
                )
                st.plotly_chart(fig_citations, use_container_width=True)
        
        # Content feature comparison
        st.markdown("### 🎯 Content Features Comparison")
        
        features = ['has_timeline', 'has_responsibilities', 'has_procedures', 'has_monitoring', 'has_compliance', 'has_technical_details', 'has_risk_assessment']
        feature_names = ['Timeline', 'Responsibilities', 'Procedures', 'Monitoring', 'Compliance', 'Technical Details', 'Risk Assessment']
        
        feature_comparison = []
        for feature, name in zip(features, feature_names):
            exp1_has = analysis1.get(feature, False)
            exp2_has = analysis2.get(feature, False)
            feature_comparison.append({
                'Feature': name,
                'Experiment 1': '✅' if exp1_has else '❌',
                'Experiment 2': '✅' if exp2_has else '❌',
                'Both Have': '✅' if exp1_has and exp2_has else '❌',
                'Neither Have': '✅' if not exp1_has and not exp2_has else '❌'
            })
        
        feature_df = pd.DataFrame(feature_comparison)
        st.dataframe(feature_df, use_container_width=True)
        
        # Quality assessment
        st.markdown("### 🏆 Quality Assessment")
        
        qcol1, qcol2 = st.columns(2)
        
        with qcol1:
            st.markdown("**Experiment 1 Strengths:**")
            if analysis1.get('completeness_score', 0) > analysis2.get('completeness_score', 0):
                st.write("• Higher completeness score")
            if analysis1.get('total_citations', 0) > analysis2.get('total_citations', 0):
                st.write("• More framework citations")
            if analysis1.get('word_count', 0) > analysis2.get('word_count', 0):
                st.write("• More detailed content")
            if analysis1.get('section_count', 0) > analysis2.get('section_count', 0):
                st.write("• Better structured")
                
        with qcol2:
            st.markdown("**Experiment 2 Strengths:**")
            if analysis2.get('completeness_score', 0) > analysis1.get('completeness_score', 0):
                st.write("• Higher completeness score")
            if analysis2.get('total_citations', 0) > analysis1.get('total_citations', 0):
                st.write("• More framework citations")
            if analysis2.get('word_count', 0) > analysis1.get('word_count', 0):
                st.write("• More detailed content")
            if analysis2.get('section_count', 0) > analysis1.get('section_count', 0):
                st.write("• Better structured")

def show_individual_metadata():
    """Display individual experiment metadata"""
    st.title("🔍 Individual Experiment Analysis")
    
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
        st.subheader("🔧 RAG Configuration")
        rag_config = data["rag_config"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Top-K:** {rag_config.get('top_k', 'N/A')}")
            st.write(f"**Chunk Size:** {rag_config.get('chunk_size', 'N/A')}")
        with col2:
            st.write(f"**Embedder:** {rag_config.get('embedder', 'N/A')}")
            st.write(f"**Vector Store:** {rag_config.get('vector_store', 'N/A')}")
    
    # Processing details
    if "policy_ids_processed" in data:
        st.subheader("📋 Processing Details")
        
        # Convert to DataFrame for better display
        process_data = []
        for item in data["policy_ids_processed"]:
            process_data.append({
                "Vulnerability ID": item["vuln_id"],
                "Duration (s)": round(item["duration_seconds"], 2),
                "Status": "✓ Success" if item["success"] else "✗ Failed"
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
    st.title("📈 Aggregate Policy Analysis")
    
    selected_model = st.sidebar.selectbox("Model", MODELS, key="aggregate")
    
    # Load all policies for both experiments
    exp1_policies = load_policies(selected_model, "1")
    exp2_policies = load_policies(selected_model, "2")
    
    if not exp1_policies and not exp2_policies:
        st.error("No policies found for analysis")
        return
    
    # Analyze all policies
    exp1_analyses = []
    exp2_analyses = []
    
    all_cves = set(exp1_policies.keys()) | set(exp2_policies.keys())
    
    for cve in all_cves:
        if cve in exp1_policies:
            analysis = analyze_policy_content(exp1_policies[cve])
            analysis['cve'] = cve
            exp1_analyses.append(analysis)
            
        if cve in exp2_policies:
            analysis = analyze_policy_content(exp2_policies[cve])
            analysis['cve'] = cve
            exp2_analyses.append(analysis)
    
    # Convert to DataFrames
    df1 = pd.DataFrame(exp1_analyses) if exp1_analyses else pd.DataFrame()
    df2 = pd.DataFrame(exp2_analyses) if exp2_analyses else pd.DataFrame()
    
    # Summary statistics
    st.subheader("📊 Summary Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Experiment 1: Standardized + RAG")
        if not df1.empty:
            st.metric("Total Policies", len(df1))
            st.metric("Avg Word Count", f"{df1['word_count'].mean():.0f}")
            st.metric("Avg Citations", f"{df1['total_citations'].mean():.1f}")
            st.metric("Avg Completeness", f"{df1['completeness_score'].mean():.1f}/7")
            
    with col2:
        st.markdown("### Experiment 2: Tailored + RAG")
        if not df2.empty:
            st.metric("Total Policies", len(df2))
            st.metric("Avg Word Count", f"{df2['word_count'].mean():.0f}")
            st.metric("Avg Citations", f"{df2['total_citations'].mean():.1f}")
            st.metric("Avg Completeness", f"{df2['completeness_score'].mean():.1f}/7")
    
    # Distribution comparisons
    if not df1.empty and not df2.empty:
        st.subheader("📊 Distribution Comparisons")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Word count distribution
            fig_words = go.Figure()
            fig_words.add_trace(go.Histogram(x=df1['word_count'], name='Experiment 1', opacity=0.7))
            fig_words.add_trace(go.Histogram(x=df2['word_count'], name='Experiment 2', opacity=0.7))
            fig_words.update_layout(title='Word Count Distribution', barmode='overlay')
            st.plotly_chart(fig_words, use_container_width=True)
            
        with col2:
            # Citation distribution
            fig_citations = go.Figure()
            fig_citations.add_trace(go.Histogram(x=df1['total_citations'], name='Experiment 1', opacity=0.7))
            fig_citations.add_trace(go.Histogram(x=df2['total_citations'], name='Experiment 2', opacity=0.7))
            fig_citations.update_layout(title='Total Citations Distribution', barmode='overlay')
            st.plotly_chart(fig_citations, use_container_width=True)
        
        # Feature adoption rates
        st.subheader("🎯 Feature Adoption Rates")
        
        features = ['has_timeline', 'has_responsibilities', 'has_procedures', 'has_monitoring', 'has_compliance', 'has_technical_details', 'has_risk_assessment']
        feature_names = ['Timeline', 'Responsibilities', 'Procedures', 'Monitoring', 'Compliance', 'Technical Details', 'Risk Assessment']
        
        adoption_data = []
        for feature, name in zip(features, feature_names):
            exp1_rate = (df1[feature].sum() / len(df1)) * 100 if len(df1) > 0 else 0
            exp2_rate = (df2[feature].sum() / len(df2)) * 100 if len(df2) > 0 else 0
            adoption_data.append({
                'Feature': name,
                'Experiment 1 (%)': exp1_rate,
                'Experiment 2 (%)': exp2_rate,
                'Difference': exp2_rate - exp1_rate
            })
        
        adoption_df = pd.DataFrame(adoption_data)
        
        fig_adoption = px.bar(
            adoption_df.melt(id_vars=['Feature', 'Difference'], 
                           value_vars=['Experiment 1 (%)', 'Experiment 2 (%)'],
                           var_name='Experiment', value_name='Adoption Rate (%)'),
            x='Feature',
            y='Adoption Rate (%)',
            color='Experiment',
            title='Feature Adoption Rates by Experiment',
            barmode='group'
        )
        fig_adoption.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_adoption, use_container_width=True)
        
        # Statistical comparison table
        st.subheader("📋 Statistical Comparison")
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