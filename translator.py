import html
import json
from io import BytesIO
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

import user_data

# ----------------------------
# Font registration
# ----------------------------
HERE = Path(__file__).resolve().parent

FONT_FILES = {
    "Lexend": {
        "regular": HERE / "Lexend-Regular.ttf",
        "medium":  HERE / "Lexend-Medium.ttf",
        "semi":    HERE / "Lexend-SemiBold.ttf",
        "bold":    HERE / "Lexend-Bold.ttf",
    },
    "OpenDyslexic": {
        "regular": HERE / "OpenDyslexic-Regular.ttf",
        "bold":    HERE / "OpenDyslexic-Bold.ttf",
    },
}

# Register TTFs we have on disk (skip missing silently so the app still runs).
_REGISTERED: dict[str, dict[str, str]] = {}
for family, variants in FONT_FILES.items():
    registered_variants: dict[str, str] = {}
    for variant, path in variants.items():
        if path.exists():
            psname = f"{family}-{variant}"
            try:
                pdfmetrics.registerFont(TTFont(psname, str(path)))
                registered_variants[variant] = psname
            except Exception:
                pass
    if registered_variants:
        _REGISTERED[family] = registered_variants

# Built-in PDF fonts always available
_BUILTIN = {
    "Helvetica":  {"regular": "Helvetica",  "bold": "Helvetica-Bold"},
    "Times":      {"regular": "Times-Roman", "bold": "Times-Bold"},
    "Courier":    {"regular": "Courier",     "bold": "Courier-Bold"},
}

AVAILABLE_FONTS = list(_REGISTERED.keys()) + list(_BUILTIN.keys())


def _resolve_pdf_font(family: str, weight: str = "regular") -> str:
    if family in _REGISTERED:
        variants = _REGISTERED[family]
        if weight in variants:
            return variants[weight]
        # Reasonable fallbacks within the family
        for w in ("semi", "medium", "regular", "bold"):
            if w in variants:
                return variants[w]
    if family in _BUILTIN:
        return _BUILTIN[family].get(weight, _BUILTIN[family]["regular"])
    return "Helvetica"


API_KEY = st.secrets["API_KEY"]


