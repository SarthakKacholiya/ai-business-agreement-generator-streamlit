import os
import uuid
from datetime import date
import streamlit as st

from generator.builder import (
    AVAILABLE_TEMPLATES,
    load_template,
    render_template,
    build_txt,
    build_docx,
    build_pdf,
    ensure_output_dir,
)

# ---------- Page config ----------
st.set_page_config(
    page_title="AI Business Agreement Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- CSS ----------
st.markdown("""
<style>
/* page */
section.main > div { padding-top: 1rem; }
h1, h2, h3 { letter-spacing: .2px; }
.kbd { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background:#f4f4f5; padding:.15rem .4rem; border-radius:.35rem; border:1px solid #e4e4e7; }
/* cards */
.card {
  background: white; border:1px solid #e5e7eb; border-radius:16px; padding:18px;
  box-shadow: 0 6px 18px rgba(2,6,23,.06);
}
.preview {
  white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  line-height:1.6; font-size:.95rem;
}
.stTabs [data-baseweb="tab"] { font-weight:600; }
.stButton>button {
  background: #2563eb; color: white; border-radius:10px; padding:.6rem 1rem; border:none;
}
.stButton>button:hover { background:#1e40af; }
.badge {
  display:inline-block; font-size:.75rem; padding:.2rem .5rem; border-radius:.4rem;
  background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe;
}
</style>
""", unsafe_allow_html=True)

# ---------- App title ----------
st.title("📄 AI Business Agreement Generator")
st.caption("Streamlit • Python 3.12.6 • PDF / DOCX / TXT export")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")
    st.write("Choose a template and fill in details. A live preview is shown on the right.")
    template_name = st.selectbox("Agreement template", AVAILABLE_TEMPLATES, index=0)
    st.divider()
    st.subheader("Export options")
    want_pdf = st.checkbox("PDF", value=True)
    want_docx = st.checkbox("DOCX", value=True)
    want_txt = st.checkbox("TXT", value=False)
    st.divider()
    st.markdown("Need help? Press <span class='kbd'>?</span> to open Streamlit help.", unsafe_allow_html=True)

# ---------- Inputs ----------
left, right = st.columns([0.9, 1.1], vertical_alignment="top")

with left:
    st.subheader("📝 Agreement details")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            party1 = st.text_input("First party", placeholder="Company A / John Doe")
            start_date = st.date_input("Start date", value=date.today())
            scope = st.text_area("Scope / Services", height=100, placeholder="Describe the services/scope…")
        with c2:
            party2 = st.text_input("Second party", placeholder="Company B / Jane Smith")
            end_date = st.date_input("End date", value=date.today())
            compensation = st.text_area("Compensation / Consideration", height=100, placeholder="Fees, milestones, etc.")

        governing_law = st.text_input("Governing law", placeholder="California / India")
        special_terms = st.text_area("Special terms (optional)", height=100, placeholder="Any additional clauses…")

        # Build input dict used by the renderer
        input_data = {
            "party1": party1,
            "party2": party2,
            "start_date": start_date.isoformat() if start_date else "",
            "end_date": end_date.isoformat() if end_date else "",
            "governing_law": governing_law,
            "scope": scope,
            "compensation": compensation,
            "special_terms": special_terms,
            "today": date.today().isoformat(),
            "agreement_type": template_name,
        }

        st.caption("Fields left blank will be omitted gracefully in the final text.")

        gen_btn = st.button("✨ Generate & Save", type="primary", use_container_width=True)

with right:
    st.subheader("👀 Live preview")
    with st.container():
        template_text = load_template(template_name)
        preview_text = render_template(template_text, input_data)
        st.markdown(f"<div class='card preview'>{preview_text}</div>", unsafe_allow_html=True)

# ---------- Generate & offer downloads ----------
if gen_btn:
    # basic validation
    missing = [k for k in ("party1", "party2", "start_date", "end_date", "governing_law") if not input_data.get(k)]
    if missing:
        st.error("Please fill these required fields: " + ", ".join(missing))
    else:
        ensure_output_dir()
        uid = uuid.uuid4().hex[:12]
        base = f"{template_name.lower()}_{uid}"

        saved = {}
        if want_txt:
            saved["TXT"] = build_txt(preview_text, os.path.join("output", f"{base}.txt"))
        if want_docx:
            saved["DOCX"] = build_docx(preview_text, os.path.join("output", f"{base}.docx"))
        if want_pdf:
            saved["PDF"] = build_pdf(preview_text, os.path.join("output", f"{base}.pdf"))

        st.success("✅ Agreement generated!")
        st.markdown("<div class='badge'>Saved to /output</div>", unsafe_allow_html=True)

        # download buttons
        dcols = st.columns(len(saved) or 1)
        for (fmt, path), col in zip(saved.items(), dcols):
            with col:
                with open(path, "rb") as f:
                    st.download_button(
                        label=f"⬇️ Download {fmt}",
                        data=f.read(),
                        file_name=os.path.basename(path),
                        mime="application/octet-stream",
                        use_container_width=True,
                    )

        # keep simple history in session
        hist = st.session_state.get("history", [])
        hist.append({"template": template_name, "file_map": saved, "ts": date.today().isoformat()})
        st.session_state["history"] = hist

# ---------- History ----------
st.divider()
with st.expander("🕘 Recent files (this session)"):
    history = st.session_state.get("history", [])
    if not history:
        st.caption("No files generated yet.")
    else:
        for i, item in enumerate(reversed(history[-8:]), start=1):
            st.write(f"**{i}. {item['template']}** — {item['ts']}")
            inline = []
            for fmt, path in item["file_map"].items():
                inline.append(f"`{os.path.basename(path)}`")
            st.caption(" • ".join(inline))
