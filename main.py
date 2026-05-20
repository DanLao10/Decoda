import streamlit as st
from streamlit_option_menu import option_menu
import home, account, about, translator
import chatbot

st.session_state.setdefault("signedout", False)
st.session_state.setdefault("signout",  False)

st.set_page_config(
    page_title="Decoda",
    layout="wide",
)

class MultiApp:
    def __init__(self):
        self.apps = []
    def add_app(self, title, function):
        self.apps.append({
            "title": title,
            "function": function
        })
    def run(self):
        with st.sidebar:
            if st.session_state.signedout == True and st.session_state.signout == True:
                app = option_menu(
                    menu_title="Decoda",
                    options=["Home", "Decoder", "Account"],
                    icons=["house-fill", "translate", "person-circle"],
                    menu_icon="arrow-down",
                    default_index=0,
                    styles={
                        "container": {"padding": "5!important", "background-color": "black"},
                        "icon": {"color": "white", "font-size": "23px"},
                        "nav-link": {"color": "white", "font-size": "20px", "text-align": "left", "margin": "0px"},
                        "nav-link-selected": {"background-color": "#02ab21"},
                        "menu-title": {"color": "#b388ff", "font-weight": "700"},
                        "menu-icon": {"color": "#b388ff"},
                    }
                )
                st.sidebar.header("Decoda Chatbot")
                question = st.sidebar.text_input(
                    "Ask Decoda Chatbot any question!")
                if st.sidebar.button("Ask"):
                    answer = chatbot._llm_reply(question, st.secrets["API_KEY"])
                    st.sidebar.write(answer)
                if st.sidebar.button("Clear"):
                    st.sidebar.write("")
            else:
                app = option_menu(
                    menu_title="Decoda",
                    options=["Account"],
                    icons=["key"],
                    menu_icon="arrow-down",
                    default_index=0,
                    styles={
                        "container": {"padding": "5!important", "background-color": "black"},
                        "icon": {"color": "white", "font-size": "23px"},
                        "nav-link": {"color": "white", "font-size": "20px", "text-align": "left", "margin": "0px"},
                        "nav-link-selected": {"background-color": "#02ab21"},
                        "menu-title": {"color": "#b388ff", "font-weight": "700"},
                        "menu-icon": {"color": "#b388ff"},
                    }
                )
        if app== "Home":
            home.app()
        if app== "Account":
            account.app()
        if app== "About":
            about.app()
        if app== "Decoder":
            translator.app()

app = MultiApp()
app.run()


