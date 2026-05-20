import streamlit as st
import firebase_admin
from firebase_admin import auth, credentials
import requests
import user_data

FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]

def firebase_login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    resp = requests.post(url, json={
        "email": email,
        "password": password,
        "returnSecureToken": True
    })
    data = resp.json()
    if resp.status_code != 200:
        # Bubble up the real Firebase error
        raise ValueError(data.get("error", {}).get("message", "LOGIN_FAILED"))
    return data

def get_firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(user_data._service_account_dict())
        return firebase_admin.initialize_app(cred)

def app():
    get_firebase_app()
    user_data.apply_reading_theme()
    st.title("Welcome to :violet[Decoda]!")

    # Initialize session state
    for key, default in [
        ("username", ""),
        ("useremail", ""),
        ("signedout", False),   # False -> show login/signup
        ("signout", False),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    def login_callback():
        email = st.session_state.login_email
        password = st.session_state.login_password
        try:
            data = firebase_login(email, password)
            st.session_state.username = data.get("localId", "")
            st.session_state.useremail = data.get("email", "")
            st.session_state.signedout = True
            st.session_state.signout = True
            st.success("Login Successful")
        except Exception as e:
            st.error(f"Login failed: {e}")

    def signout_callback():
        st.session_state.signedout = False
        st.session_state.signout = False
        st.session_state.username = ""
        st.session_state.useremail = ""

    if not st.session_state.signedout:
        choice = st.radio("", ["Login", "Sign Up"], horizontal=True)

        if choice == "Login":
            st.text_input("Email Address", key="login_email")
            st.text_input("Password", type="password", key="login_password")
            st.button("Login", on_click=login_callback)
        else:
            email = st.text_input("Enter Your Email Address")
            username = st.text_input("Enter your unique username")
            password = st.text_input("Please select a Password", type="password")

            if st.button("Create my account"):
                try:
                    user = auth.create_user(email=email, password=password, uid=username)
                    st.success("Account created successfully!")
                    st.markdown("Please login with your email and password")
                    st.balloons()
                except Exception as e:
                    st.error(f"Signup failed: {e}")

    if st.session_state.signout:
        st.text("Username: " + st.session_state.username)
        st.text("Email: " + st.session_state.useremail)
        st.button("Sign Out", on_click=signout_callback)

        st.markdown("---")
        st.subheader("Reading preferences")
        st.caption("Customize how text appears across Decoda. Saved to your account.")
        user_data.render_quick_prefs(location="account")
