import pyttsx3
import tempfile
from pathlib import Path
import streamlit.components.v1 as components
import html
import streamlit as st

def tts_to_wav_bytes(text: str) -> bytes:
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)  # adjust speaking speed

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name

    engine.save_to_file(text, tmp_path)
    engine.runAndWait()

    data = Path(tmp_path).read_bytes()
    Path(tmp_path).unlink(missing_ok=True)
    return data



def tts_component(text: str, key: str = "tts", rate: float = 0.95):
    safe_text = html.escape(text).replace("\n", " ")

    components.html(
        f"""
        <div style="font-family: system-ui; display:flex; gap:10px; align-items:center;">
          <button id="{key}_speak" style="padding:8px 12px; cursor:pointer;">🔊 Speak</button>
          <button id="{key}_stop" style="padding:8px 12px; cursor:pointer;">⏹ Stop</button>
          <span id="{key}_status" style="opacity:0.8;">Loaded ✅</span>
        </div>

        <script>
          (function() {{
            const status = document.getElementById("{key}_status");
            const speakBtn = document.getElementById("{key}_speak");
            const stopBtn = document.getElementById("{key}_stop");
            const text = "{safe_text}";

            function pickEnglishVoice() {{
              const voices = window.speechSynthesis.getVoices() || [];
              return voices.find(v => (v.lang || "").toLowerCase().startsWith("en")) || voices[0];
            }}

            function speak() {{
              try {{
                if (!("speechSynthesis" in window)) {{
                  status.textContent = "TTS not supported in this browser.";
                  return;
                }}
                if (!text || text.trim().length === 0) {{
                  status.textContent = "No text to read.";
                  return;
                }}

                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance(text);
                u.rate = {rate};
                u.pitch = 1.0;
                u.volume = 1.0;

                const v = pickEnglishVoice();
                if (v) u.voice = v;

                u.onstart = () => status.textContent = "Speaking…";
                u.onend = () => status.textContent = "Done ✅";
                u.onerror = (e) => status.textContent = "Error: " + (e.error || "unknown");

                window.speechSynthesis.speak(u);
              }} catch (err) {{
                status.textContent = "JS error: " + err;
              }}
            }}

            speakBtn.onclick = speak;
            stopBtn.onclick = () => {{
              window.speechSynthesis.cancel();
              status.textContent = "Stopped.";
            }};

            window.speechSynthesis.onvoiceschanged = () => {{}};
          }})();
        </script>
        """,
        height=80,
    )


def app():
    st.title(":violet[Text-to-Speech]")
    if st.button("🔊 Generate audio"):
        text = st.session_state.get("decoded_text", "")
        if not text:
            st.info("No decoded text yet. Go to Translator first.")
        else:
            tts_component(text, key="decoded")
            st.markdown(text)