# ----------------------------
# PDF rendering
# ----------------------------
def _hex_to_rgb01(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r / 255, g / 255, b / 255


def _wrap_with_charspace(text: str, font_name: str, font_size: int, max_width: float, char_space: float) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines, cur = [], words[0]
    for w in words[1:]:
        candidate = cur + " " + w
        glyph_w = pdfmetrics.stringWidth(candidate, font_name, font_size)
        extra = max(0, len(candidate) - 1) * char_space
        if glyph_w + extra <= max_width:
            cur = candidate
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def text_to_pdf_bytes(
    text: str,
    *,
    font_family: str = "Lexend",
    text_color: str = "#1a1a1a",
    bg_color: str = "#ffffff",
    font_size: int = 13,
    line_spacing_mult: float = 1.5,
    char_space: float = 0.4,
) -> bytes:
    font_name = _resolve_pdf_font(font_family, "regular")
    font_heading = _resolve_pdf_font(font_family, "semi") or _resolve_pdf_font(font_family, "bold")

    leading = max(int(font_size * line_spacing_mult), font_size + 2)
    left = right = top = bottom = 0.9 * inch

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    page_w, page_h = letter
    usable_w = page_w - left - right

    fr, fg, fb = _hex_to_rgb01(text_color)
    br, bg_, bb = _hex_to_rgb01(bg_color)

    def paint_bg():
        c.setFillColorRGB(br, bg_, bb)
        c.rect(0, 0, page_w, page_h, stroke=0, fill=1)
        c.setFillColorRGB(fr, fg, fb)

    paint_bg()

    y = page_h - top
    text_obj = c.beginText()
    text_obj.setTextOrigin(left, y)
    text_obj.setLeading(leading)
    text_obj.setCharSpace(char_space)
    text_obj.setFillColorRGB(fr, fg, fb)

    def new_page():
        nonlocal text_obj, y
        c.drawText(text_obj)
        c.showPage()
        paint_bg()
        y = page_h - top
        text_obj = c.beginText()
        text_obj.setTextOrigin(left, y)
        text_obj.setLeading(leading)
        text_obj.setCharSpace(char_space)
        text_obj.setFillColorRGB(fr, fg, fb)

    def ensure_space(lines_needed: int, line_height: int):
        nonlocal y
        if y - (lines_needed * line_height) < bottom:
            new_page()

    for raw_line in text.split("\n"):
        line = raw_line.rstrip()
        if not line.strip():
            ensure_space(1, leading)
            text_obj.textLine("")
            y -= leading
            continue

        is_h1 = line.startswith("# ")
        is_h2 = line.startswith("## ")
        is_bullet = line.startswith("- ") or line.startswith("* ")

        if is_h1:
            content, f, sz = line[2:].strip(), font_heading, int(font_size * 1.4)
        elif is_h2:
            content, f, sz = line[3:].strip(), font_heading, int(font_size * 1.2)
        elif is_bullet:
            content, f, sz = "• " + line[2:].strip(), font_name, font_size
        else:
            content, f, sz = line, font_name, font_size

        ld = max(int(sz * line_spacing_mult), sz + 2)
        text_obj.setFont(f, sz)
        text_obj.setLeading(ld)

        wrapped = _wrap_with_charspace(content, f, sz, usable_w, char_space)
        ensure_space(len(wrapped) + (1 if (is_h1 or is_h2) else 0), ld)
        for wline in wrapped:
            text_obj.textLine(wline)
            y -= ld
        if is_h1 or is_h2:
            text_obj.textLine("")
            y -= ld

    c.drawText(text_obj)
    c.save()
    buffer.seek(0)
    return buffer.read()


# ----------------------------
# Input helpers
# ----------------------------
def _reflow_paragraphs(text: str) -> str:
    """PDF extractors often emit one word (or short fragment) per line, with
    blank lines scattered between them. Reflow so visual line breaks within a
    sentence become spaces, and only sentence-ending punctuation, true gaps,
    or structural markers (headings, bullets) start new paragraphs."""
    if not text:
        return ""

    import re

    # De-hyphenate words split across lines: "warfa-\nrin" -> "warfarin"
    text = re.sub(r"-\n(?=\w)", "", text)

    raw_lines = text.split("\n")

    # Count consecutive blank lines BEFORE each non-empty line, so we can tell
    # "single blank between wrapped lines" (likely same paragraph) apart from
    # "multiple blank lines" (real paragraph break).
    cleaned: list[tuple[str, int]] = []  # (line, blanks_before_it)
    blanks = 0
    for raw in raw_lines:
        s = raw.strip()
        if not s:
            blanks += 1
            continue
        cleaned.append((s, blanks))
        blanks = 0

    def is_structural(line: str) -> bool:
        return line.startswith(("#", "- ", "* "))

    def ends_sentence(line: str) -> bool:
        # Strip trailing closers like quotes/brackets before checking
        stripped = line.rstrip(")]}»\"'”’")
        return bool(stripped) and stripped[-1] in ".!?"

    paragraphs: list[str] = []
    buf: list[str] = []

    def flush():
        if buf:
            paragraphs.append(" ".join(buf))
            buf.clear()

    for i, (line, gap) in enumerate(cleaned):
        if is_structural(line):
            flush()
            paragraphs.append(line)
            continue

        if not buf:
            buf.append(line)
            continue

        prev = buf[-1]
        # Start a new paragraph if:
        #   - the previous line ended a sentence, OR
        #   - there were 2+ blank lines (clear visual break), OR
        #   - the previous line is short and ends with a colon (heading-ish),
        #     while the new line starts with a capital letter
        new_para = (
            ends_sentence(prev)
            or gap >= 2
            or (prev.endswith(":") and line[:1].isupper() and len(prev) < 80)
        )
        if new_para:
            flush()
            buf.append(line)
        else:
            buf.append(line)

    flush()

    # Collapse internal whitespace runs
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in paragraphs if p.strip()]
    return "\n\n".join(paragraphs)


def extract_pdf_text(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n\n"
    return _reflow_paragraphs(text)


# ----------------------------
# AI tool: simplification for dense text
# ----------------------------
def _llm_simplify(text: str, api_key: str) -> str:
    """Extra-dumbed-down version for very dense material."""
    client = OpenAI(api_key=api_key)
    prompt = f"""
You are a "Make It Simple" tool for dyslexic and neurodivergent readers who are
struggling with very dense text.

Rewrite the input so a curious 10-year-old could understand it:
- Use everyday words. Replace jargon with plain language.
- Keep sentences under 12 words when possible.
- One idea per sentence.
- Use bullet points and short headings to break things up.
- Add a one-line "In short:" summary at the very top.
- If something is technical, briefly explain it in parentheses.
- Do NOT lose key facts, names, numbers, or dates.

Output valid Markdown only. No preamble.

Text to simplify:
{text}
""".strip()
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "system", "content": prompt}],
    )
    return resp.choices[0].message.content


