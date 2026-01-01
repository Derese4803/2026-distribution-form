import streamlit as st
import pandas as pd
import base64
import zipfile
from io import BytesIO
from sqlalchemy import inspect, text
from database import SessionLocal, engine
from models import BackCheck, Base
from auth import check_password

# --- INITIALIZATION ---
st.set_page_config(page_title="OAF Nursery Back Check", layout="wide", page_icon="🌳")

def init_db():
    Base.metadata.create_all(bind=engine)
    # Self-healing: Check for missing columns
    inspector = inspect(engine)
    cols = [c['name'] for c in inspector.get_columns('oaf_back_checks')]
    with engine.connect() as conn:
        for c_name in ['cbe_acc', 'auto_remark', 'general_remark', 'photo']:
            if c_name not in cols:
                conn.execute(text(f"ALTER TABLE oaf_back_checks ADD COLUMN {c_name} TEXT"))
        conn.commit()

init_db()

def process_photo(file):
    return base64.b64encode(file.getvalue()).decode() if file else None

if "page" not in st.session_state: st.session_state["page"] = "Form"

def nav(p):
    st.session_state["page"] = p
    st.rerun()

def main():
    st.sidebar.title("OAF Nursery 🌳")
    if st.sidebar.button("📝 Form / ፎርም", use_container_width=True): nav("Form")
    if st.sidebar.button("📊 Data / መረጃ", use_container_width=True): nav("Data")

    if st.session_state["page"] == "Form":
        st.title("🚜 Nursery Back Check Form")
        db = SessionLocal()
        with st.form("main_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            w = c1.text_input("Woreda"); cl = c2.text_input("Cluster"); k = c3.text_input("Kebele"); t = c4.text_input("TNO")
            p1, p2, p3, p4 = st.columns(4)
            fa = p1.text_input("FA Name"); acc = p2.text_input("CBE ACC"); ph = p3.text_input("Phone")
            fn = p4.radio("Fenced?", ["Yes", "No"], horizontal=True)

            def get_rem(val, exp, name):
                if val == 0: return ""
                return f"{name}: Correct" if val == exp else f"{name}: {val-exp:+} diff"

            def section(name, amharic, exp):
                st.markdown(f"--- \n### {name} ({amharic}) - Exp: {exp}")
                sc1, sc2, sc3 = st.columns(3)
                nb = sc1.number_input(f"{name} beds", 0, key=f"n_{name}")
                ln = sc2.number_input(f"{name} length", 0.0, key=f"l_{name}")
                sk = sc3.number_input(f"{name} sockets", 0, key=f"s_{name}")
                return nb, ln, sk

            g_n, g_l, g_s = section("Guava", "ዘይቶን", 13)
            ge_n, ge_l, ge_s = section("Gesho", "ጌሾ", 16)
            l_n, l_l, l_s = section("Lemon", "ሎሚ", 13)
            gr_n, gr_l, gr_s = section("Grevillea", "ግራቪሊያ", 16)

            st.markdown("---")
            up_img = st.file_uploader("Upload Photo", type=['jpg', 'png', 'jpeg'])
            rem = st.text_area("General Remarks")

            if st.form_submit_button("Submit"):
                auto = " | ".join(filter(None, [get_rem(g_s, 13, "Guava"), get_rem(ge_s, 16, "Gesho"), 
                                              get_rem(l_s, 13, "Lemon"), get_rem(gr_s, 16, "Grev")]))
                new_rec = BackCheck(woreda=w, cluster=cl, kebele=k, tno_name=t, checker_fa_name=fa, 
                                   cbe_acc=acc, checker_phone=ph, fenced=fn, guava_beds=g_n, guava_length=g_l,
                                   guava_sockets=g_s, total_guava_sockets=g_n*g_s, gesho_beds=ge_n, 
                                   gesho_length=ge_l, gesho_sockets=ge_s, total_gesho_sockets=ge_n*ge_s,
                                   lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s, total_lemon_sockets=l_n*l_s,
                                   grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s, 
                                   total_grevillea_sockets=gr_n*gr_s, auto_remark=auto, general_remark=rem, 
                                   photo=process_photo(up_img))
                db.add(new_rec); db.commit(); st.success("Saved!")
        db.close()

    elif st.session_state["page"] == "Data":
        if check_password():
            st.title("📊 Records")
            db = SessionLocal()
            recs = db.query(BackCheck).all()
            if recs:
                # Photo ZIP Download
                buf = BytesIO()
                with zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                    for r in recs:
                        if r.photo: zf.writestr(f"ID_{r.id}_{r.kebele}.jpg", base64.b64decode(r.photo))
                st.download_button("📥 Download Photo ZIP", buf.getvalue(), "photos.zip")

                for r in recs:
                    with st.container(border=True):
                        c_t, c_i = st.columns([3, 1])
                        c_t.write(f"**ID:** {r.id} | **Kebele:** {r.kebele} | **Status:** {r.auto_remark}")
                        c_t.write(f"**Remarks:** {r.general_remark}")
                        if r.photo: c_i.image(base64.b64decode(r.photo))
                        if st.button(f"Delete {r.id}", key=f"d_{r.id}"):
                            db.delete(r); db.commit(); st.rerun()
            db.close()

if __name__ == "__main__": main()
