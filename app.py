import streamlit as st
import pandas as pd
from database import SessionLocal, engine
from models import BackCheck, Base

# --- APP CONFIG ---
st.set_page_config(page_title="OAF Nursery Back Check", layout="wide", page_icon="🌳")

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

if "page" not in st.session_state:
    st.session_state["page"] = "Form"

def nav(p):
    st.session_state["page"] = p
    st.rerun()

def main():
    page = st.session_state["page"]
    
    # --- SIDEBAR ---
    st.sidebar.title("OAF Nursery 🌳")
    if st.sidebar.button("📝 Registration Form", use_container_width=True): nav("Form")
    if st.sidebar.button("📊 View Records", use_container_width=True): nav("Data")

    # --- FORM PAGE ---
    if page == "Form":
        st.title("🚜 Nursery Back Check Form")
        db = SessionLocal()

        with st.form("oaf_form", clear_on_submit=True):
            st.subheader("📍 Location & Personnel")
            c1, c2, c3, c4 = st.columns(4)
            w_val = c1.text_input("Woreda (ወረዳ)")
            cl_val = c2.text_input("Cluster (ክላስተር)")
            k_val = c3.text_input("Kebele (ቀበሌ)")
            t_val = c4.text_input("TNO Name (የTNO ስም)")

            p1, p2, p3, p4 = st.columns(4)
            f_val = p1.text_input("FA Name (የFA ስም)")
            acc_val = p2.text_input("CBE ACC (የCBE ሂሳብ ቁጥር)")
            ph_val = p3.text_input("Phone (ስልክ)")
            fn_val = p4.radio("Fenced? (አጥር?)", ["Yes", "No"], horizontal=True)

            def bed_section(species, amharic):
                st.markdown(f"--- \n### 🌿 {species} ({amharic})")
                bc1, bc2, bc3 = st.columns(3)
                n = bc1.number_input(f"{species} beds #", min_value=0, step=1, key=f"n_{species}")
                l = bc2.number_input(f"Length (m)", min_value=0.0, step=0.1, key=f"l_{species}")
                s = bc3.number_input(f"Sockets (width)", min_value=0, step=1, key=f"s_{species}")
                return n, l, s

            g_n, g_l, g_s = bed_section("Guava", "ዘይቶን")
            ge_n, ge_l, ge_s = bed_section("Gesho", "ጌሾ")
            l_n, l_l, l_s = bed_section("Lemon", "ሎሚ")
            gr_n, gr_l, gr_s = bed_section("Grevillea", "ግራቪሊያ")

            if st.form_submit_button("Submit Data"):
                try:
                    new_rec = BackCheck(
                        woreda=w_val, cluster=cl_val, kebele=k_val, tno_name=t_val,
                        checker_fa_name=f_val, cbe_acc=acc_val, checker_phone=ph_val, fenced=fn_val,
                        guava_beds=g_n, guava_length=g_l, guava_sockets=g_s, total_guava_sockets=g_n*g_s,
                        gesho_beds=ge_n, gesho_length=ge_l, gesho_sockets=ge_s, total_gesho_sockets=ge_n*ge_s,
                        lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s, total_lemon_sockets=l_n*l_s,
                        grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s, total_grevillea_sockets=gr_n*gr_s
                    )
                    db.add(new_rec); db.commit()
                    st.success("✅ Saved!")
                except Exception as e:
                    st.error(f"Error: {e}")
        db.close()

    # --- DATA PAGE ---
    elif page == "Data":
        st.title("📊 Records")
        db = SessionLocal()
        recs = db.query(BackCheck).all()
        if recs:
            df = pd.DataFrame([r.__dict__ for r in recs])
            # ORDER: Bed -> Length -> Sockets for each species
            cols = [
                'id', 'woreda', 'cluster', 'kebele', 'tno_name', 'checker_fa_name', 'cbe_acc', 'checker_phone',
                'guava_beds', 'guava_length', 'guava_sockets',
                'gesho_beds', 'gesho_length', 'gesho_sockets',
                'lemon_beds', 'lemon_length', 'lemon_sockets',
                'grevillea_beds', 'grevillea_length', 'grevillea_sockets',
                'fenced'
            ]
            df = df[[c for c in cols if c in df.columns]]
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 Download CSV", df.to_csv(index=False), "nursery_data.csv")
        db.close()

if __name__ == "__main__":
    main()