# ----------------------------
# Preview rendering
# ----------------------------
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


_READER_JS = r"""
window.addEventListener('error', function(ev) {
  var s = document.getElementById('status');
  if (s) s.textContent = 'JS error: ' + (ev.message || ev.error || 'unknown');
});
(function() {
try {
  const plain = __PLAIN_JSON__;
  const offsets = __OFFSETS_JSON__;
  const spans = Array.from(document.querySelectorAll('.w'));
  const content = document.getElementById('content');
  const playBtn = document.getElementById('play');
  const pauseBtn = document.getElementById('pause');
  const resumeBtn = document.getElementById('resume');
  const stopBtn = document.getElementById('stop');
  const status = document.getElementById('status');
  const rate = document.getElementById('rate');
  const rateVal = document.getElementById('rateVal');
  const voiceSel = document.getElementById('voice');

  let voices = [];
  let chosenVoice = null;
  let activeIdx = -1;
  let sentences = [];
  let queueIdx = 0;
  let currentUtter = null;
  let stopped = false;
  let boundaryFired = false;

  function scoreVoice(v) {
    const n = (v.name || '').toLowerCase();
    let s = 0;
    if (!(v.lang || '').toLowerCase().startsWith('en')) return -1;
    if (n.includes('natural')) s += 50;
    if (n.includes('neural')) s += 50;
    if (n.includes('premium')) s += 40;
    if (n.includes('enhanced')) s += 30;
    if (n.includes('online')) s += 25;
    if (n.includes('google')) s += 20;
    if (n.startsWith('microsoft')) s += 15;
    ['samantha','ava','allison','evan','tom','serena','daniel','karen'].forEach(function(name) {
      if (n.includes(name)) s += 12;
    });
    if (!v.localService) s += 5;
    return s;
  }

  function loadVoices() {
    if (!('speechSynthesis' in window)) return 0;
    voices = (window.speechSynthesis.getVoices() || []).slice();
    const ranked = voices
      .map(function(v, i) { return { v: v, i: i, s: scoreVoice(v) }; })
      .filter(function(x) { return x.s >= 0; })
      .sort(function(a, b) { return b.s - a.s; });
    voiceSel.innerHTML = '';
    ranked.forEach(function(r) {
      const opt = document.createElement('option');
      opt.value = r.i;
      opt.textContent = r.v.name + ' (' + r.v.lang + ')';
      voiceSel.appendChild(opt);
    });
    if (ranked.length) {
      voiceSel.value = ranked[0].i;
      chosenVoice = voices[ranked[0].i];
    }
    return ranked.length;
  }
  voiceSel.onchange = function() { chosenVoice = voices[parseInt(voiceSel.value, 10)] || null; };

  function buildSentences(fromChar) {
    fromChar = Math.max(0, fromChar | 0);
    const out = [];
    let i = fromChar;
    const n = plain.length;
    while (i < n) {
      while (i < n && /\s/.test(plain[i])) i++;
      if (i >= n) break;
      const start = i;
      while (i < n) {
        const c = plain[i];
        if (c === '.' || c === '!' || c === '?') {
          let j = i + 1;
          while (j < n && /[)\]"'\u201d\u2019]/.test(plain[j])) j++;
          if (j >= n || /\s/.test(plain[j])) { i = j; break; }
          i = j;
          continue;
        }
        if (c === '\n' && i + 1 < n && plain[i + 1] === '\n') break;
        i++;
      }
      const end = i;
      const text = plain.slice(start, end).trim();
      if (!text) continue;
      let wordStart = -1, wordEnd = -1;
      for (let k = 0; k < offsets.length; k++) {
        const s = offsets[k][0], l = offsets[k][1];
        if (s + l <= start) continue;
        if (s >= end) break;
        if (wordStart === -1) wordStart = k;
        wordEnd = k;
      }
      if (wordStart === -1) continue;
      out.push({ text: text, charStart: start, wordStart: wordStart, wordEnd: wordEnd });
    }
    return out;
  }

  function clearActive() {
    document.querySelectorAll('.w.active').forEach(function(el) { el.classList.remove('active'); });
    activeIdx = -1;
  }

  function highlightWord(i) {
    if (i < 0 || i >= spans.length || i === activeIdx) return;
    clearActive();
    activeIdx = i;
    const el = spans[i];
    if (!el) return;
    el.classList.add('active');
    const r = el.getBoundingClientRect();
    const cr = content.getBoundingClientRect();
    if (r.top < cr.top + 40 || r.bottom > cr.bottom - 40) {
      el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }

  function highlightSentence(sent) {
    clearActive();
    for (let i = sent.wordStart; i <= sent.wordEnd; i++) {
      if (spans[i]) spans[i].classList.add('active');
    }
    activeIdx = sent.wordStart;
    const el = spans[sent.wordStart];
    if (el) {
      const r = el.getBoundingClientRect();
      const cr = content.getBoundingClientRect();
      if (r.top < cr.top + 40 || r.bottom > cr.bottom - 40) {
        el.scrollIntoView({ block: 'center', behavior: 'smooth' });
      }
    }
  }

  function charToWordInSentence(sent, localChar) {
    const absChar = sent.charStart + localChar;
    for (let i = sent.wordStart; i <= sent.wordEnd; i++) {
      const s = offsets[i][0], l = offsets[i][1];
      if (absChar < s + l) return i;
    }
    return sent.wordEnd;
  }

  function setButtons(state) {
    const playing = state.playing, paused = state.paused;
    playBtn.disabled = playing && !paused;
    pauseBtn.disabled = !(playing && !paused);
    resumeBtn.disabled = !paused;
    stopBtn.disabled = !playing;
  }

  function speakNext() {
    if (stopped || queueIdx >= sentences.length) {
      status.textContent = stopped ? 'Stopped' : 'Done';
      setButtons({ playing: false, paused: false });
      clearActive();
      return;
    }
    const sent = sentences[queueIdx];
    const u = new SpeechSynthesisUtterance(sent.text);
    u.rate = parseFloat(rate.value);
    u.pitch = 1.0;
    u.volume = 1.0;
    if (chosenVoice) u.voice = chosenVoice;
    boundaryFired = false;

    u.onstart = function() {
      status.textContent = 'Reading sentence ' + (queueIdx + 1) + ' / ' + sentences.length;
      setButtons({ playing: true, paused: false });
      highlightSentence(sent);
    };
    u.onboundary = function(e) {
      if (!(e.name === 'word' || e.charIndex != null)) return;
      if (!boundaryFired) { boundaryFired = true; clearActive(); }
      const wIdx = charToWordInSentence(sent, e.charIndex || 0);
      highlightWord(wIdx);
    };
    u.onend = function() {
      if (stopped) return;
      queueIdx++;
      speakNext();
    };
    u.onerror = function(e) {
      status.textContent = 'Speech error: ' + (e.error || 'unknown') + ' (sentence ' + (queueIdx + 1) + ')';
      queueIdx++;
      speakNext();
    };
    currentUtter = u;
    try {
      window.speechSynthesis.speak(u);
    } catch (err) {
      status.textContent = 'speak() threw: ' + (err && err.message ? err.message : err);
    }
    setTimeout(function() {
      if (currentUtter === u && !window.speechSynthesis.speaking && !window.speechSynthesis.pending) {
        status.textContent = 'No audio after 2s. pending=' + window.speechSynthesis.pending + ' speaking=' + window.speechSynthesis.speaking + ' voices=' + voices.length + ' chosen=' + (chosenVoice ? chosenVoice.name : 'none');
      }
    }, 2000);
  }

  function startSpeaking(fromCharIndex) {
    if (!('speechSynthesis' in window)) {
      status.textContent = 'Speech not supported in this browser';
      return;
    }
    if (!voices.length) loadVoices();
    window.speechSynthesis.cancel();
    clearActive();
    stopped = false;
    sentences = buildSentences(fromCharIndex || 0);
    queueIdx = 0;
    if (!sentences.length) {
      status.textContent = 'Nothing to read (text is empty)';
      return;
    }
    status.textContent = 'Starting…';
    setButtons({ playing: true, paused: false });
    speakNext();
  }

  playBtn.onclick = function() { startSpeaking(0); };
  pauseBtn.onclick = function() {
    if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
      window.speechSynthesis.pause();
      status.textContent = 'Paused';
      setButtons({ playing: true, paused: true });
    }
  };
  resumeBtn.onclick = function() {
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      status.textContent = 'Reading...';
      setButtons({ playing: true, paused: false });
    }
  };
  stopBtn.onclick = function() {
    stopped = true;
    window.speechSynthesis.cancel();
    clearActive();
    status.textContent = 'Stopped';
    setButtons({ playing: false, paused: false });
  };
  rate.oninput = function() {
    rateVal.textContent = parseFloat(rate.value).toFixed(2) + '×';
  };

  spans.forEach(function(el, i) {
    el.style.cursor = 'pointer';
    el.title = 'Click to read from here. Shift+click for definition.';
    el.addEventListener('click', function(e) {
      if (e.shiftKey) return;
      startSpeaking(offsets[i][0]);
    });
  });

  if ('speechSynthesis' in window) {
    if (!loadVoices()) {
      let tries = 0;
      const t = setInterval(function() {
        tries++;
        if (loadVoices() || tries > 20) clearInterval(t);
      }, 250);
    }
    window.speechSynthesis.onvoiceschanged = loadVoices;
  } else {
    status.textContent = 'Speech not supported in this browser';
    playBtn.disabled = true;
  }

  // -------- Focus mode --------
  const focusTog = document.getElementById('focusTog');
  if (focusTog) {
    focusTog.addEventListener('change', function() {
      content.classList.toggle('focus', focusTog.checked);
    });
  }

  // -------- Bionic reading --------
  // Bolds the first ~40% of each word's letters.
  const bionicTog = document.getElementById('bionicTog');
  function applyBionic(on) {
    spans.forEach(function(el) {
      const txt = el.getAttribute('data-orig') || el.textContent;
      el.setAttribute('data-orig', txt);
      if (on) {
        const letters = txt.match(/^[A-Za-z\u00C0-\u024F'’-]+/);
        if (letters && letters[0].length > 1) {
          const headLen = Math.max(1, Math.ceil(letters[0].length * 0.4));
          const head = txt.slice(0, headLen);
          const tail = txt.slice(headLen);
          el.innerHTML = '<span class="bionic">' + head + '</span>' + tail;
        } else {
          el.textContent = txt;
        }
      } else {
        el.textContent = txt;
      }
    });
  }
  if (bionicTog) {
    bionicTog.addEventListener('change', function() { applyBionic(bionicTog.checked); });
  }

  // -------- Definition popover (shift+click a word) --------
  const defPop = document.getElementById('defPop');
  const defBody = document.getElementById('defBody');
  const defClose = document.getElementById('defClose');
  const defCache = {};
  function hideDef() { if (defPop) defPop.style.display = 'none'; }
  if (defClose) defClose.addEventListener('click', hideDef);
  document.addEventListener('click', function(e) {
    if (defPop && !defPop.contains(e.target) && !e.target.classList.contains('w')) hideDef();
  });
  function showDef(html, x, y) {
    if (!defPop) return;
    defBody.innerHTML = html;
    defPop.style.display = 'block';
    // Clamp inside viewport
    const w = defPop.offsetWidth, h = defPop.offsetHeight;
    const maxX = window.innerWidth - w - 10;
    const maxY = window.innerHeight - h - 10;
    defPop.style.left = Math.max(10, Math.min(x, maxX)) + 'px';
    defPop.style.top = Math.max(10, Math.min(y, maxY)) + 'px';
  }
  function lookupWord(raw, x, y) {
    const word = (raw || '').toLowerCase().replace(/[^a-z'’-]/g, '');
    if (!word) return;
    showDef('<span class="word">' + word + '</span><div class="def">Looking up…</div>', x, y);
    if (defCache[word]) { showDef(defCache[word], x, y); return; }
    fetch('https://api.dictionaryapi.dev/api/v2/entries/en/' + encodeURIComponent(word))
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(data) {
        if (!data || !data.length) {
          const html = '<span class="word">' + word + '</span><div class="def">No definition found.</div>';
          defCache[word] = html;
          showDef(html, x, y);
          return;
        }
        const entry = data[0];
        const meanings = (entry.meanings || []).slice(0, 2);
        let html = '<span class="word">' + word + '</span>';
        meanings.forEach(function(m) {
          const def = (m.definitions && m.definitions[0] && m.definitions[0].definition) || '';
          if (def) {
            html += '<div class="def"><span class="pos">' + (m.partOfSpeech || '') + '</span> ' + def + '</div>';
          }
        });
        defCache[word] = html;
        showDef(html, x, y);
      })
      .catch(function() {
        showDef('<span class="word">' + word + '</span><div class="def">Could not load definition.</div>', x, y);
      });
  }
  // Wire shift-click on all words
  spans.forEach(function(el) {
    el.addEventListener('click', function(e) {
      if (e.shiftKey) {
        e.preventDefault();
        e.stopPropagation();
        const txt = el.getAttribute('data-orig') || el.textContent;
        lookupWord(txt, e.pageX + 10, e.pageY + 10);
      }
    }, true);
  });

} catch (err) {
  var s = document.getElementById('status');
  if (s) s.textContent = 'Init error: ' + (err && err.message ? err.message : err);
}
})();
"""


