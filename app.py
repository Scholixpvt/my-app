import streamlit as st
import pandas as pd
import dns.resolver
import re
import os

st.set_page_config(page_title="Advanced Email Verifier ERP", layout="wide")

# File to store blocked domains permanently
BLOCKLIST_FILE = "blocked_domains.txt"

# Default domains to initialize blocklist if file doesn't exist yet
DEFAULT_BLOCKED = {"mcri.edu.au", "uowmail.edu.au"}

def load_blocked_domains():
    if not os.path.exists(BLOCKLIST_FILE):
        with open(BLOCKLIST_FILE, "w") as f:
            for d in DEFAULT_BLOCKED:
                f.write(f"{d}\n")
        return DEFAULT_BLOCKED
    
    with open(BLOCKLIST_FILE, "r") as f:
        domains = {line.strip().lower() for line in f if line.strip()}
    return domains

def save_blocked_domain(new_domain):
    new_domain = new_domain.strip().lower().replace("@", "")
    if new_domain:
        domains = load_blocked_domains()
        if new_domain not in domains:
            with open(BLOCKLIST_FILE, "a") as f:
                f.write(f"{new_domain}\n")
            return True, f"Added '{new_domain}' to Blocklist!"
        return False, f"'{new_domain}' is already in the Blocklist."
    return False, "Please enter a valid domain name."

def remove_blocked_domain(domain_to_remove):
    domains = load_blocked_domains()
    if domain_to_remove in domains:
        domains.remove(domain_to_remove)
        with open(BLOCKLIST_FILE, "w") as f:
            for d in domains:
                f.write(f"{d}\n")
        return True, f"Removed '{domain_to_remove}' from Blocklist."
    return False, "Domain not found."

# Load current blocklist
blocked_domains = load_blocked_domains()

# ----------------- SIDEBAR MANAGEMENT -----------------
st.sidebar.title("🛑 Blocklist Manager")
st.sidebar.write("Add bouncing or unwanted domains to permanently filter them out in future verifications.")

# Form to add new domain
new_domain_input = st.sidebar.text_input("Add Domain to Block (e.g. `domain.com`):")
if st.sidebar.button("➕ Add Domain to Blocklist"):
    success, msg = save_blocked_domain(new_domain_input)
    if success:
        st.sidebar.success(msg)
        st.rerun()
    else:
        st.sidebar.warning(msg)

st.sidebar.write("---")
st.sidebar.subheader(f"Current Blocked Domains ({len(blocked_domains)})")

# Display blocked domains with option to remove them
for d in sorted(list(blocked_domains)):
    col_a, col_b = st.sidebar.columns([3, 1])
    col_a.write(f"`{d}`")
    if col_b.button("❌", key=f"del_{d}"):
        remove_blocked_domain(d)
        st.rerun()

# ----------------- MAIN APP CONTENT -----------------
st.title("📧 Advanced Email Verification ERP")
st.write("Upload your CSV file to perform multi-stage local verification while preserving all original data columns.")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# Known Disposable Domains
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
    "sharklasers.com", "throwawaymail.com", "yopmail.com", "dispostable.com",
    "getnada.com", "trashmail.com", "tempail.com", "mytemp.email"
}

# Role-Based Account Prefixes
ROLE_PREFIXES = {
    "info", "support", "sales", "admin", "contact", "help", "billing",
    "jobs", "careers", "marketing", "office", "enquiries", "team", "hello"
}

# Common Domain Typos & Corrections
DOMAIN_TYPOS = {
    "gnail.com": "gmail.com",
    "gamil.com": "gmail.com",
    "gmal.com": "gmail.com",
    "outlok.com": "outlook.com",
    "yaho.com": "yahoo.com",
    "hotmial.com": "hotmail.com"
}

