import streamlit as st
import pandas as pd
from database import SessionLocal, engine
from models import BackCheck, Base

# --- INITIALIZATION ---
st.set_page_config(page_title="OAF Nursery Back Check", layout="wide", page_icon="🌳")

def init_db():
    # This creates the tables. If you changed the model, you MUST delete the .db file first.
    Base.metadata.create_all(bind=engine)

init_db()

if "page" not in st.session_state:
    st.session_state["page"] = "Form"

def nav(p):
    st.session_state["page"] = p
    st.rerun()

def main():
    page = st.session_state["page"]
    
    st.sidebar.title("OAF Nursery 🌳")
    st.sidebar.markdown("---")
    if st.sidebar.button("📝 Registration Form / መመዝገቢያ ፎርም", use_container_width=True): nav("Form")
    if st.sidebar.button("📊 View Records / መረጃዎችን ይመልከቱ", use_container_width=True): nav("Data")

    if page == "Form":
        st.title("🚜 OAF Nursery Back Check Form")
        db = SessionLocal()

        with st.form("oaf_form", clear_on_submit=True):
            st.subheader("📍 Location & Personnel / ቦታ እና ሰራተኛ")
            
            c1, c2, c3, c4 = st.columns(4)
            w_val = c1.text_input("Woreda (ወረዳ)")
            cl_val = c2.text_input("Cluster (ክላስተር)")
            k_val = c3.text_input("Kebele (ቀበሌ)")
            t_val = c4.text_input("TNO Name (የTNO ስም)")

            p1, p2, p3, p4 = st.columns(4)
            f_val = p1.text_input("Name of Back checker FAs (የFA ስም)")
            cb_val = p2.text_input("Back checker CBE (የCBE ስም)")
            ph_val = p3.text_input("Back checker phone # (ስልክ ቁጥር)")
            fn_val = p4.radio("Is Nursery Fenced? (አጥር አለው?)", ["Yes (አዎ)", "No (የለም)"], horizontal=True)

            st.markdown("---")

            def bed_section(species, amharic):
                st.markdown(f"### 🌿 {species} ({amharic})")
                bc1, bc2, bc3 = st.columns(3)
                n = bc1.number_input(f"{species} beds # ({amharic} አልጋ ብዛት)", min_value=0, step=1, key=f"n_{species}")
                l = bc2.number_input(f"Length (m) (ርዝመት)", min_value=0.0, step=0.1, key=f"l_{species}")
                s = bc3.number_input(f"Sockets in width (የጎን ሶኬት)", min_value=0, step=1, key=f"s_{species}")
                return n, l, s

            g_n, g_l, g_s = bed_section("Guava", "ዘይቶን")
            ge_n, ge_l, ge_s = bed_section("Gesho", "ጌሾ")
            l_n, l_l, l_s = bed_section("Lemon", "ሎሚ")
            gr_n, gr_l, gr_s = bed_section("Grevillea", "ግራቪሊያ")

            # Calculations
            t_guava, t_gesho = g_n * g_s, ge_n * ge_s
            t_lemon, t_grevillea = l_n * l_s, gr_n * gr_s

            st.markdown("---")
            st.subheader("📊 Totals / አጠቃላይ ድምር")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Guava (ዘይቶን)", t_guava)
            m2.metric("Gesho (ጌሾ)", t_gesho)
            m3.metric("Lemon (ሎሚ)", t_lemon)
            m4.metric("Grevillea (ግራቪሊያ)", t_grevillea)

            if st.form_submit_button("Submit Data / መረጃውን መዝግብ"):
                if not w_val or not k_val or not f_val:
                    st.error("Woreda, Kebele, and FAs Name are required! / ወረዳ፣ ቀበሌ እና የFA ስም ይሙሉ!")
                else:
                    try:
                        new_record = BackCheck(
                            woreda=w_val, cluster=cl_val, kebele=k_val, tno_name=t_val,
                            checker_fa_name=f_val, checker_cbe_name=cb_val,
                            checker_phone=ph_val, fenced=fn_val,
                            guava_beds=g_n, guava_length=g_l, guava_sockets=g_s, total_guava_sockets=t_guava,
                            gesho_beds=ge_n, gesho_length=ge_l, gesho_sockets=ge_s, total_gesho_sockets=t_gesho,
                            lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s, total_lemon_sockets=t_lemon,
                            grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s, total_grevillea_sockets=t_grevillea
                        )
                        db.add(new_record)
                        db.commit()
                        st.success("✅ Saved! / መረጃው ተመዝግቧል!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Error: {e}. Please delete your .db file and try again.")
        db.close()

    elif page == "Data":
        st.title("📊 Recorded Data / የተመዘገቡ መረጃዎች")
        db = SessionLocal()
        records = db.query(BackCheck).all()
        if records:
            df = pd.DataFrame([r.__dict__ for r in records]).drop('_sa_instance_state', axis=1, errors='ignore')
            
            # Bilingual Headers for Table
            rename_map = {
                'woreda': 'ወረዳ (Woreda)', 'cluster': 'ክላስተር (Cluster)', 
                'kebele': 'ቀበሌ (Kebele)', 'tno_name': 'የTNO ስም (TNO Name)',
                'total_guava_sockets': 'ድምር ዘይቶን', 'total_gesho_sockets': 'ድምር ጌሾ',
                'total_lemon_sockets': 'ድምር ሎሚ', 'total_grevillea_sockets': 'ድምር ግራቪሊያ'
            }
            st.dataframe(df.rename(columns=rename_map), use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV / መረጃውን አውርድ", data=csv, file_name="nursery_backcheck.csv")
        else:
            st.info("No records found. / ምንም መረጃ የለም::")
        db.close()

if __name__ == "__main__":
    main()
