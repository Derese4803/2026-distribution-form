import streamlit as st
import pandas as pd
from database import SessionLocal, engine
from models import BackCheck, Base

# --- INITIALIZATION ---
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
    if st.sidebar.button("📝 Registration Form / መመዝገቢያ ፎርም", use_container_width=True): nav("Form")
    if st.sidebar.button("📊 View & Delete / መረጃዎችን ይመልከቱ እና ያጥፉ", use_container_width=True): nav("Data")

    if page == "Form":
        st.title("🚜 Nursery Back Check Form / የችግኝ ጣቢያ ቁጥጥር ፎርም")
        db = SessionLocal()

        with st.form("oaf_form", clear_on_submit=True):
            st.subheader("📍 Location & Personnel / ቦታ እና ሰራተኛ")
            c1, c2, c3, c4 = st.columns(4)
            w_val = c1.text_input("Woreda / ወረዳ")
            cl_val = c2.text_input("Cluster / ክላስተር")
            k_val = c3.text_input("Kebele / ቀበሌ")
            t_val = c4.text_input("TNO Name / የTNO ስም")

            p1, p2, p3, p4 = st.columns(4)
            f_val = p1.text_input("FA Name / የFA ስም")
            acc_val = p2.text_input("CBE ACC / የCBE ሂሳብ ቁጥር")
            ph_val = p3.text_input("Phone / ስልክ ቁጥር")
            fn_val = p4.radio("Is Nursery Fenced? / አጥር አለው?", ["Yes / አዎ", "No / የለም"], horizontal=True)

            # Helper function to calculate remarks
            def get_remark(val, expected, name):
                if val == 0: return ""
                if val == expected: return f"{name}: Correct"
                elif val > expected: return f"{name}: Over Expectation (+{val-expected})"
                else: return f"{name}: Under Expectation (-{expected-val})"

            def bed_section(species, amharic, expected):
                st.markdown(f"--- \n### 🌿 {species} ({amharic})")
                st.info(f"💡 Expected: **{expected}** sockets. / የሚጠበቀው፡ **{expected}** ሶኬቶች።")
                bc1, bc2, bc3 = st.columns(3)
                n = bc1.number_input(f"{amharic} beds #", min_value=0, step=1, key=f"n_{species}")
                l = bc2.number_input(f"{amharic} Length (m)", min_value=0.0, step=0.1, key=f"l_{species}")
                s = bc3.number_input(f"{amharic} Sockets width", min_value=0, step=1, key=f"s_{species}")
                return n, l, s

            g_n, g_l, g_s = bed_section("Guava", "ዘይቶን", 13)
            ge_n, ge_l, ge_s = bed_section("Gesho", "ጌሾ", 16)
            l_n, l_l, l_s = bed_section("Lemon", "ሎሚ", 13)
            gr_n, gr_l, gr_s = bed_section("Grevillea", "ግራቪሊያ", 16)

            st.markdown("---")
            st.subheader("📝 Additional Remarks / ተጨማሪ ማስታወሻ")
            gen_remark = st.text_area("General Remarks / አጠቃላይ አስተያየት", placeholder="Enter any other observations here...")

            if st.form_submit_button("Submit Data / መረጃውን መዝግብ"):
                # Generate Auto-Remarks based on input
                remarks_list = [
                    get_remark(g_s, 13, "Guava"),
                    get_remark(ge_s, 16, "Gesho"),
                    get_remark(l_s, 13, "Lemon"),
                    get_remark(gr_s, 16, "Grevillea")
                ]
                auto_rem = " | ".join([r for r in remarks_list if r != ""])

                try:
                    new_rec = BackCheck(
                        woreda=w_val, cluster=cl_val, kebele=k_val, tno_name=t_val,
                        checker_fa_name=f_val, cbe_acc=acc_val, checker_phone=ph_val, fenced=fn_val,
                        guava_beds=g_n, guava_length=g_l, guava_sockets=g_s, total_guava_sockets=g_n*g_s,
                        gesho_beds=ge_n, gesho_length=ge_l, gesho_sockets=ge_s, total_gesho_sockets=ge_n*ge_s,
                        lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s, total_lemon_sockets=l_n*l_s,
                        grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s, total_grevillea_sockets=gr_n*gr_s,
                        auto_remark=auto_rem,
                        general_remark=gen_remark
                    )
                    db.add(new_rec); db.commit()
                    st.success("✅ Saved Successfully! / መረጃው ተመዝግቧል!")
                except Exception as e:
                    st.error(f"Error / ስህተት: {e}")
        db.close()

    elif page == "Data":
        st.title("📊 Recorded Data / የተመዘገቡ መረጃዎች")
        db = SessionLocal()
        
        with st.expander("🗑️ Delete a Record / መረጃን አጥፋ"):
            del_id = st.number_input("Enter ID to Delete", min_value=1, step=1)
            if st.button("Confirm Delete", type="primary"):
                target = db.query(BackCheck).filter(BackCheck.id == del_id).first()
                if target:
                    db.delete(target); db.commit()
                    st.success(f"Record {del_id} deleted!")
                    st.rerun()

        recs = db.query(BackCheck).all()
        if recs:
            df = pd.DataFrame([r.__dict__ for r in recs])
            # Include remarks in columns
            cols = [
                'id', 'kebele', 'checker_fa_name', 
                'guava_sockets', 'gesho_sockets', 'lemon_sockets', 'grevillea_sockets',
                'auto_remark', 'general_remark'
            ]
            df = df[[c for c in cols if c in df.columns]]
            
            rename_map = {
                'id': 'ID', 'kebele': 'Kebele / ቀበሌ', 'checker_fa_name': 'FA Name',
                'auto_remark': 'System Remark / ሲስተም ማስታወሻ',
                'general_remark': 'General Remark / አጠቃላይ አስተያየት'
            }
            
            st.dataframe(df.rename(columns=rename_map), use_container_width=True)
            st.download_button("📥 Export CSV", df.to_csv(index=False), "nursery_data.csv")
        db.close()

if __name__ == "__main__":
    main()