def verify_email_advanced(email, allow_roles=False, active_blocklist=set()):
    if not isinstance(email, str) or pd.isna(email):
        return "Invalid Syntax", None
    
    email = email.strip().lower()
    
    # Check Syntax
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return "Invalid Syntax", None
    
    local_part, domain = email.split('@')
    
    # Check Blocked / Suppressed Domains
    if domain in active_blocklist:
        return "Blocked Domain", None
    
    # Check Known Typos
    if domain in DOMAIN_TYPOS:
        corrected_email = f"{local_part}@{DOMAIN_TYPOS[domain]}"
        return f"Domain Typo (Suggest: {DOMAIN_TYPOS[domain]})", corrected_email

    # Check Disposable Domains
    if domain in DISPOSABLE_DOMAINS:
        return "Disposable Email", None
    
    # Check Role Accounts
    if not allow_roles and local_part in ROLE_PREFIXES:
        return "Role Account (e.g. info@, sales@)", None
    
    # Check MX Records (Domain Verification)
    try:
        dns.resolver.resolve(domain, 'MX', lifetime=2)
        return "Valid", None
    except Exception:
        return "No MX Server (Dead Domain)", None


if uploaded_file is not None:
    original_filename = os.path.splitext(uploaded_file.name)[0]
    df = pd.read_csv(uploaded_file)
    
    st.write(f"**Loaded File:** `{uploaded_file.name}` ({len(df):,} total rows across {len(df.columns)} columns)")
    
    col1, col2 = st.columns(2)
    with col1:
        col_name = st.selectbox("Select the Email Column:", df.columns)
    with col2:
        allow_roles = st.checkbox("Keep Role Emails (info@, sales@, support@)", value=False)
    
    if st.button("🚀 Start Advanced Verification"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        statuses = []
        corrections = []
        total = len(df)
        
        for idx, email in enumerate(df[col_name]):
            status, correction = verify_email_advanced(
                email, 
                allow_roles=allow_roles, 
                active_blocklist=blocked_domains
            )
            statuses.append(status)
            corrections.append(correction if correction else "")
            
            progress_bar.progress((idx + 1) / total)
            status_text.text(f"Processing {idx + 1}/{total}...")
        
        df['Verification_Status'] = statuses
        df['Suggested_Correction'] = corrections
        
        # Mark duplicates
        df['Is_Duplicate'] = df.duplicated(subset=[col_name], keep='first')
        df.loc[df['Is_Duplicate'] & (df['Verification_Status'] == "Valid"), 'Verification_Status'] = "Duplicate Email"
        
        st.success("Verification Complete!")
        
        # Split Data
        valid_df = df[df['Verification_Status'] == "Valid"]
        invalid_df = df[df['Verification_Status'] != "Valid"]
        
        # Summary Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Rows", f"{total:,}")
        m2.metric("Valid Emails", f"{len(valid_df):,}")
        m3.metric("Invalid / Flagged", f"{len(invalid_df):,}")
        m4.metric("Typos Found", f"{(df['Suggested_Correction'] != '').sum():,}")
        
        st.write("---")
        st.subheader("📥 Download Options")
        
        d_col1, d_col2 = st.columns(2)
        
        verified_file_name = f"{original_filename}_verified.csv"
        invalid_file_name = f"{original_filename}_invalid.csv"
        
        # Download 1: Verified (Uses utf-8-sig for smooth Mautic imports)
        with d_col1:
            st.markdown("### ✅ Clean & Valid List")
            st.write(f"**{len(valid_df):,}** clean emails ready for sending.")
            valid_csv = valid_df.drop(columns=['Is_Duplicate']).to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label=f"📥 Download {verified_file_name}",
                data=valid_csv,
                file_name=verified_file_name,
                mime="text/csv",
            )
            st.dataframe(valid_df.head(5))
            
        # Download 2: Flagged / Invalid
        with d_col2:
            st.markdown("### ❌ Flagged / Invalid List")
            st.write(f"**{len(invalid_df):,}** problematic rows removed.")
            invalid_csv = invalid_df.drop(columns=['Is_Duplicate']).to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label=f"📥 Download {invalid_file_name}",
                data=invalid_csv,
                file_name=invalid_file_name,
                mime="text/csv",
            )
            st.dataframe(invalid_df.head(5))