def render_reader(markdown_text: str, prefs: dict, key: str = "reader"):
    """Styled preview with built-in TTS: play, pause, resume, stop, word highlight."""
    safe = html.escape(markdown_text)
    lines = safe.split("\n")

    # Build HTML. Each non-markup word gets wrapped in <span class="w" data-i="...">
    # so we can highlight it during TTS via the SpeechSynthesisUtterance boundary
    # event. We also build a parallel plain-text string and a list of (start,len)
    # offsets per word so JS can map charIndex -> word index.
    plain_words: list[str] = []
    word_offsets: list[tuple[int, int]] = []  # (start_in_plain, length)
    plain_buf: list[str] = []
    plain_len = 0

    def add_word(token: str) -> str:
        nonlocal plain_len
        start = plain_len
        plain_words.append(token)
        word_offsets.append((start, len(token)))
        plain_buf.append(token)
        plain_len += len(token)
        idx = len(plain_words) - 1
        return f'<span class="w" data-i="{idx}">{token}</span>'

    def add_gap(gap: str):
        nonlocal plain_len
        plain_buf.append(gap)
        plain_len += len(gap)

    def tokenize_line(text_line: str) -> str:
        out = []
        i = 0
        while i < len(text_line):
            ch = text_line[i]
            if ch.isspace():
                j = i
                while j < len(text_line) and text_line[j].isspace():
                    j += 1
                add_gap(" ")
                out.append(" ")
                i = j
            else:
                j = i
                while j < len(text_line) and not text_line[j].isspace():
                    j += 1
                out.append(add_word(text_line[i:j]))
                i = j
        return "".join(out)

    html_parts: list[str] = []
    in_ul = False
    for ln in lines:
        s = ln.rstrip()
        if not s.strip():
            if in_ul:
                html_parts.append("</ul>"); in_ul = False
            html_parts.append("<p></p>")
            add_gap("\n")
            continue
        if s.startswith("# "):
            if in_ul:
                html_parts.append("</ul>"); in_ul = False
            html_parts.append("<h2>" + tokenize_line(s[2:].strip()) + "</h2>")
            add_gap("\n")
        elif s.startswith("## "):
            if in_ul:
                html_parts.append("</ul>"); in_ul = False
            html_parts.append("<h3>" + tokenize_line(s[3:].strip()) + "</h3>")
            add_gap("\n")
        elif s.startswith("- ") or s.startswith("* "):
            if not in_ul:
                html_parts.append("<ul>"); in_ul = True
            html_parts.append("<li>" + tokenize_line(s[2:].strip()) + "</li>")
            add_gap("\n")
        else:
            if in_ul:
                html_parts.append("</ul>"); in_ul = False
            html_parts.append("<p>" + tokenize_line(s) + "</p>")
            add_gap("\n")
    if in_ul:
        html_parts.append("</ul>")

    body = "\n".join(html_parts)
    plain_text = "".join(plain_buf)
    family = prefs["font_family"]
    css_family = _FONT_CSS_STACK.get(family, f"'{family}', sans-serif")

    word_offsets_json = json.dumps(word_offsets)
    plain_json = json.dumps(plain_text)

    script_js = (
        _READER_JS
        .replace("__PLAIN_JSON__", plain_json)
        .replace("__OFFSETS_JSON__", word_offsets_json)
    )

    component_html = f"""
<!doctype html>
<html><head><meta charset="utf-8"><style>
  body {{ margin: 0; }}
  .toolbar {{
    display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
    padding: 8px 12px; background: #1f1f24; color: #fff;
    font-family: system-ui, sans-serif; border-radius: 10px 10px 0 0;
    position: sticky; top: 0; z-index: 5;
  }}
  .toolbar button {{
    background: #6b46c1; color: white; border: 0; padding: 8px 12px;
    border-radius: 8px; cursor: pointer; font-size: 14px;
  }}
  .toolbar button:hover {{ background: #7c5ad3; }}
  .toolbar button:disabled {{ background: #444; cursor: not-allowed; }}
  .toolbar .meta {{ margin-left: auto; opacity: 0.85; font-size: 13px; }}
  .toolbar label {{ font-size: 13px; opacity: 0.9; }}
  .toolbar input[type=range] {{ width: 120px; }}
  .decoda-preview {{
    background: {prefs['background_color']};
    color: {prefs['text_color']};
    font-family: {css_family};
    font-size: {prefs['font_size']}px;
    line-height: {prefs['line_spacing']};
    letter-spacing: {prefs['letter_spacing']}em;
    word-spacing: {prefs['word_spacing']}em;
    padding: 24px;
    border-radius: 0 0 12px 12px;
    max-height: 70vh;
    overflow-y: auto;
  }}
  .decoda-preview h2 {{ font-size: {int(prefs['font_size']*1.4)}px; margin: 0.6em 0 0.3em; }}
  .decoda-preview h3 {{ font-size: {int(prefs['font_size']*1.2)}px; margin: 0.6em 0 0.3em; }}
  .decoda-preview p {{ margin: 0.4em 0; }}
  .decoda-preview ul {{ margin: 0.4em 0 0.6em 1.2em; }}
  .w.active {{
    background: #ffe066;
    color: #1a1a1a;
    border-radius: 3px;
  }}
  /* Focus mode: dim everything except the active sentence words. */
  .decoda-preview.focus .w:not(.active) {{ opacity: 0.28; }}
  .decoda-preview.focus .w {{ transition: opacity 0.2s; }}
  /* Bionic reading: bold the leading characters of each word. */
  .w .bionic {{ font-weight: 800; }}
  /* Definition popover */
  #defPop {{
    position: absolute; max-width: 320px; z-index: 1000;
    background: #1f1f24; color: #fff; border-radius: 8px;
    padding: 10px 12px; font-family: system-ui, sans-serif;
    font-size: 13px; line-height: 1.4; box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    display: none;
  }}
  #defPop .word {{ font-weight: 700; color: #b388ff; font-size: 14px; }}
  #defPop .pos {{ font-style: italic; opacity: 0.75; margin-left: 6px; }}
  #defPop .def {{ margin-top: 4px; }}
  #defPop .close {{ float: right; cursor: pointer; opacity: 0.6; }}
  .w {{ cursor: pointer; }}
  .w:hover {{ text-decoration: underline; text-decoration-color: rgba(107,70,193,0.5); }}
</style></head><body>
  <div class="toolbar">
    <button id="play">▶ Play</button>
    <button id="pause" disabled>⏸ Pause</button>
    <button id="resume" disabled>⏵ Resume</button>
    <button id="stop" disabled>⏹ Stop</button>
    <label>Voice
      <select id="voice" style="max-width: 220px;"></select>
    </label>
    <label>Speed
      <input id="rate" type="range" min="0.6" max="1.6" step="0.05" value="1.0">
      <span id="rateVal">1.0×</span>
    </label>
    <label><input type="checkbox" id="focusTog"> Focus</label>
    <label><input type="checkbox" id="bionicTog"> Bionic</label>
    <span class="meta" id="status">Ready</span>
  </div>
  <div class="decoda-preview" id="content">{body}</div>
  <div id="defPop"><span class="close" id="defClose">✕</span><div id="defBody">Loading…</div></div>

<script>{script_js}</script>
</body></html>
"""
    components.html(component_html, height=720, scrolling=False)


