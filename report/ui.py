import streamlit as st
import json
import os

st.set_page_config(page_title="Policy Comparison", layout="wide")

# Config
POLICY_DIR = r"C:\Users\achra\Desktop\report\policies"

def load_policies(model, experiment):
    """Load policies for model and experiment"""
    path = os.path.join(POLICY_DIR, model.replace(":", "_"), f"experiment_{experiment}", "policies.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def main():
    st.title("🔒 RAG Policy Comparison Dashboard")
    
    # Sidebar
    st.sidebar.header("Filters")
    
    models = ["llama3.1", "deepseek-r1:8b", "gpt-oss:20b"]
    selected_model = st.sidebar.selectbox("Model", models)
    
    # Load both experiments
    exp1 = load_policies(selected_model, "1")
    exp2 = load_policies(selected_model, "2")
    
    if not exp1 and not exp2:
        st.error("No policies found. Run generator first.")
        return
    
    # Get CVE list
    cves = list(set(list(exp1.keys()) + list(exp2.keys())))
    selected_cve = st.sidebar.selectbox("Vulnerability", sorted(cves))
    
    # Display
    st.subheader(f"{selected_model} - {selected_cve}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Experiment 1: Standardized + RAG")
        if selected_cve in exp1:
            policy1 = exp1[selected_cve]
            st.markdown(policy1)
            st.metric("Word Count", len(policy1.split()))
            
            # Extract citations
            nist_count = policy1.count("NIST")
            iso_count = policy1.count("ISO")
            st.metric("NIST Citations", nist_count)
            st.metric("ISO Citations", iso_count)
        else:
            st.warning("No policy generated")
    
    with col2:
        st.markdown("### Experiment 2: Tailored + RAG")
        if selected_cve in exp2:
            policy2 = exp2[selected_cve]
            st.markdown(policy2)
            st.metric("Word Count", len(policy2.split()))
            
            # Extract citations
            nist_count = policy2.count("NIST")
            iso_count = policy2.count("ISO")
            st.metric("NIST Citations", nist_count)
            st.metric("ISO Citations", iso_count)
        else:
            st.warning("No policy generated")
    
    # Comparison stats
    if selected_cve in exp1 and selected_cve in exp2:
        st.markdown("---")
        st.subheader("Quick Comparison")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            diff = len(exp2[selected_cve].split()) - len(exp1[selected_cve].split())
            st.metric("Word Count Difference", diff, delta=diff)
        
        with col2:
            has_timeline_1 = "days" in exp1[selected_cve].lower() or "timeline" in exp1[selected_cve].lower()
            has_timeline_2 = "days" in exp2[selected_cve].lower() or "timeline" in exp2[selected_cve].lower()
            st.metric("Exp 1 Has Timeline", "✓" if has_timeline_1 else "✗")
            st.metric("Exp 2 Has Timeline", "✓" if has_timeline_2 else "✗")
        
        with col3:
            sections_1 = exp1[selected_cve].count("**")
            sections_2 = exp2[selected_cve].count("**")
            st.metric("Exp 1 Sections", sections_1)
            st.metric("Exp 2 Sections", sections_2)

if __name__ == "__main__":
    main()