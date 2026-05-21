# Decoda

> Make dense reading easier. Upload a PDF, get a clear, dyslexia-friendly version you can read, hear, and download.

**Live app:** https://decoda.streamlit.app/

Decoda is an accessibility-first reading tool for dyslexic and neurodivergent readers. It rewrites complex text into shorter sentences and simpler vocabulary, then presents it in a typography setup designed for easier reading — with text-to-speech and a downloadable, dyslexia-friendly PDF.

## What it does

- **Decode any PDF.** Upload a text-based PDF and Decoda rewrites it preserving meaning while using short sentences, plain vocabulary, clear headings, and bullets.
- **Read it your way.** Choose Lexend or OpenDyslexic, adjust size, spacing, and color to fit how *you* read best. Preferences save to your account.
- **Listen to it.** Built-in text-to-speech reads the simplified version aloud.
- **Take it with you.** Download the rewritten content as a dyslexia-friendly PDF (Lexend / OpenDyslexic, generous spacing, clean margins).
- **Ask the assistant.** A built-in chatbot explains how Decoda works and helps troubleshoot.

## Who it's for

- Readers with dyslexia
- Neurodivergent readers
- Anyone who finds dense, jargon-heavy text exhausting

## How to use it

1. Visit https://decoda.streamlit.app/ (use light mode)
2. Create an account (email + password).
3. Open the **Decoder** tab and upload a text-based PDF.
4. Click **Translate** to simplify.
5. Read on screen, listen with the TTS player, or download the dyslexia-friendly PDF.

> Decoda works best with PDFs that contain **selectable text**. Scanned-image PDFs need OCR first.

## Built with

- [Streamlit](https://streamlit.io) — UI
- [Firebase](https://firebase.google.com) — Authentication + Firestore for user preferences
- [OpenAI](https://openai.com) — text simplification + assistant chatbot
- [PyPDF2](https://pypi.org/project/PyPDF2/) + [ReportLab](https://www.reportlab.com/) — PDF parsing and export
- [Lexend](https://www.lexend.com/) and [OpenDyslexic](https://opendyslexic.org/) typefaces

## Limitations

- Only works on PDFs with extractable text (not scanned images).
- Complex tables, multi-column layouts, and mathematical formulas may simplify imperfectly.
- Uploaded files are processed only for the current session — nothing is stored server-side.

## Running locally

```bash
git clone https://github.com/<your-username>/Decoda.git
cd Decoda
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run main.py
```

You'll need your own `.streamlit/secrets.toml` with an OpenAI API key, a Firebase Web API key, and a Firebase service-account JSON (under a `[firebase]` table). Make sure both Firebase credentials belong to the same project, and enable Email/Password sign-in in the Firebase console.

## License

MIT