# Back-compat alias (other modules may still call render_preview)
render_preview = render_reader


# ----------------------------
# Main app
# ----------------------------
def app():
    st.title(":violet[Decoder Tool]")

    uid = st.session_state.get("username", "")

    # Load preferences from Firebase (cached on session for editing)
    if "prefs" not in st.session_state:
        st.session_state.prefs = user_data.load_preferences(uid)
    prefs = st.session_state.prefs

    user_data.apply_reading_theme(prefs)

    # --- Reading style controls ---
    with st.expander("Reading style", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            prefs["text_color"] = st.color_picker("Text color", prefs["text_color"])
            prefs["background_color"] = st.color_picker("Background", prefs["background_color"])
        with c2:
            font_options = list(dict.fromkeys(AVAILABLE_FONTS + ["Arial", "Verdana", "Comic Sans MS"]))
            current_family = prefs["font_family"] if prefs["font_family"] in font_options else font_options[0]
            prefs["font_family"] = st.selectbox(
                "Font", font_options, index=font_options.index(current_family)
            )
            prefs["font_size"] = st.slider("Font size (px)", 12, 36, int(prefs["font_size"]))
        with c3:
            prefs["line_spacing"] = st.slider("Line spacing", 1.0, 3.0, float(prefs["line_spacing"]), 0.1)
            prefs["letter_spacing"] = st.slider("Letter spacing (em)", 0.0, 0.3, float(prefs["letter_spacing"]), 0.01)
            prefs["word_spacing"] = st.slider("Word spacing (em)", 0.0, 1.0, float(prefs["word_spacing"]), 0.05)

        cols = st.columns([1, 1, 3])
        with cols[0]:
            if st.button("Save settings", use_container_width=True):
                user_data.save_preferences(uid, prefs)
                st.success("Settings saved to your account.")
        with cols[1]:
            if st.button("Reset", use_container_width=True):
                st.session_state.prefs = dict(user_data.DEFAULT_PREFS)
                st.rerun()

    st.session_state.prefs = prefs

    # --- Input ---
    st.subheader("Your text")
    mode = st.radio("Input method", ["Upload PDF", "Paste text", "Try a sample"], horizontal=True)

    source_text = ""
    source_label = ""
    if mode == "Upload PDF":
        uploaded = st.file_uploader("Upload a PDF", type=["pdf"], accept_multiple_files=False)
        if uploaded is not None:
            source_text = extract_pdf_text(uploaded)
            source_label = f"pdf:{uploaded.name}"
            if not source_text.strip():
                st.warning("No text could be extracted (the PDF may be scanned images).")
    elif mode == "Paste text":
        pasted = st.text_area("Paste text here", height=220, key="pasted_text")
        source_text = _reflow_paragraphs(pasted or "")
        source_label = "paste"
    else:
        import samples
        sc1, sc2 = st.columns(2)
        with sc1:
            band = st.selectbox("Grade band", samples.grade_bands(), key="sample_band")
        with sc2:
            title = st.selectbox("Passage", samples.titles_for(band), key="sample_title")
        source_text = samples.get_sample(band, title)
        source_label = f"sample:{band}:{title}"
        with st.expander("Preview the sample", expanded=False):
            st.write(source_text)

    if not source_text.strip():
        st.info("Add text to start.")
        return

    # Reset cached simplified output if the source changed
    if st.session_state.get("source_text_cache") != source_text:
        st.session_state.source_text_cache = source_text
        st.session_state.simplified_text = ""

    max_chars = 20000
    if len(source_text) > max_chars:
        st.caption(
            f"Heads up: this text is {len(source_text):,} characters. "
            f"AI simplification will only use the first {max_chars:,}."
        )

    # --- AI tool: optional simplification for dense text ---
    b1, b2 = st.columns(2)
    with b1:
        simplify_clicked = st.button(
            "Make it simple (AI tool for dense text)",
            type="primary",
            use_container_width=True,
        )
    with b2:
        if st.session_state.get("simplified_text"):
            if st.button("Show original instead", use_container_width=True):
                st.session_state.simplified_text = ""
                st.rerun()

    if simplify_clicked:
        truncated = source_text[:max_chars]
        with st.spinner("Simplifying..."):
            simplified = _llm_simplify(truncated, API_KEY)
        st.session_state.simplified_text = simplified
        user_data.save_decode(
            uid, source=source_label, mode="simplify",
            input_text=source_text, output_text=simplified,
        )

    # The "decoded" output is just the original text reformatted with the user's
    # reading style. The AI only runs when the user asks for simplification.
    is_simplified = bool(st.session_state.get("simplified_text"))
    output = st.session_state.simplified_text if is_simplified else source_text
    st.session_state.decoded_text = output  # used by Text-to-Speech page

    st.markdown("### Read along" + (" (simplified)" if is_simplified else ""))
    st.caption("Tip: click any word to read from there · **Shift+click** a word for a quick definition · use **Focus** to dim other text · use **Bionic** to bold the start of each word.")
    render_reader(output, prefs, key="decoder_reader")

    pdf_bytes = text_to_pdf_bytes(
        output,
        font_family=prefs["font_family"],
        text_color=prefs["text_color"],
        bg_color=prefs["background_color"],
        font_size=max(11, min(int(prefs["font_size"] * 0.75), 22)),
        line_spacing_mult=float(prefs["line_spacing"]),
        char_space=float(prefs["letter_spacing"]) * 10,
    )
    st.download_button(
        label=":violet[Download Decoded PDF]",
        data=pdf_bytes,
        file_name="decoded_dyslexia_friendly.pdf",
        mime="application/pdf",
    )
