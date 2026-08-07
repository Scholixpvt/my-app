import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Advanced Email Verification ERP", page_icon="📧", layout="wide")

BLOCKLIST_FILE = "blocklist.json"

# Helper function to load domains from local file
def load_blocklist():
    if os.path.exists(BLOCKLIST_FILE):
        try:
            with open(BLOCKLIST_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    # Default list if file doesn't exist yet
    return ["mcri.edu.au", "uowmail.edu.au"]

# Helper function to save domains to local file
def save_blocklist(domains):
    with open(BLOCKLIST_FILE, "w") as f:
        json.dump(domains, f)

# Load saved domains into session state on app launch
if "blocked_domains" not in st.session_state:
    st.session_state.blocked_domains = load_blocklist()

# ---------------------------------------------------------
# SIDEBAR: BLOCKLIST MANAGER
# ---------------------------------------------------------
st.sidebar.title("🛑 Blocklist Manager")
st.sidebar.write("Add bouncing or unwanted domains to permanently filter them out in future verifications.")

new_domain = st.sidebar.text_input("Add Domain to Block (e.g. domain.com):")

if st.sidebar.button("➕ Add Domain to Blocklist"):
    if new_domain:
        clean_domain = new_domain.strip().lower()
        if clean_domain not in st.session_state.blocked_domains:
            st.session_state.blocked_domains.append(clean_domain)
            save_blocklist(st.session_state.blocked_domains)  # <--- Saves to file permanently!
            st.sidebar.success(f"Added {clean_domain}!")
            st.rerun()

st.sidebar.write(f"### Current Blocked Domains ({len(st.session_state.blocked_domains)})")

for domain in list(st.session_state.blocked_domains):
    col1, col2 = st.sidebar.columns([4, 1])
    col1.code(domain)
    if col2.button("❌", key=f"del_{domain}"):
        st.session_state.blocked_domains.remove(domain)
        save_blocklist(st.session_state.blocked_domains)  # <--- Saves removal to file permanently!
        st.rerun()

# ---------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------
st.title("📧 Advanced Email Verification ERP")
st.write("Upload your CSV file to perform multi-stage local verification while preserving all original data columns.")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("### File Preview")
    st.dataframe(df.head())
