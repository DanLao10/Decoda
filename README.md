# Decoda

**Decoda** is an accessibility-first Streamlit app that helps dyslexic and neurodivergent readers tackle dense documents. Upload a PDF, and Decoda rewrites it in clear, dyslexia-friendly language, lets you listen to it, and exports a readable PDF in fonts like Lexend or OpenDyslexic.

## Features

- **PDF decoder** — Extracts text from PDFs and rewrites it with short sentences, plain vocabulary, clear headings, and bullet points (preserving meaning).
- **Dyslexia-friendly export** — Downloads the rewritten content as a PDF with Lexend / OpenDyslexic typefaces, increased line and letter spacing, and generous margins.
- **Text-to-speech** — Listen to the rewritten content directly in the browser.
- **Reading preferences** — Per-account theme settings (font, size, spacing, color) saved to Firestore and applied across the app.
- **Built-in chatbot** — A sidebar assistant that explains how Decoda works and helps troubleshoot.
- **Accounts** — Email/password sign-up and login via Firebase Authentication.

## Tech stack

- **Frontend / app framework:** Streamlit
- **Auth:** Firebase Authentication (Admin SDK + REST `signInWithPassword`)
- **Database:** Cloud Firestore (user preferences)
- **AI:** OpenAI API (text simplification + chatbot)
- **PDF:** PyPDF2 (extraction), ReportLab (export)
- **TTS:** Browser `SpeechSynthesis` (with `pyttsx3` fallback for WAV export)

## Project layout

```
main.py         # Entry point + sidebar nav
home.py         # Landing page
account.py      # Login / signup (Firebase)
translator.py   # PDF upload, AI simplification, dyslexia-friendly PDF export
chatbot.py      # Sidebar Q&A assistant
tts.py          # Text-to-speech component
about.py        # About page
user_data.py    # Firestore prefs + Firebase init helpers
```

## Running locally

1. **Clone and install:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Add secrets** in `.streamlit/secrets.toml` (gitignored):
   ```toml
   API_KEY = "sk-..."                                 # OpenAI
   FIREBASE_API_KEY = "AIza..."                       # Firebase Web API key
                                                      # (Project Settings → General → Your apps)
   [firebase]
   # Paste contents of your Firebase service-account JSON here.
   # Use triple quotes for the multi-line private_key.
   type = "service_account"
   project_id = "your-project"
   private_key_id = "..."
   private_key = """-----BEGIN PRIVATE KEY-----
   ...
   -----END PRIVATE KEY-----
   """
   client_email = "..."
   client_id = "..."
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "..."
   universe_domain = "googleapis.com"
   ```

3. **Enable Email/Password sign-in** in the Firebase Console
   (Authentication → Sign-in method → Email/Password → Enable).

4. **Run:**
   ```bash
   streamlit run main.py
   ```

## Deploying to Streamlit Cloud

Push to GitHub, connect the repo on [share.streamlit.io](https://share.streamlit.io), and paste the same `secrets.toml` contents into the app's **Settings → Secrets** editor. Make sure the `FIREBASE_API_KEY` and the `[firebase]` service account belong to the **same** Firebase project — otherwise sign-up will land users in one project and login will look in another.

## Notes & limitations

- Decoda only works on PDFs with **extractable text**. Scanned image PDFs need OCR first.
- Math formulas, complex tables, and multi-column layouts may simplify imperfectly.
- Uploaded documents are processed only for the current session; nothing is persisted server-side.
