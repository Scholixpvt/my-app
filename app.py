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
    page_title="Advanced Email Verification ERP  SCHOLIX PUBLICATIONS",
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
    
    # 2. Blocklist Check
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
    
    # Generate output file name based on uploaded file name
    original_filename = os.path.splitext(uploaded_file.name)[0]
    output_filename = f"{original_filename}_verified.csv"
    
    st.write("### 1. Data Preview")
    st.dataframe(df.head(5), use_container_width=True)
    
    # Select Email Column
    columns = df.columns.tolist()
    email_col = st.selectbox("Select the column containing email addresses:", columns)
    
    if st.button("🚀 Start Verification Process", type="primary"):
        with st.spinner("Processing emails against Syntax, MX Records, and Blocklist..."):
            
            valid_indices = []
            blocked_count = 0
            invalid_count = 0
            
            current_blocklist = set(st.session_state.blocked_domains)
            
            for idx, row in df.iterrows():
                email_val = row[email_col]
                status, reason = verify_single_email(email_val, current_blocklist)
                
                if status == "Valid":
                    valid_indices.append(idx)
                elif status == "Blocked Domain":
                    blocked_count += 1
                else:
                    invalid_count += 1
            
            # Keep ONLY valid rows and original CSV columns
            clean_df = df.loc[valid_indices].copy()
            
            # Remove duplicate emails within the list
            clean_df = clean_df.drop_duplicates(subset=[email_col])
            
            st.success("Verification Completed!")
            
            # Summary Metrics
            st.write("### 2. Verification Summary")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Uploaded", len(df))
            m2.metric("Clean / Valid Emails", len(clean_df))
            m3.metric("Blocked Domains Removed", blocked_count)
            m4.metric("Invalid / Failed Removed", invalid_count)
            
            st.write("### 3. Clean Data Preview (Original Fields Only)")
            st.dataframe(clean_df, use_container_width=True)
            
            # Download Button with Dynamic File Name (<filename>_verified.csv)
            csv_data = clean_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Download {output_filename} ({len(clean_df)} Valid Contacts)",
                data=csv_data,
                file_name=output_filename,
                mime="text/csv"
            )
