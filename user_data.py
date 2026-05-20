"""Firestore-backed user metadata: reading preferences and decode history."""
from __future__ import annotations

import os
import json

import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore

# Local fallback only — not used in production. Production reads st.secrets["firebase"].
_LOCAL_CRED_PATH = "decoda-99a3b-084c6c2b6705.json"


def _service_account_dict() -> dict:
    """Return Firebase service-account credentials as a dict.

    Prefers st.secrets["firebase"] (Streamlit Cloud). Falls back to the local
    JSON file for development.
    """
    if "firebase" in st.secrets:
        data = dict(st.secrets["firebase"])
        # In TOML, private_key newlines may have been stored as literal '\n'.
        pk = data.get("private_key", "")
        if "\\n" in pk and "\n" not in pk:
            data["private_key"] = pk.replace("\\n", "\n")
        return data
    if os.path.exists(_LOCAL_CRED_PATH):
        with open(_LOCAL_CRED_PATH, "r") as f:
            return json.load(f)
    raise RuntimeError(
        "Firebase credentials not found. Set st.secrets['firebase'] or place "
        f"{_LOCAL_CRED_PATH} in the project root."
    )

DEFAULT_PREFS = {
    "text_color": "#1a1a1a",
    "background_color": "#fdf6e3",
    "font_family": "Lexend",
    "font_size": 18,
    "line_spacing": 1.8,
    "letter_spacing": 0.06,
    "word_spacing": 0.12,
}


def _get_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(_service_account_dict())
        return firebase_admin.initialize_app(cred)


def _db():
    return firestore.client(_get_app())


def _user_ref(uid: str):
    return _db().collection("users").document(uid)


def load_preferences(uid: str) -> dict:
    if not uid:
        return dict(DEFAULT_PREFS)
    snap = _user_ref(uid).get()
    data = snap.to_dict() if snap.exists else {}
    prefs = dict(DEFAULT_PREFS)
    prefs.update((data or {}).get("preferences", {}))
    return prefs


def save_preferences(uid: str, prefs: dict) -> None:
    if not uid:
        return
    _user_ref(uid).set({"preferences": prefs}, merge=True)


def save_decode(uid: str, *, source: str, mode: str, input_text: str, output_text: str) -> None:
    if not uid:
        return
    _user_ref(uid).collection("decodes").add({
        "source": source,
        "mode": mode,
        "input_preview": input_text[:500],
        "input_length": len(input_text),
        "output": output_text,
        "created_at": firestore.SERVER_TIMESTAMP,
    })


