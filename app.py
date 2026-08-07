import streamlit as st
import dns.resolver
import pandas as pd
import re

# Page config
st.set_page_config(page_title="Advanced Email Verification ERP", page_icon="📧", layout="wide")

# ---------------------------------------------------------
# 1. BLOCKLIST MANAGEMENT (SESSION STATE)
# ---------------------------------------------------------
if "blocked_domains" not in st.session_state:
    # Initial default domains
    st.session_state.blocked_domains = ["mcri.edu.au", "uowmail.edu.au"]

# Sidebar Blocklist UI
st.sidebar.title("🛑 Blocklist Manager")
st.sidebar.write("Add bouncing or unwanted domains to permanently filter them out in future verifications.")

new_domain = st.sidebar.text_input("Add Domain to Block (e.g. domain.com):")

if st.sidebar.button("➕ Add Domain to Blocklist"):
    if new_domain:
        clean_domain = new_domain.strip().lower()
        if clean_domain not in st.session_state.blocked_domains:
            st.session_state.blocked_domains.append(clean_domain)
            st.sidebar.success(f"Added {clean_domain}!")
            st.rerun()

st.sidebar.write(f"### Current Blocked Domains ({len(st.session_state.blocked_domains)})")

# Display blocked domains with individual delete buttons
for domain in list(st.session_state.blocked_domains):
    col1, col2 = st.sidebar.columns([4, 1])
    col1.code(domain)
    if col2.button("❌", key=f"del_{domain}"):
        st.session_state.blocked_domains.remove(domain)
        st.rerun()

# ---------------------------------------------------------
# 2. MAIN APP & FILE UPLOAD
# ---------------------------------------------------------
st.title("📧 Advanced Email Verification ERP")
st.write("Upload your CSV file to perform multi-stage local verification while preserving all original data columns.")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("### File Preview")
    st.dataframe(df.head())
    
    # Add your email verification processing logic below as needed
