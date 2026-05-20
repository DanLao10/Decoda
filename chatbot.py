from openai import OpenAI

APP_SPEC = """
Decoda is an accessibility-first Streamlit application designed to help dyslexic and neurodivergent users
read complex documents more easily.

Core functionality:
- Users upload a text-based PDF.
- The app extracts readable text from the PDF.
- An AI model rewrites the text to be dyslexia-friendly by:
  - Preserving meaning and factual content
  - Using short sentences and simple vocabulary
  - Organizing content with clear headings and bullet points
  - Reducing ambiguity by making references explicit
- The rewritten text is displayed in a clean, readable format.
- The rewritten text can be exported as a dyslexia-friendly PDF using:
  - Lexend font
  - Increased line spacing
  - Increased letter spacing
  - Proper margin wrapping to prevent overflow
- The app provides text-to-speech so users can listen to the rewritten content.
- Users can download the decoded PDF and optionally the audio output.

Design principles:
- Accessibility-first (dyslexia-friendly typography and layout)
- Minimal cognitive load
- Clear feedback and predictable behavior
- No unnecessary animations or distractions
- Privacy-conscious: uploaded documents are processed only for the current session

Limitations:
- Works only with PDFs that contain extractable text (not scanned images).
- Mathematical formulas, tables, and complex layouts may be simplified or read imperfectly.
"""



SYSTEM_PROMPT = (
    "You are the built-in assistant for 'Decoda,' an accessibility-focused Streamlit app that helps dyslexic "
    "and neurodivergent users read documents more easily. Decoda allows users to upload PDFs, converts the text "
    "into a dyslexia-friendly version using clear language and structure, provides text-to-speech playback, "
    "and enables downloading a readable PDF. Your role is to explain how Decoda works, guide users through its "
    "features, and help troubleshoot issues related to PDF uploads, text conversion, readability, downloads, "
    "and text-to-speech. Be accurate, concise, supportive, and avoid speculation or hallucinations."
)



def _as_parts(text: str):
    return [{"type": "text", "text": text}]


def _llm_reply(question, api_key, model="gpt-4.1-mini"):
    client = OpenAI(api_key=api_key)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "assistant",
            "content": (
                "Here is everything you know about the Byte-Sized Business Boost app:\n\n"
                f"{APP_SPEC}\n\n"
                "Use this as the source of truth when helping the user."
            ),
        },
        {
            "role": "user",
            "content": (
                "Answer the following user question using the app description above. "
                "If the question cannot be answered from that context, say you don't know.\n\n"
                f"User question: {question}"
            ),
        },
    ]

    response = client.chat.completions.create(
        model=model,  # fill in with your preferred OpenAI model
        messages=messages,
    )

    return response.choices[0].message.content