def list_recent_decodes(uid: str, limit: int = 10) -> list[dict]:
    if not uid:
        return []
    q = (
        _user_ref(uid)
        .collection("decodes")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    return [doc.to_dict() | {"id": doc.id} for doc in q.stream()]


_FONT_CSS_STACK = {
    "Lexend": "'Lexend', system-ui, sans-serif",
    "OpenDyslexic": "'OpenDyslexic', 'Comic Sans MS', sans-serif",
    "Helvetica": "Helvetica, Arial, sans-serif",
    "Times": "'Times New Roman', Times, serif",
    "Courier": "'Courier New', Courier, monospace",
    "Arial": "Arial, Helvetica, sans-serif",
    "Verdana": "Verdana, Geneva, sans-serif",
    "Comic Sans MS": "'Comic Sans MS', 'Comic Sans', cursive",
}


def get_current_prefs() -> dict:
    """Load prefs for the signed-in user (cached on session) or defaults."""
    uid = st.session_state.get("username", "")
    cached = st.session_state.get("_prefs_cache")
    cached_uid = st.session_state.get("_prefs_cache_uid")
    if cached and cached_uid == uid:
        return cached
    try:
        prefs = load_preferences(uid) if uid else dict(DEFAULT_PREFS)
    except Exception:
        prefs = dict(DEFAULT_PREFS)
    st.session_state["_prefs_cache"] = prefs
    st.session_state["_prefs_cache_uid"] = uid
    return prefs


def clear_prefs_cache() -> None:
    st.session_state.pop("_prefs_cache", None)
    st.session_state.pop("_prefs_cache_uid", None)


def apply_reading_theme(prefs: dict | None = None) -> None:
    """Inject CSS that styles the main Streamlit content with the user's reading prefs."""
    if prefs is None:
        prefs = get_current_prefs()
    family = prefs.get("font_family", "Lexend")
    css_family = _FONT_CSS_STACK.get(family, f"'{family}', sans-serif")
    bg = prefs.get("background_color", "#fdf6e3")
    fg = prefs.get("text_color", "#1a1a1a")
    size = int(prefs.get("font_size", 18))
    line = float(prefs.get("line_spacing", 1.8))
    letter = float(prefs.get("letter_spacing", 0.06))
    word = float(prefs.get("word_spacing", 0.12))
    st.markdown(
        f"""
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700&display=swap');
          html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {{
            background: {bg} !important;
          }}
          /* Sidebar + top header: match the page background so the whole window feels unified. */
          [data-testid="stSidebar"],
          [data-testid="stSidebar"] > div:first-child,
          [data-testid="stSidebarContent"],
          [data-testid="stHeader"] {{
            background: {bg} !important;
          }}
          /* Subtle divider between sidebar and main content. */
          [data-testid="stSidebar"] {{
            border-right: 1px solid rgba(0, 0, 0, 0.18) !important;
            box-shadow: 2px 0 6px rgba(0, 0, 0, 0.06) !important;
          }}
          /* Make sidebar text use the user's chosen text color (but skip the option_menu
             which sets its own black background + white text via inline styles). */
          [data-testid="stSidebar"] .stMarkdown,
          [data-testid="stSidebar"] label,
          [data-testid="stSidebar"] p,
          [data-testid="stSidebar"] h1,
          [data-testid="stSidebar"] h2,
          [data-testid="stSidebar"] h3 {{
            color: {fg} !important;
          }}
          [data-testid="stAppViewContainer"] .main .block-container {{
            background: {bg} !important;
            font-family: {css_family} !important;
          }}
          /* Body text: apply font + reading prefs, but only color paragraphs/lists so
             headings, buttons, and colored markdown (e.g. :violet[]) keep their own color. */
          [data-testid="stMarkdownContainer"] p,
          [data-testid="stMarkdownContainer"] li,
          [data-testid="stMarkdownContainer"] blockquote,
          [data-testid="stAppViewContainer"] .main .block-container p,
          [data-testid="stAppViewContainer"] .main .block-container li {{
            font-family: {css_family} !important;
            font-size: {size}px !important;
            line-height: {line} !important;
            letter-spacing: {letter}em !important;
            word-spacing: {word}em !important;
            color: {fg} !important;
          }}
          /* Headings: same font family + spacing, force user's text color so they're
             readable on the cream/light background. Inline color markers like
             :violet[...] use inline style on a child span, which still wins. */
          [data-testid="stAppViewContainer"] .main .block-container h1,
          [data-testid="stAppViewContainer"] .main .block-container h2,
          [data-testid="stAppViewContainer"] .main .block-container h3,
          [data-testid="stAppViewContainer"] .main .block-container h4 {{
            font-family: {css_family} !important;
            letter-spacing: {letter}em !important;
            color: {fg} !important;
          }}
          [data-testid="stAppViewContainer"] .main .block-container h1 {{ font-size: {int(size*2.0)}px !important; line-height: 1.2 !important; }}
          [data-testid="stAppViewContainer"] .main .block-container h2 {{ font-size: {int(size*1.5)}px !important; line-height: 1.25 !important; }}
          [data-testid="stAppViewContainer"] .main .block-container h3 {{ font-size: {int(size*1.25)}px !important; line-height: 1.3 !important; }}
          [data-testid="stAppViewContainer"] .main .block-container h4 {{ font-size: {int(size*1.1)}px !important; line-height: 1.35 !important; }}
          /* Force any inline span (like :violet[Decoda]) inside a heading to inherit the heading's size. */
          [data-testid="stAppViewContainer"] .main .block-container h1 *,
          [data-testid="stAppViewContainer"] .main .block-container h2 *,
          [data-testid="stAppViewContainer"] .main .block-container h3 *,
          [data-testid="stAppViewContainer"] .main .block-container h4 * {{
            font-size: inherit !important;
            line-height: inherit !important;
            font-family: inherit !important;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_quick_prefs(location: str = "expander") -> dict:
    """Render a compact prefs editor; saves to Firestore for signed-in users.

    Returns the (possibly updated) prefs dict.
    """
    prefs = dict(get_current_prefs())
    uid = st.session_state.get("username", "")

    container = st.expander("⚙️ Reading preferences", expanded=False) if location == "expander" else st.container()
    with container:
        c1, c2 = st.columns(2)
        with c1:
            prefs["font_family"] = st.selectbox(
                "Font",
                list(_FONT_CSS_STACK.keys()),
                index=list(_FONT_CSS_STACK.keys()).index(prefs.get("font_family", "Lexend"))
                if prefs.get("font_family", "Lexend") in _FONT_CSS_STACK else 0,
                key=f"qp_font_{location}",
            )
            prefs["font_size"] = st.slider("Text size", 12, 32, int(prefs.get("font_size", 18)), key=f"qp_size_{location}")
            prefs["line_spacing"] = st.slider("Line spacing", 1.0, 3.0, float(prefs.get("line_spacing", 1.8)), 0.1, key=f"qp_line_{location}")
        with c2:
            prefs["text_color"] = st.color_picker("Text color", prefs.get("text_color", "#1a1a1a"), key=f"qp_fg_{location}")
            prefs["background_color"] = st.color_picker("Background", prefs.get("background_color", "#fdf6e3"), key=f"qp_bg_{location}")
            prefs["letter_spacing"] = st.slider("Letter spacing", 0.0, 0.3, float(prefs.get("letter_spacing", 0.06)), 0.01, key=f"qp_letter_{location}")
            prefs["word_spacing"] = st.slider("Word spacing", 0.0, 0.6, float(prefs.get("word_spacing", 0.12)), 0.02, key=f"qp_word_{location}")

        b1, b2 = st.columns(2)
        with b1:
            if st.button("💾 Save preferences", key=f"qp_save_{location}", use_container_width=True):
                if uid:
                    try:
                        save_preferences(uid, prefs)
                        clear_prefs_cache()
                        st.success("Saved!")
                    except Exception as e:
                        st.error(f"Could not save: {e}")
                else:
                    st.info("Sign in to save these across devices.")
                st.session_state["_prefs_cache"] = prefs
                st.session_state["_prefs_cache_uid"] = uid
        with b2:
            if st.button("↺ Reset", key=f"qp_reset_{location}", use_container_width=True):
                prefs = dict(DEFAULT_PREFS)
                st.session_state["_prefs_cache"] = prefs
                st.session_state["_prefs_cache_uid"] = uid
                if uid:
                    try:
                        save_preferences(uid, prefs)
                    except Exception:
                        pass
                st.rerun()

    return prefs
