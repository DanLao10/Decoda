import streamlit as st
import user_data

def app():
    user_data.apply_reading_theme()

    st.title("Welcome to :violet[Decoda]")

    st.markdown(
        """
        **Decoda helps make reading easier.**

        Upload a document, and Decoda will rewrite the text in a clear,
        dyslexia-friendly format. You can also listen to the text and
        download a readable PDF.
        """
    )

    st.markdown("---")

    st.markdown(
        """
        ### How to get started
        1. Select **Decoder Tool** from the left sidebar.
        2. Upload a text-based PDF.
        3. Click **Translate** to simplify the text.
        4. Read, listen, or download the decoded version.
        """
    )

    st.markdown("---")

    st.markdown(
        """
        ### Who Decoda is for
        - People with dyslexia
        - Neurodivergent readers
        - Anyone who finds dense text hard to read
        """
    )

    st.info(
        "Decoda works best with PDFs that contain selectable text. "
        "Scanned images may not extract correctly."
    )

    st.markdown("---")
    user_data.render_quick_prefs(location="expander")
