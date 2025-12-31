import streamlit as st
import pandas as pd
from database import SessionLocal, engine
from models import BackCheck, Base

# --- INITIALIZATION ---
st.set_page_config(page_title="OAF Nursery Back Check", layout="wide", page_icon="🌳")

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

# --- NAVIGATION ---
if "page" not in st.session_state:
    st.session_state["page"] = "Form"

def nav(p):
    st.session_state["page"] = p
    st.rerun()

def main():
    page = st.session_state["page"]
    
    st.sidebar.title("OAF Nursery 🌳")
    st.sidebar.markdown("---")
    if st.sidebar.button("📝 Registration Form", use_container_width=True): nav("Form")
    if st.sidebar.button("📊 View Records", use_container_width=True): nav("Data")

    # --- PAGE 1: REGISTRATION FORM ---
    if page == "Form":
        st.title("🚜 OAF Nursery Back Check Form")
        db = SessionLocal()

        with st.form("oaf_form", clear_on_submit=True):
            st.subheader("📍 Location & Personnel")
            c1, c2, c3, c4 = st.columns(4)
            woreda = c1.text_input("Woreda")
            cluster = c2.text_input("Cluster")
            kebele = c3.text_input("Kebele")
            tno_name = c4.text_input("TNO Name")

            p1, p2, p3, p4 = st.columns(4)
            fa_name = p1.text_input("Name of Back checker (FAs)")
            cbe_name = p2.text_input("Back checker (CBE)")
            phone = p3.text_input("Back checker phone #")
            fenced = p4.radio("Is Nursery Fenced?", ["Yes", "No"], horizontal=True)

            st.markdown("---")

            # Helper function for bed sections
            def bed_section(species, expected):
                st.markdown(f"### 🌿 {species}")
                st.caption(f"Expectation: **{expected}** sockets in the width.")
                bc1, bc2, bc3 = st.columns(3)
                n = bc1.number_input(f"{species} beds number", min_value=0, step=1, key=f"n_{species}")
                l = bc2.number_input(f"Length of {species} (m)", min_value=0.0, step=0.1, key=f"l_{species}")
                s = bc3.number_input(f"Sockets in width", min_value=0, step=1, key=f"s_{species}")
                return n, l, s

            # Organized Input Sections
            g_n, g_l, g_s = bed_section("Guava", 13)
            ge_n, ge_l, ge_s = bed_section("Gesho", 16)
            l_n, l_l, l_s = bed_section("Lemon", 13)
            gr_n, gr_l, gr_s = bed_section("Grevillea", 16)

            # Calculations (ALL SPECIES)
            t_guava = g_n * g_s
            t_gesho = ge_n * ge_s
            t_lemon = l_n * l_s
            t_grevillea = gr_n * gr_s

            st.markdown("---")
            st.subheader("📊 Automatic Calculations (Total Sockets)")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Guava", t_guava)
            m2.metric("Total Gesho", t_gesho)
            m3.metric("Total Lemon", t_lemon)
            m4.metric("Total Grevillea", t_grevillea)

            if st.form_submit_button("Submit OAF Back Check"):
                if not woreda or not kebele or not fa_name:
                    st.error("Woreda, Kebele, and FAs Name are required!")
                else:
                    new_record = BackCheck(
                        woreda=woreda, cluster=cluster, kebele=kebele, tno_name=tno_name,
                        checker_fa_name=fa_name, checker_cbe_name=cbe_name,
                        checker_phone=phone, fenced=fenced,
                        guava_beds=g_n, guava_length=g_l, guava_sockets=g_s, total_guava_sockets=t_guava,
                        gesho_beds=ge_n, gesho_length=ge_l, gesho_sockets=ge_s, total_gesho_sockets=t_gesho,
                        lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s, total_lemon_sockets=t_lemon,
                        grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s, total_grevillea_sockets=t_grevillea
                    )
                    db.add(new_record)
                    db.commit()
                    st.success(f"✅ Data for {kebele} saved successfully!")
                    st.balloons()
        db.close()

    # --- PAGE 2: DATA VIEW & DELETE ---
    elif page == "Data":
        st.title("📊 OAF Recorded Survey Data")
        db = SessionLocal()
        records = db.query(BackCheck).all()
        
        if records:
            df = pd.DataFrame([r.__dict__ for r in records])
            
            # --- STRICT COLUMN ORDERING ---
            cols = [
                'id', 'woreda', 'cluster', 'kebele', 'tno_name', 
                'checker_fa_name', 'checker_cbe_name', 'checker_phone',
                'guava_beds', 'guava_length', 'guava_sockets', 'total_guava_sockets',
                'gesho_beds', 'gesho_length', 'gesho_sockets', 'total_gesho_sockets',
                'lemon_beds', 'lemon_length', 'lemon_sockets', 'total_lemon_sockets',
                'grevillea_beds', 'grevillea_length', 'grevillea_sockets', 'total_grevillea_sockets',
                'fenced', 'timestamp'
            ]
            
            df = df[[c for c in cols if c in df.columns]]
            display_df = df.copy()
            display_df.columns = [c.replace('_', ' ').title() for c in display_df.columns]
            
            st.dataframe(display_df, use_container_width=True)

            st.markdown("---")
            st.subheader("🗑️ Data Management")
            del_c1, del_c2 = st.columns([1, 2])
            
            with del_c1:
                id_to_del = st.number_input("Enter ID to Delete", min_value=1, step=1)
                if st.button("❌ Delete Selected ID", type="primary"):
                    target = db.query(BackCheck).filter(BackCheck.id == id_to_del).first()
                    if target:
                        db.delete(target)
                        db.commit()
                        st.success(f"ID {id_to_del} removed.")
                        st.rerun()
                    else:
                        st.error("ID not found.")
            
            with del_c2:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Export CSV", data=csv, file_name="OAF_Nursery_Data.csv")
        else:
            st.info("No records found.")
        db.close()

if __name__ == "__main__":
    main()
