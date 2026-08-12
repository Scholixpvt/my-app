 import json
import os
import streamlit as st

BLOCKLIST_FILE = "blocklist.json"


def load_blocklist():
    if os.path.exists(BLOCKLIST_FILE):
        try:
            with open(BLOCKLIST_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass

    return [
        "mcri.edu.au",
        "uowmail.edu.au",
        "jefferson.edu",
        "waitematadhb.govt.nz",
        "southerntrust.hscni.net",
        "mft.nhs.uk",
        "duke.edu",
        "nhs.net",
        "sydney.edu.au",
        "monashhealth.org",
        "rcoa.ac.uk",
        "hubruxelles.be",
        "alumni.uct.ac.za",
        "uw.edu",
        "hsc.wvu.edu",
        "gazeta.pl",
        "doctors.org.uk",
        "unimelb.edu.au",
        "ggc.scot.nhs.uk",
        "adelaide.edu.au",
        "uct.ac.za",
        "florey.edu.au",
        "icatt.it",
        "universitadipavia.it",
        "karmanos.org",
        "zums.ac.ir",
        "biology.gatech.edu",
        "sheffield.ac.uk",
        "anthro.ox.ac.uk",
        "ccf.org",
        "ahn.org",
        "uni.edu",
        "thewrightcenter.org",
        "nd.edu",
        "ndph.ox.ac.uk",
        "cdc.gov",
        "mums.ac.ir",
        "mail.utoronto.ca",
        "env.cn",
        "umsha.ac.ir",
        "africa-union.org",
        "acu.edu.in",
        "mlodz.pl",
        "stanford.edu",
        "cmu.edu.cn",
        "med.edu",
    ]


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
st.sidebar.write(
    "Domains listed here will be flagged as **BLOCKED** during email verification."
)
new_domain = st.sidebar.text_input("Add Domain to Block (e.g. domain.com):")

if st.sidebar.button("➕ Add Domain to Blocklist"):
    if new_domain:
        clean_domain = new_domain.strip().lower()
        if clean_domain not in st.session_state.blocked_domains:
            st.session_state.blocked_domains.append(clean_domain)
            save_blocklist(st.session_state.blocked_domains)
            st.sidebar.success(f"Added `{clean_domain}` to blocklist!")
        else:
            st.sidebar.warning(f"`{clean_domain}` is already in the blocklist.")
