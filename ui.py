import os

import streamlit as st
from dotenv import load_dotenv

from src.runner import run_outreach

load_dotenv()


def _render_table(title: str, rows: list[dict[str, str]], empty_message: str) -> None:
    st.subheader(title)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info(empty_message)


def _render_download(path: str, label: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, "rb") as f:
        st.download_button(
            label=label,
            data=f.read(),
            file_name=os.path.basename(path),
            mime="text/csv",
            use_container_width=True,
        )


st.set_page_config(
    page_title="LinkedIn Outreach",
    page_icon="Inbox",
    layout="wide",
)

st.title("LinkedIn Outreach")
st.caption("Run LinkedIn lead discovery, email pattern detection, and CSV export from a friendlier local UI.")

with st.sidebar:
    st.header("Run Settings")
    criteria = st.text_input("Criteria", value="co-founder", help='Examples: "co-founder", "founder", "recruiter"')
    max_results = st.slider("Max results", min_value=5, max_value=100, value=25, step=5)
    output_dir = st.text_input("Output folder", value="output_ui")
    cookies_file = st.text_input(
        "Cookies file",
        value=os.getenv("LINKEDIN_COOKIES_FILE", "linkedin_cookies.json"),
    )
    run_clicked = st.button("Run Outreach", type="primary", use_container_width=True)

st.markdown(
    """
    This app uses your existing LinkedIn session cookies. If the cookies are missing,
    a browser window will open so you can log in once and save them.
    """
)

if run_clicked:
    if not criteria.strip():
        st.error("Enter a search criteria before running.")
    else:
        log_box = st.empty()
        logs: list[str] = []

        def add_log(message: str) -> None:
            logs.append(message)
            log_box.code("\n".join(logs), language="text")

        with st.spinner("Running outreach workflow..."):
            result = run_outreach(
                criteria=criteria.strip(),
                max_results=max_results,
                output_dir=output_dir.strip() or "output_ui",
                cookies_file=cookies_file.strip() or "linkedin_cookies.json",
                log=add_log,
            )

        if not result["profiles_found"]:
            st.warning("No profiles were found. Try a different criteria or refresh your LinkedIn session.")
        else:
            a, b, c, d = st.columns(4)
            a.metric("Profiles Found", result["profiles_found"])
            b.metric("Verified", result["verified"])
            c.metric("Rejected", result["rejected"])
            d.metric("Skipped", result["skipped"])

            left, right = st.columns(2)
            with left:
                _render_download(result["verified_path"], "Download Verified CSV")
            with right:
                _render_download(result["rejected_path"], "Download Rejected CSV")

            _render_table(
                "Verified Leads",
                result["verified_rows"],
                "No verified leads were produced in this run.",
            )
            _render_table(
                "Rejected Leads",
                result["rejected_rows"],
                "No rejected leads were produced in this run.",
            )
