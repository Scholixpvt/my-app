import streamlit as st
import dns.resolver
import pandas as pd
import re
import json
import os

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Advanced Email Verification ERP",
    page_icon="📧",
    layout="wide"
)

BLOCKLIST_FILE = "blocklist.json"

# Helper functions to persist blocklist to file
def load_blocklist():
    if os.path.exists(BLOCKLIST_FILE):
        try:
            with open(BLOCKLIST_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return ["mcri.edu.au", "uowmail.edu.au"]

def save_blocklist(domains):
    with open(BLOCKLIST_FILE, "w") as f:
        json.dump(domains, f)

# Initialize Session State
if "blocked_domains" not in st.session_state:
    st.session_state.blocked_domains = load_blocklist()

# ---------------------------------------------------------
# 1. SIDEBAR: BLOCKLIST MANAGER
# ---------------------------------------------------------
st.sidebar.title("🛑 Blocklist Manager")
st.sidebar.write("Domains listed here will be flagged as **BLOCKED** during email verification.")

new_domain = st.sidebar.text_input("Add Domain to Block (e.g. domain.com):")

if st.sidebar.button("➕ Add Domain to Blocklist"):
    if new_domain:
        clean_domain = new_domain.strip().lower()
        if clean_domain not in st.session_state.blocked_domains:
            st.session_state.blocked_domains.append(clean_domain)
            save_blocklist(st.session_state.blocked_domains)
            st.sidebar.success(f"Added {clean_domain}!")
            st.rerun()

st.sidebar.write(f"### Current Blocked Domains ({len(st.session_state.blocked_domains)})")

for domain in list(st.session_state.blocked_domains):
    col1, col2 = st.sidebar.columns([4, 1])
    col1.code(domain)
    if col2.button("❌", key=f"del_{domain}"):
        st.session_state.blocked_domains.remove(domain)
        save_blocklist(st.session_state.blocked_domains)
        st.rerun()

# ---------------------------------------------------------
# 2. EMAIL VERIFICATION ENGINE
# ---------------------------------------------------------
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

def check_mx_record(domain):
    """Checks if domain has valid MX (Mail Exchange) DNS records."""
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return len(answers) > 0
    except Exception:
        return False

def verify_single_email(email, blocklist):
    """Verifies a single email against syntax, blocklist, and DNS."""
    if not isinstance(email, str) or not email.strip():
        return "Invalid / Empty", "Missing Email"
    
    email = email.strip().lower()
    
    # 1. Regex Syntax Check
    if not re.match(EMAIL_REGEX, email):
        return "Invalid Syntax", "Malformed Email Address"
    
    domain = email.split("@")[-1]
    
    # 2. Blocklist Check (LINKED TO ERP)
    if domain in blocklist:
        return "Blocked Domain", f"Domain '{domain}' is in Blocklist"
    
    # 3. MX DNS Record Check
    if not check_mx_record(domain):
        return "Invalid Domain", f"No MX Records for '{domain}'"
    
    return "Valid", "Passed All Checks"

# ---------------------------------------------------------
# 3. MAIN ERP INTERFACE & FILE UPLOAD
# ---------------------------------------------------------
st.title("📧 Advanced Email Verification ERP")
st.write("Upload your CSV file to perform multi-stage local verification linked directly to your Blocklist Manager.")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    st.write("### 1. Data Preview")
    st.dataframe(df.head(5), use_container_width=True)
    
    # Select Email Column
    columns = df.columns.tolist()
    email_col = st.selectbox("Select the column containing email addresses:", columns)
    
    if st.button("🚀 Start Verification Process", type="primary"):
        with st.spinner("Processing emails against Syntax, MX Records, and Blocklist..."):
            
            statuses = []
            reasons = []
            
            # Run verification linked to current active blocklist
            current_blocklist = set(st.session_state.blocked_domains)
            
            for idx, row in df.iterrows():
                email_val = row[email_col]
                status, reason = verify_single_email(email_val, current_blocklist)
                statuses.append(status)
                reasons.append(reason)
            
            # Attach verification results while preserving all original columns
            df["Verification_Status"] = statuses
            df["Verification_Reason"] = reasons
            
            st.success("Verification Completed!")
            
            # Summary Metrics
            st.write("### 2. Verification Summary")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Records", len(df))
            m2.metric("Valid Emails", len(df[df["Verification_Status"] == "Valid"]))
            m3.metric("Blocked Domains", len(df[df["Verification_Status"] == "Blocked Domain"]))
            m4.metric("Invalid / Failed", len(df[~df["Verification_Status"].isin(["Valid", "Blocked Domain"])]))
            
            st.write("### 3. Detailed Results")
            st.dataframe(df, use_container_width=True)
            
            # Download Button for Updated CSV
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Verified CSV Results",
                data=csv_data,
                file_name="verified_email_results.csv",
                mime="text/csv"
            )
