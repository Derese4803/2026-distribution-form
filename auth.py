import streamlit as st

# 1. User Database
# For small teams, you can manage users here. 
# For higher security, you could move these to Streamlit Secrets.
USERS = {
    "admin": "amhara2025",
    "surveyor1": "field01",
    "derese": "pass123",
    "supervisor": "check2025"
}

def check_auth():
    """
    Checks if the user is authenticated.
    If not, it displays the login form and stops execution of the main app.
    """
    if "user" not in st.session_state:
        st.title("🚜 2025 Amhara Survey Login")
        st.markdown("Please enter your credentials to access the registration system.")
        
        # Create a login form
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Enter System")
            
            if submit_button:
                if username in USERS and USERS[username] == password:
                    st.session_state["user"] = username
                    st.success(f"Welcome, {username}!")
                    st.rerun() # Refresh to show the main app
                else:
                    st.error("❌ Invalid Username or Password. Please try again.")
        
        # This stops the rest of app.py from running if not logged in
        st.stop()

def logout():
    """Clears the session and logs the user out."""
    if "user" in st.session_state:
        del st.session_state["user"]
    if "page" in st.session_state:
        st.session_state["page"] = "Home"
    st.rerun()
