"""
app.py  —  Gemma Without Borders (student-facing quiz + AI study guide).

Run it:   streamlit run app.py

Flow:  take a short quiz  ->  submit  ->  score + a personalized study guide the
AGENT builds from your wrong answers (explanation + fresh practice per mistake),
plus the agent's read on your #1 trick and a parent hand-off if needed.
"""
import json
import re
from html import escape as _hescape
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

import agent
import mastery as m
import tutor
import rewards
from gemma_client import plainify

QUESTIONS = json.loads((Path(__file__).parent / "data" / "questions.json").read_text())
STRANDS = sorted({q["strand"] for q in QUESTIONS})

# GEMMA MONSTERS is the front door; the classic dashboard is one click away
if "stage" not in st.session_state:
    st.session_state.adventure = True
    st.session_state.stage = "map"

st.set_page_config(
    page_title="GEMMA MONSTERS",
    layout="centered")

_GAME_SKIN = """
<style>
:root { --ink:#f2e8dc; --muted:#b9a794; --line:#3a2a35; --card:#160e18; --accent:#e08d6d; }
html, body, [class*="css"], p, li, label, span, div, button, input {
  font-family:'Trebuchet MS','Segoe UI',sans-serif;
}
[data-testid="stAppViewContainer"]{
  background:radial-gradient(70% 45% at 50% 0%, #1c1019 0%, #0b0710 55%) #0b0710 !important}
[data-testid="stHeader"]{background:transparent !important}
html,body,p,li,label,span,div{color:var(--ink)}
h1,h2,h3{
  font-weight:900 !important; text-transform:uppercase; letter-spacing:-0.5px;
  background:linear-gradient(135deg,#ffe9d6 25%,#e08d6d 70%,#b98868);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  filter:drop-shadow(0 0 12px rgba(224,141,109,.4));
}
.stCaption,[data-testid="stCaptionContainer"]{color:var(--muted) !important;
  letter-spacing:.06em}
.stButton button, .stDownloadButton button{
  border-radius:24px;border:1px solid rgba(255,240,225,.16);
  background:rgba(255,240,225,.06);color:#d9c6b2;font-weight:700;
  text-transform:uppercase;letter-spacing:.08em;font-size:.8rem;box-shadow:none}
.stButton button:hover{background:rgba(255,240,225,.15);color:#fff;
  border-color:rgba(255,240,225,.3)}
.stButton button[kind="primary"]{
  background:linear-gradient(135deg,#e08d6d,#a8434f);border:none;color:#1a0f14;
  border-radius:10px;font-weight:900;letter-spacing:.12em;
  box-shadow:0 8px 24px rgba(224,141,109,.45)}
.stButton button[kind="primary"]:hover{transform:translateY(-1px);color:#0b0710}
[data-testid="stVerticalBlockBorderWrapper"]{
  background:linear-gradient(160deg,#1c1119,#160e18);
  border:1px solid rgba(255,236,214,.12) !important;border-radius:14px;
  box-shadow:0 14px 34px rgba(0,0,0,.5), 0 0 22px rgba(224,141,109,.08)}
[data-testid="stExpander"]{border:1px solid rgba(255,236,214,.12);border-radius:10px;
  background:var(--card)}
[data-testid="stExpander"] summary{color:#d9c6b2;text-transform:uppercase;
  font-size:.78rem;letter-spacing:.1em;font-weight:700}
[data-testid="stMetricValue"]{
  font-weight:900;
  background:linear-gradient(135deg,#ffe9d6,#e08d6d);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}
[data-testid="stMetricLabel"] p{text-transform:uppercase;letter-spacing:.14em;
  font-size:.68rem;color:var(--muted) !important}
hr{border-color:var(--line) !important}
/* answer options as selectable game chips */
.stRadio > div{gap:6px}
.stRadio label{
  background:#1c1119;border:1px solid rgba(255,236,214,.12);border-radius:10px;
  padding:9px 14px;margin:0;width:100%;transition:border-color .15s, box-shadow .15s}
.stRadio label:hover{border-color:#e08d6d;box-shadow:0 0 14px rgba(224,141,109,.25)}
.stRadio label p,.stRadio label{color:#f2e8dc !important}
[data-testid="stWidgetLabel"] p{color:#d9c6b2 !important}
.stProgress > div > div > div{background:linear-gradient(90deg,#e08d6d,#ffd166) !important;
  box-shadow:0 0 12px rgba(224,141,109,.5)}
.stTextInput input{background:#1c1119;color:#f2e8dc;border:1px solid var(--line);
  border-radius:10px}
[data-testid="stFileUploaderDropzone"]{background:#1c1119;border:1px dashed var(--line)}
code, pre{background:#1c1119 !important;color:#ffd9b8 !important}
.gwb-note{border:1px solid rgba(255,236,214,.12);border-left:3px solid var(--accent);
  border-radius:10px;background:linear-gradient(160deg,#1c1119,#160e18);
  padding:.85rem 1.1rem;margin:.4rem 0 .9rem;color:var(--ink);
  box-shadow:0 0 18px rgba(224,141,109,.14)}
.gwb-note .label{display:block;font-size:.68rem;letter-spacing:.16em;
  text-transform:uppercase;color:var(--accent);margin-bottom:.3rem;font-weight:900}
.gwb-kicker{font-size:.72rem;letter-spacing:.18em;text-transform:uppercase;
  color:var(--accent);margin-bottom:.2rem;font-weight:900}
.katex{color:#ffefdd}
/* selects and their dropdown menus: dark, readable */
[data-baseweb="select"] > div{background:#1c1119 !important;border-color:#3a2a35 !important}
[data-baseweb="select"] div, [data-baseweb="select"] span, [data-baseweb="select"] input{color:#f2e8dc !important}
[data-baseweb="select"] svg{fill:#e08d6d !important}
[data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] ul, [data-baseweb="menu"]{
  background:#1c1119 !important;border:1px solid #3a2a35 !important}
[data-baseweb="popover"] [role="option"], [data-baseweb="popover"] li, [data-baseweb="menu"] li{
  color:#f2e8dc !important;background:#1c1119 !important}
[data-baseweb="popover"] [role="option"]:hover, [data-baseweb="popover"] li:hover,
[data-baseweb="menu"] li:hover, [data-baseweb="popover"] li[aria-selected="true"]{
  background:#2a1a26 !important;color:#ffefdd !important}
.gwb-taunt{position:fixed;bottom:20px;right:20px;z-index:999;display:flex;
  align-items:flex-end;gap:10px;animation:gwbBob 3.2s ease-in-out infinite}
.gwb-bubble{background:#1c1119;border:1px solid #e08d6d;
  border-radius:14px 14px 2px 14px;padding:9px 13px;color:#f2e8dc;font-size:.82rem;
  max-width:210px;box-shadow:0 0 16px rgba(224,141,109,.35)}
.gwb-tmon{filter:drop-shadow(0 0 12px rgba(224,141,109,.5));
  animation:gwbSway 2.6s ease-in-out infinite}
@keyframes gwbBob{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}
@keyframes gwbSway{0%,100%{transform:rotate(-3deg)}50%{transform:rotate(3deg)}}
</style>
"""

# ---- one identity everywhere: the GEMMA MONSTERS skin (looks only, no logic) ----
st.markdown(_GAME_SKIN, unsafe_allow_html=True)


def _inline_md(s: str) -> str:
    """Render **bold** / *italic* as HTML inside our note boxes (raw HTML doesn't
    process markdown). The italic rule ignores '2 * 3' (asterisks hugging text
    only), so multiplication is never mistaken for emphasis."""
    s = re.sub(r"\*\*(\S(?:.*?\S)?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*(?!\s)([^*]+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", s)
    return s


def note(label: str, body: str):
    st.markdown(
        f'<div class="gwb-note"><span class="label">{label}</span>{_inline_md(body)}</div>',
        unsafe_allow_html=True,
    )


_FRAC = re.compile(r"(?<![\w.$])(\d+)\s*/\s*(\d+)(?![\w.])")
_SUPD = str.maketrans("0123456789", "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079")
_POW = re.compile(r"\b(\d+|[a-wyzA-Z])\s+to\s+the\s+power\s+(?:of\s+)?(negative\s+)?(\d+)\b", re.I)
_SQ = re.compile(r"\b(\d+|[a-wyzA-Z])\s+squared\b", re.I)
_CU = re.compile(r"\b(\d+|[a-wyzA-Z])\s+cubed\b", re.I)


def esc_note(text) -> str:
    """esc() for note boxes. Notes are raw HTML, so markdown/KaTeX never runs
    there: keep fractions plain (3/7), convert wordy powers to unicode, and
    HTML-escape the rest so model output can never break the box."""
    t = plainify(str(text))
    t = _POW.sub(lambda m: m.group(1) + ("⁻" if m.group(2) else "")
                 + m.group(3).translate(_SUPD), t)
    t = _SQ.sub(lambda m: m.group(1) + "²", t)
    t = _CU.sub(lambda m: m.group(1) + "³", t)
    return _hescape(t, quote=False)


_STEP_SPLIT = re.compile(r"(?<=[.;])\s+(?=[A-Z(√\d])")


def steps_md(text) -> str:
    """Render a worked solution as numbered steps instead of one dense
    paragraph. Splits on sentence boundaries (decimals are safe: a digit
    after '. ' only splits when it starts a new sentence-like chunk)."""
    t = esc(plainify(str(text)))
    parts = [p.strip() for p in _STEP_SPLIT.split(t) if p.strip()]
    if len(parts) <= 1:
        return t
    return "\n".join(f"{i}. {p}" for i, p in enumerate(parts, 1))


def esc(text) -> str:
    """Prepare text for display: (1) escape currency '$' so $3.60 shows literally
    instead of the run between two '$' rendering as LaTeX; (2) turn plain integer
    fractions like 3/7 into proper stacked fractions via KaTeX. Decimals and
    money (3.60 / 1.5, $3.60) are left alone by the fraction rule."""
    t = str(text).replace("$", "\\$")                 # currency first
    t = _POW.sub(lambda m: m.group(1) + ("\u207b" if m.group(2) else "")
                 + m.group(3).translate(_SUPD), t)   # 2 to the power 6 -> 2\u2076
    t = _SQ.sub(lambda m: m.group(1) + "\u00b2", t)
    t = _CU.sub(lambda m: m.group(1) + "\u00b3", t)
    t = _FRAC.sub(r"$\\frac{\1}{\2}$", t)             # 3/7 -> stacked fraction
    return t


def pick_quiz(strand: str, n: int) -> list:
    pool = QUESTIONS if strand == "Mixed" else [q for q in QUESTIONS if q["strand"] == strand]
    return pool[:n]


def reset():
    for k in ("stage", "quiz", "answers", "guides", "mastered", "teacher_report",
              "escal_report", "msession", "mprobe", "mlesson", "mlesson_why",
              "mfeedback", "mtranscript"):
        st.session_state.pop(k, None)


def start_mastery(result, analysis):
    """Enter the autonomous practice loop, targeting the priority trick."""
    pid = analysis["priority"]["id"]
    seed = next(w for w in result["wrong"]
                if w["trick"] and w["trick"].get("id") == pid)
    s = m.MasterySession(
        trick_id=pid,
        trick_name=analysis["priority"]["name"],
        strand=seed["item"]["strand"],
        seed_question=seed["item"]["question"],
        seed_solution=seed["item"].get("solution", ""),
        used_item_ids=[q["id"] for q in st.session_state.quiz],
    )
    st.session_state.msession = s
    with st.spinner("The agent is preparing your first lesson..."):
        st.session_state.mlesson = m.teach(s)
        st.session_state.mprobe = m.next_probe(s, QUESTIONS)
    st.session_state.mlesson_why = ("Starting with the most direct explanation of the "
                                    "mistake — the quickest path to seeing it.")
    st.session_state.mfeedback = None
    st.session_state.stage = "mastery"


# ---------------- INTRO ----------------
def intro():
    st.markdown('<div class="gwb-kicker">Grade 9 EQAO Mathematics · Simple mode</div>', unsafe_allow_html=True)
    st.title("GEMMA MONSTERS")
    st.caption("Simple mode — same brain, no monsters underfoot. Runs privately on device.")
    st.write(
        "Take a short quiz. When you submit, the agent identifies why you missed "
        "what you missed, teaches each gap, and gives you a fresh question to "
        "confirm you understand."
    )
    col1, col2 = st.columns(2)
    strand = col1.selectbox("Topic", ["Mixed"] + STRANDS)
    n = col2.slider("Questions", 3, 8, 5)
    if st.button("Start quiz"):
        st.session_state.stage = "quiz"
        st.session_state.quiz = pick_quiz(strand, n)
        st.session_state.answers = {}
        st.rerun()

    st.divider()
    st.caption("Rather play than scroll?")
    if st.button("Back to GEMMA Monsters", type="primary"):
        st.session_state.adventure = True
        st.session_state.stage = "map"
        st.rerun()


# ---------------- GEMMA MONSTERS (optional, additive game layer) ----------------
# Every unit is guarded by a Gemma Monster — a personified trick. The hub
# is a 3D nexus (three.js, bloom). Clicking a monster shows its game card; Begin
# enters that unit's real quiz via ?station=. Deliberately NOT the app's clean
# design language — it's a different world.
MONSTERS = {
    "Number": {
        "monster": "Fractis", "taunt": "Ready to watch you crumble like a bad fraction.", "lines": ["So... {name}. You found my shard field.", "Braver visitors than you have left here counting on their fingers, {name}.", "Show me your fractions - or become part of my collection.", "And {name}... fail too often in the training grounds, and HE notices. Even I go quiet when the Collector passes."], "clip_ambient": "CharacterArmature|Idle", "clip_fight": "CharacterArmature|Bite_Front", "sp_ambient": 0.8, "sp_fight": 0.65, "ns": 0.9, "color": "#ff8a5c", "shape": "shard", "model": "/app/static/monsters/alien.glb",
        "lore": "Feeds on fractions added straight across. Weak to common denominators."},
    "Algebra": {
        "monster": "Equazor", "taunt": "I am ready to watch you lose this battle. Your signs will slip.", "lines": ["Well, well. {name} dares to balance equations with ME watching.", "One slipped sign, {name}, and your answers belong to me.", "I hope you brought more than luck, kid.", "A warning, free of charge: keep failing, and the Collector comes. I don't share my prey with him willingly."], "clip_ambient": "CharacterArmature|Flying_Idle", "clip_fight": "CharacterArmature|Punch", "sp_ambient": 0.9, "sp_fight": 0.7, "ns": 1.0, "color": "#ff6b9d", "shape": "knot", "model": "/app/static/monsters/dragon.glb",
        "lore": "Twists equations until the signs flip wrong. Weak to balanced moves."},
    "Data": {
        "monster": "Statiq", "taunt": "Your answers will drown in my noise.", "lines": ["Splash... {name}, was it? The data here gets... murky.", "Means, medians - it all blurs together down here, {name}.", "Let's see if you can keep your numbers in order. I doubt it.", "Psst... {name}. Lose too often and the water goes cold. That means HE is near. The Collector."], "clip_ambient": "CharacterArmature|Idle", "clip_fight": "CharacterArmature|Punch", "sp_ambient": 0.8, "sp_fight": 0.7, "ns": 1.0, "color": "#35d0c0", "shape": "blob", "model": "/app/static/monsters/fish.glb",
        "lore": "Blurs means and medians into noise. Weak to ordered data."},
    "Geometry & Measurement": {
        "monster": "Polygor", "taunt": "Every angle you pick will be the wrong one, little hero.", "lines": ["Hop hop, {name}. Welcome to my angle hoard.", "Every formula in here is ALMOST right. That's how I catch clever ones like you.", "Draw your diagrams carefully, kid. I feast on sloppy sketches.", "Careful, though. Fail too much and you'll meet something older than me. We call him the Collector. We don't joke about him."], "clip_ambient": "CharacterArmature|Idle", "clip_fight": "CharacterArmature|Punch", "sp_ambient": 0.8, "sp_fight": 0.7, "ns": 1.0, "color": "#a78bfa", "shape": "poly", "model": "/app/static/monsters/frog.glb",
        "lore": "Hoards angles and stolen area formulas. Weak to a true diagram."},
    "Financial Literacy": {
        "monster": "Ledgerling", "taunt": "I collect mistakes - and I charge interest.", "lines": ["Ah, a new account. Name: {name}. Balance: doubtful.", "I skim a little interest off every mistake, {name}. Business is booming.", "Check the math or sign it all away. Your move, kid.", "Oh - and if your debts pile too high, my boss collects them personally. You do NOT want that meeting, {name}."], "clip_ambient": "CharacterArmature|Flying_Idle", "clip_fight": "CharacterArmature|Headbutt", "sp_ambient": 0.9, "sp_fight": 0.7, "ns": 1.0, "color": "#ffd166", "shape": "coin", "model": "/app/static/monsters/demon.glb",
        "lore": "Skims your interest while you sleep. Weak to a sharp budget."},
}
STATIONS = MONSTERS  # router alias: ?station= keys


def monster_for(trick_strand):
    return MONSTERS.get(trick_strand)


def monster_svg(color, size):
    """Tiny original monster mark (blob + eyes) used in the 2D app when a
    Gemma Monster 'gets you'. Inline SVG, no assets."""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 40 40" '
            f'style="vertical-align:middle">'
            f'<path d="M20 3 C31 3 37 12 37 21 C37 32 30 37 20 37 C10 37 3 32 3 21 '
            f'C3 12 9 3 20 3 Z" fill="{color}"/>'
            f'<circle cx="14" cy="18" r="4.2" fill="#14101c"/>'
            f'<circle cx="26" cy="18" r="4.2" fill="#14101c"/>'
            f'<circle cx="15.4" cy="16.6" r="1.4" fill="#fff"/>'
            f'<circle cx="27.4" cy="16.6" r="1.4" fill="#fff"/>'
            f'<path d="M13 28 Q20 33 27 28" stroke="#14101c" stroke-width="2.4" '
            f'fill="none" stroke-linecap="round"/></svg>')


_HUB_TEMPLATE = r"""
<style>
  html,body{margin:0;height:100%;overflow:hidden;background:#0b0710;
    font-family:'Trebuchet MS','Segoe UI',sans-serif;color:#f2e8dc;user-select:none}
  #canvas-container{position:absolute;inset:0;z-index:1}
  #canvas-container canvas{filter:saturate(1.06) contrast(1.09) brightness(.96)}
  #vig{position:absolute;inset:0;pointer-events:none;z-index:2;
    background:radial-gradient(ellipse 75% 62% at 50% 42%,transparent 55%,rgba(4,3,8,.55) 82%,rgba(2,2,6,.9) 100%)}
  #ui{position:absolute;inset:0;z-index:10;pointer-events:none;display:flex;
    flex-direction:column;justify-content:space-between;padding:28px}
  header h1{font-size:2.6rem;font-weight:900;letter-spacing:-1px;text-transform:uppercase;
    background:linear-gradient(135deg,#ffe9d6 25%,#e08d6d 70%,#b98868);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    filter:drop-shadow(0 0 14px rgba(224,141,109,.55))}
  header p{color:#b9a794;font-size:.95rem;margin-top:4px;max-width:430px}
  header{display:flex;justify-content:space-between;align-items:flex-start}
  .hbtns{display:flex;gap:10px}
  #herobox, #herobox *, #herotag{pointer-events:auto}
  #heroname{cursor:text}
  .hbtn{display:inline-flex;align-items:center;justify-content:center;text-align:center;pointer-events:auto;background:rgba(255,240,225,.06);border:1px solid rgba(255,240,225,.16);
    color:#d9c6b2;padding:10px 20px;border-radius:24px;cursor:pointer;font-weight:700;
    text-transform:uppercase;letter-spacing:1px;font-size:.75rem;text-decoration:none;
    transition:all .25s}
  .hbtn:hover{background:rgba(255,240,225,.16);color:#fff}

  /* ---- GAME CARD ---- */
  #card{align-self:flex-end;width:300px;margin-top:auto;margin-bottom:8px;opacity:0;transform:translateY(26px) rotate(1.5deg) scale(.96);
    transition:all .5s cubic-bezier(.16,1,.3,1);pointer-events:auto;
    --mc:#e08d6d}
  #card.active{opacity:1;transform:translateY(0) rotate(0) scale(1)}
  .cardframe{border-radius:16px;padding:7px;
    background:linear-gradient(160deg,var(--mc),#241322 55%,var(--mc));
    box-shadow:0 24px 50px rgba(0,0,0,.85),0 0 34px color-mix(in srgb,var(--mc) 45%,transparent)}
  .cardinner{border-radius:11px;background:
      radial-gradient(120% 65% at 50% 0%,color-mix(in srgb,var(--mc) 26%,#160e18) 0%,#160e18 55%),
      repeating-linear-gradient(45deg,rgba(255,255,255,.02) 0 2px,transparent 2px 6px),#160e18;
    border:1px solid rgba(255,236,214,.14);padding:0 0 14px 0;overflow:hidden}
  .unitchip{display:inline-block;margin:12px 0 0 14px;padding:3px 11px;border-radius:4px;
    background:var(--mc);color:#1a0f14;font-size:.66rem;font-weight:900;letter-spacing:.18em}
  .mname{font-size:2rem;font-weight:900;letter-spacing:-.5px;text-transform:uppercase;
    margin:6px 14px 2px;color:#ffefdd;text-shadow:0 0 12px color-mix(in srgb,var(--mc) 70%,transparent)}
  .mstage{height:132px;margin:8px 14px;border-radius:8px;position:relative;
    background:radial-gradient(60% 90% at 50% 60%,color-mix(in srgb,var(--mc) 38%,#0d0810),#0d0810);
    border:1px solid rgba(255,236,214,.12);display:flex;align-items:center;justify-content:center}
  .mstage svg{filter:drop-shadow(0 0 10px var(--mc))}
  .lore{font-style:italic;color:#cbb8a4;font-size:.9rem;line-height:1.5;margin:2px 16px 10px;
    border-left:3px solid var(--mc);padding-left:10px}
  .stats{display:flex;gap:8px;margin:0 14px 12px}
  .stat{flex:1;text-align:center;background:rgba(255,236,214,.06);border:1px solid rgba(255,236,214,.1);
    border-radius:6px;padding:6px 2px;font-size:.62rem;letter-spacing:.12em;color:#d9c6b2}
  .stat b{display:block;font-size:.95rem;color:#ffefdd;letter-spacing:0}
  .fight{display:block;margin:0 14px;padding:14px;text-align:center;border-radius:9px;
    background:linear-gradient(135deg,var(--mc),color-mix(in srgb,var(--mc) 45%,#7a2a3a));
    color:#1a0f14;font-weight:900;letter-spacing:.12em;text-transform:uppercase;text-decoration:none;
    font-size:.95rem;box-shadow:0 8px 22px color-mix(in srgb,var(--mc) 55%,transparent);
    transition:transform .15s}
  .fight:hover{transform:translateY(-2px)}
  footer{color:#8d7c6b;font-size:.75rem;letter-spacing:.1em;text-transform:uppercase}
  #banner{background:rgba(8,11,20,.72);backdrop-filter:blur(10px);
    border:1px solid rgba(226,192,125,.35);border-left:4px solid #e2c07d;
    border-radius:6px;padding:14px 22px;max-width:520px;
    box-shadow:0 12px 32px rgba(0,0,0,.7)}
  #banner h1{font-size:2.1rem;font-weight:900;letter-spacing:.14em;margin:0;
    background:linear-gradient(135deg,#fff3d8 20%,#e2c07d 60%,#c58f5a);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    filter:drop-shadow(0 0 14px rgba(226,192,125,.55))}
  #banner p{color:#cdd5e4;font-size:.85rem;margin:6px 0 0;letter-spacing:.04em;
    text-shadow:0 1px 3px rgba(0,0,0,.8)}
</style>
<div id="canvas-container"></div>
<div id="vig"></div>
<div id="ui">
  <header>
    <div id="banner">
      <h1>GEMMA MONSTERS</h1>
      <p>Every monster is here to make you forget your math. Defeat them by proving you remember.</p>
    </div>
    <div class="hbtns">
      <button class="hbtn" onclick="resetCamera()">Nexus view</button>
      <a class="hbtn" target="_top" id="exitlink" href="#">Simple dashboard</a>
      <button class="hbtn" id="mutebtn" title="Toggle music and battle sounds">Sound: on</button>
      <span id="herobox" style="display:none;margin-left:10px">
        <input id="heroname" maxlength="20" placeholder="YOUR NAME, CHALLENGER"
          style="background:#1c1119;border:1px solid #3a2a35;border-radius:18px;
          padding:7px 12px;color:#f2e8dc;font-size:.75rem;letter-spacing:.08em;width:170px">
        <button id="herogo" style="background:#e08d6d;border:none;border-radius:18px;
          padding:7px 13px;font-weight:900;color:#14090c;cursor:pointer;font-size:.72rem">GO</button>
      </span>
      <span id="herotag" style="display:none;margin-left:10px;color:#7fe9d6;
        font-size:.72rem;letter-spacing:.12em;font-weight:700"></span>
    </div>
  </header>
  <div id="card">
    <div class="cardframe"><div class="cardinner">
      <span class="unitchip" id="c-unit">UNIT</span>
      <div class="mname" id="c-name">Monster</div>
      <div class="mstage" id="c-stage"></div>
      <p class="lore" id="c-lore">...</p>
      <div class="stats">
        <div class="stat">QUESTIONS<b>5</b></div>
        <div class="stat">GRADE<b>9</b></div>
        <div class="stat">REWARD<b>MASTERY</b></div>
      </div>
      <a class="fight" target="_top" id="c-fight" href="#">Begin challenge &nearr;</a>
    </div></div>
  </div>
  <footer>Click a monster to inspect its card &middot; drag nothing &mdash; the platform turns on its own</footer>
</div>
<script>
(function(){
  let o='';
  try{ o = window.parent.location.origin; }
  catch(e){ try{ o = new URL(document.referrer).origin; }catch(_){} }
  window.__ORIGIN = o;
})();
</script>
__VENDOR__
<script>
window.addEventListener('load', function(){
const UNITS = __UNITS__;
const NAMES = Object.keys(UNITS);
let base='/';
try{ base = window.parent.location.pathname || '/'; }
catch(e){ try{ base = new URL(document.referrer).pathname || '/'; }catch(_){} }
(function(){var x=document.getElementById('exitlink');
  x.href=base+'?exit=1'; x.target='_blank';})();

let scene,camera,renderer,controls,selected=null;
const monsters=[],groups=[],stations=[],mixers=[],torchLights=[],animatedPlants=[],
      ray=new THREE.Raycaster(),mouse=new THREE.Vector2();
let miniR=null,miniScene=null,miniCam=null,miniMix=null,miniObj=null;
let loader=null;
let sealRing=null,sealLight=null;
let particleGeo=null;
const PARTICLE_COUNT=250;
const RING_R=21;
const HOME={x:0,y:22,z:48},HOME_T={x:0,y:6,z:0};
const clock=new THREE.Clock();

init(); animate();

function createStoneTexture(){
  const canvas=document.createElement('canvas');
  canvas.width=512; canvas.height=512;
  const ctx=canvas.getContext('2d');
  ctx.fillStyle='#2a2d36'; ctx.fillRect(0,0,512,512);
  ctx.strokeStyle='#14161c'; ctx.lineWidth=4;
  const rows=16,cols=8,rh=512/rows,cw=512/cols;
  for(let i=0;i<rows;i++){
    const y=i*rh;
    ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(512,y); ctx.stroke();
    const offset=(i%2===0)?0:cw/2;
    for(let j=0;j<cols+1;j++){
      const x=j*cw+offset;
      ctx.beginPath(); ctx.moveTo(x,y); ctx.lineTo(x,y+rh); ctx.stroke();
    }
  }
  for(let i=0;i<15000;i++){
    const x=Math.random()*512,y=Math.random()*512;
    const shade=Math.floor(Math.random()*40);
    ctx.fillStyle='rgba('+shade+','+shade+','+shade+',0.15)';
    ctx.fillRect(x,y,2,2);
  }
  const texture=new THREE.CanvasTexture(canvas);
  texture.wrapS=THREE.RepeatWrapping; texture.wrapT=THREE.RepeatWrapping;
  return texture;
}

function init(){
  const el=document.getElementById('canvas-container');
  scene=new THREE.Scene();
  scene.background=new THREE.Color(0x0a0f1d);
  scene.fog=new THREE.FogExp2(0x0d1424,0.012);

  camera=new THREE.PerspectiveCamera(50,innerWidth/innerHeight,0.1,1000);
  camera.position.set(HOME.x,HOME.y,HOME.z);

  renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
  renderer.setSize(innerWidth,innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.shadowMap.enabled=true;
  renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=0.85;
  renderer.outputEncoding=THREE.sRGBEncoding;
  el.appendChild(renderer.domElement);

  controls=new THREE.OrbitControls(camera,renderer.domElement);
  controls.enableDamping=true;
  controls.dampingFactor=0.04;
  controls.maxPolarAngle=Math.PI/2-0.01;
  controls.minDistance=8;
  controls.maxDistance=85;
  controls.autoRotate=true;
  controls.autoRotateSpeed=0.4;
  controls.target.set(HOME_T.x,HOME_T.y,HOME_T.z);
  renderer.domElement.addEventListener('pointerdown',function(){ controls.autoRotate=false; });

  // ---- lighting: shadows live on the moonlight only ----
  scene.add(new THREE.AmbientLight(0x141c30,0.95));
  const moonLight=new THREE.DirectionalLight(0x9fb6e8,1.25);
  moonLight.position.set(-35,55,-20);
  moonLight.castShadow=true;
  moonLight.shadow.mapSize.width=2048;
  moonLight.shadow.mapSize.height=2048;
  moonLight.shadow.camera.near=10;
  moonLight.shadow.camera.far=120;
  const d=45;
  moonLight.shadow.camera.left=-d; moonLight.shadow.camera.right=d;
  moonLight.shadow.camera.top=d; moonLight.shadow.camera.bottom=-d;
  scene.add(moonLight);
  const fillLight=new THREE.DirectionalLight(0x406080,0.6);
  fillLight.position.set(30,20,30);
  scene.add(fillLight);

  // ---- materials ----
  const stoneTex=createStoneTexture(); stoneTex.repeat.set(3,3);
  const stoneMat=new THREE.MeshStandardMaterial({map:stoneTex,roughness:0.7,metalness:0.2});
  const darkGroundMat=new THREE.MeshStandardMaterial({color:0x121722,roughness:0.9});
  const cobblestoneMat=new THREE.MeshStandardMaterial({color:0x1e2433,roughness:0.8});
  const slateRoofMat=new THREE.MeshStandardMaterial({color:0x182030,roughness:0.5,metalness:0.3});
  const darkWoodMat=new THREE.MeshStandardMaterial({color:0x2b1e16,roughness:0.8});
  const darkPineMat=new THREE.MeshStandardMaterial({color:0x122218,roughness:0.8});

  // ---- terrain and courtyard ----
  const ground=new THREE.Mesh(new THREE.PlaneGeometry(160,160,32,32),darkGroundMat);
  ground.rotation.x=-Math.PI/2; ground.receiveShadow=true; scene.add(ground);
  const courtyard=new THREE.Mesh(new THREE.CylinderGeometry(15,16,0.15,24),cobblestoneMat);
  courtyard.position.set(0,0.08,0); courtyard.receiveShadow=true; scene.add(courtyard);

  // ---- castle: the sealed citadel ----
  const castleGroup=new THREE.Group();
  const mainKeep=new THREE.Mesh(new THREE.BoxGeometry(11,15,11),stoneMat);
  mainKeep.position.set(0,7.5,-2); mainKeep.castShadow=true; mainKeep.receiveShadow=true;
  castleGroup.add(mainKeep);
  const mainRoof=new THREE.Mesh(new THREE.ConeGeometry(8.5,6,4),slateRoofMat);
  mainRoof.position.set(0,18,-2); mainRoof.rotation.y=Math.PI/4; mainRoof.castShadow=true;
  castleGroup.add(mainRoof);
  const gateFrame=new THREE.Mesh(new THREE.BoxGeometry(4.5,5.5,0.8),stoneMat);
  gateFrame.position.set(0,2.75,3.6); gateFrame.castShadow=true; castleGroup.add(gateFrame);
  const woodenDoor=new THREE.Mesh(new THREE.BoxGeometry(3.2,4.5,0.3),darkWoodMat);
  woodenDoor.position.set(0,2.25,3.8); woodenDoor.castShadow=true; castleGroup.add(woodenDoor);
  const towerPos=[{x:-11,z:-11},{x:11,z:-11},{x:-11,z:9},{x:11,z:9}];
  towerPos.forEach(p=>{
    const tower=new THREE.Mesh(new THREE.CylinderGeometry(2.8,3.2,14,16),stoneMat);
    tower.position.set(p.x,7,p.z); tower.castShadow=true; tower.receiveShadow=true;
    castleGroup.add(tower);
    const roof=new THREE.Mesh(new THREE.ConeGeometry(3.6,5.5,16),slateRoofMat);
    roof.position.set(p.x,16.75,p.z); roof.castShadow=true; castleGroup.add(roof);
  });
  const wall1=new THREE.Mesh(new THREE.BoxGeometry(18,9,2.2),stoneMat);
  wall1.position.set(0,4.5,-11); wall1.castShadow=true; castleGroup.add(wall1);
  const wall2=new THREE.Mesh(new THREE.BoxGeometry(2.2,9,18),stoneMat);
  wall2.position.set(-11,4.5,-1); wall2.castShadow=true; castleGroup.add(wall2);
  const wall3=new THREE.Mesh(new THREE.BoxGeometry(2.2,9,18),stoneMat);
  wall3.position.set(11,4.5,-1); wall3.castShadow=true; castleGroup.add(wall3);
  scene.add(castleGroup);

  // story beat: a faint golden seal across the gate. Someone is locked inside.
  sealRing=new THREE.Mesh(new THREE.TorusGeometry(1.7,0.08,10,48),
    new THREE.MeshBasicMaterial({color:0xffd87a,transparent:true,opacity:0.55,
      depthWrite:false,blending:THREE.AdditiveBlending}));
  sealRing.position.set(0,2.4,4.05); scene.add(sealRing);
  const sealBar1=new THREE.Mesh(new THREE.BoxGeometry(3.0,0.09,0.04),
    new THREE.MeshBasicMaterial({color:0xffd87a,transparent:true,opacity:0.4,
      depthWrite:false,blending:THREE.AdditiveBlending}));
  sealBar1.position.set(0,2.4,4.03); sealBar1.rotation.z=Math.PI/4; scene.add(sealBar1);
  const sealBar2=sealBar1.clone(); sealBar2.rotation.z=-Math.PI/4; scene.add(sealBar2);
  sealLight=new THREE.PointLight(0xffd87a,1.4,10);
  sealLight.position.set(0,2.6,5.0); scene.add(sealLight);

  // gate torches
  function createGateTorch(x,y,z){
    const torchLight=new THREE.PointLight(0xff8800,2.2,12);
    torchLight.position.set(x,y,z);
    scene.add(torchLight);
    torchLights.push({light:torchLight,baseIntensity:2.2});
  }
  createGateTorch(-2.2,3.5,4.2);
  createGateTorch(2.2,3.5,4.2);

  // ---- star / nebula dome, very dark blue ----
  (function(){
    const c=document.createElement('canvas'); c.width=1024; c.height=512;
    const g2=c.getContext('2d');
    const gr=g2.createLinearGradient(0,0,0,512);
    gr.addColorStop(0,'#0b1226'); gr.addColorStop(0.5,'#080d1c');
    gr.addColorStop(1,'#060a14');
    g2.fillStyle=gr; g2.fillRect(0,0,1024,512);
    for(let i=0;i<20;i++){
      const x=Math.random()*1024,y=Math.random()*300,r2=40+Math.random()*90;
      const ng=g2.createRadialGradient(x,y,4,x,y,r2);
      ng.addColorStop(0,'rgba(60,90,160,0.08)');
      ng.addColorStop(1,'rgba(0,0,0,0)');
      g2.fillStyle=ng; g2.beginPath(); g2.arc(x,y,r2,0,7); g2.fill();
    }
    for(let i=0;i<520;i++){
      const x=Math.random()*1024,y=Math.random()*400,r2=Math.random()*1.2+0.2;
      g2.fillStyle='rgba('+(190+Math.random()*65|0)+','+(200+Math.random()*55|0)+',255,'
        +(Math.random()*0.5+0.1)+')';
      g2.beginPath(); g2.arc(x,y,r2,0,7); g2.fill();
    }
    const tex=new THREE.CanvasTexture(c);
    const dome=new THREE.Mesh(new THREE.SphereGeometry(140,32,20),
      new THREE.MeshBasicMaterial({map:tex,side:THREE.BackSide,fog:false}));
    scene.add(dome);
    gsap.to(dome.rotation,{y:Math.PI*2,duration:600,repeat:-1,ease:'none'});
  })();

  // ---- dense dark pine forest ring ----
  const forestGroup=new THREE.Group();
  function createDarkPine(x,z,scale){
    const tree=new THREE.Group();
    const trunk=new THREE.Mesh(new THREE.CylinderGeometry(0.3*scale,0.5*scale,3*scale,8),darkWoodMat);
    trunk.position.y=1.5*scale; trunk.castShadow=true; tree.add(trunk);
    for(let i=0;i<4;i++){
      const foliage=new THREE.Mesh(
        new THREE.ConeGeometry((2.8-i*0.5)*scale,(3.2-i*0.4)*scale,8),darkPineMat);
      foliage.position.y=(2.8+i*1.6)*scale;
      foliage.castShadow=true;
      tree.add(foliage);
    }
    tree.position.set(x,0,z);
    return tree;
  }
  const treeCoords=[
    [-33,25],[-36,-12],[-28,-29],[33,25],[37,-8],[30,-28],
    [-41,30],[36,36],[-22,39],[22,41],[-43,-5],[41,-20],
    [-30,-39],[30,-39],[0,-43],[-14,-42],[14,-44],[44,8],[-45,12],
    [8,46],[-8,45],[46,-32],[-46,-30],[40,40],[-40,42]
  ];
  treeCoords.forEach(c=>{
    forestGroup.add(createDarkPine(c[0],c[1],0.9+Math.random()*0.6));
  });
  scene.add(forestGroup);

  // ---- 5 elemental floating platforms, one per unit, ring radius RING_R ----
  loader=(typeof THREE.GLTFLoader!=='undefined')?new THREE.GLTFLoader():null;
  NAMES.forEach((name,i)=>{
    const u=UNITS[name], col=new THREE.Color(u.color);
    const ang=(i/NAMES.length)*Math.PI*2;
    const x=Math.cos(ang)*RING_R, z=Math.sin(ang)*RING_R;

    const platformGroup=new THREE.Group();
    platformGroup.userData={gi:i};
    groups.push(platformGroup);

    // tiered floating stone base
    const base1=new THREE.Mesh(new THREE.CylinderGeometry(3.2,2.6,0.7,12),stoneMat);
    base1.position.y=0; base1.castShadow=true; base1.receiveShadow=true;
    platformGroup.add(base1);
    const base2=new THREE.Mesh(new THREE.CylinderGeometry(2.6,2.8,0.4,12),cobblestoneMat);
    base2.position.y=0.55; base2.castShadow=true; base2.receiveShadow=true;
    platformGroup.add(base2);

    // glowing rune ring in the unit's color
    const runeMat=new THREE.MeshBasicMaterial({color:col,side:THREE.DoubleSide,
      transparent:true,opacity:0.85});
    const ring=new THREE.Mesh(new THREE.RingGeometry(2.0,2.25,32),runeMat);
    ring.rotation.x=-Math.PI/2; ring.position.y=0.76;
    platformGroup.add(ring);

    // torch pillar with a small flame in the unit's color
    const torchPillar=new THREE.Mesh(new THREE.CylinderGeometry(0.2,0.25,1.8,8),darkWoodMat);
    torchPillar.position.set(2.2,1.3,0); torchPillar.castShadow=true;
    platformGroup.add(torchPillar);
    const flame=new THREE.Mesh(new THREE.ConeGeometry(0.22,0.55,8),
      new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:0.9}));
    flame.position.set(2.2,2.45,0); platformGroup.add(flame);
    const torchLight=new THREE.PointLight(col,2.2,12);
    torchLight.position.set(2.2,2.3,0);
    platformGroup.add(torchLight);
    torchLights.push({light:torchLight,baseIntensity:2.2});

    // pulsing underglow light and core disk
    const underLight=new THREE.PointLight(col,3.5,14);
    underLight.position.set(0,-0.4,0);
    platformGroup.add(underLight);
    const glowDiskMat=new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:0.85});
    const glowDisk=new THREE.Mesh(new THREE.CylinderGeometry(2.2,0.5,0.2,16),glowDiskMat);
    glowDisk.position.y=-0.45; platformGroup.add(glowDisk);

    const baseY=2.0;
    platformGroup.position.set(x,baseY,z);
    scene.add(platformGroup);

    // bioluminescent plant cluster on the ground beneath, same color
    const plantGroup=new THREE.Group();
    plantGroup.position.set(x,0,z);
    const plantMat=new THREE.MeshStandardMaterial({color:col,roughness:0.3,
      emissive:col,emissiveIntensity:0.6});
    for(let k=0;k<9;k++){
      const pang=(k/9)*Math.PI*2+Math.random()*0.5;
      const dist=1.2+Math.random()*2.2;
      const px=Math.cos(pang)*dist, pz=Math.sin(pang)*dist;
      const plantHeight=0.8+Math.random()*1.2;
      const stem=new THREE.Mesh(new THREE.ConeGeometry(0.18,plantHeight,5),plantMat);
      stem.position.set(px,plantHeight/2,pz);
      stem.rotation.x=(Math.random()-0.5)*0.4;
      stem.rotation.z=(Math.random()-0.5)*0.4;
      stem.castShadow=true;
      plantGroup.add(stem);
      const tip=new THREE.Mesh(new THREE.SphereGeometry(0.12,8,8),
        new THREE.MeshBasicMaterial({color:col}));
      tip.position.set(px,plantHeight,pz);
      plantGroup.add(tip);
      animatedPlants.push({mesh:stem,baseRotZ:stem.rotation.z,offset:k+i});
    }
    scene.add(plantGroup);

    // the monster standing on top
    const holder=new THREE.Group();
    holder.position.y=0.98;
    holder.userData={i:i};
    platformGroup.add(holder);
    monsters.push(holder);
    const fallback=()=>{
      const m=makeMonster(u.shape,col); m.position.y=1.5;
      m.traverse(o=>{ if(o.isMesh) o.castShadow=true; });
      holder.add(m);
    };
    if(loader && u.model){
      loader.load((window.__ORIGIN||'')+u.model,(gltf)=>{
        const obj=gltf.scene;
        const box=new THREE.Box3().setFromObject(obj);
        const size=box.getSize(new THREE.Vector3());
        const eff=Math.max(size.y, 0.62*Math.max(size.x,size.z), 0.001);
        const scale=(3.9*(u.ns||1))/eff;  // blended height/width metric - fair for fliers and bipeds
        obj.scale.setScalar(scale);
        const box2=new THREE.Box3().setFromObject(obj);
        const c=box2.getCenter(new THREE.Vector3());
        obj.position.x-=c.x; obj.position.z-=c.z; obj.position.y-=box2.min.y;
        obj.traverse(o=>{ if(o.isMesh) o.castShadow=true; });
        holder.add(obj);
        if(gltf.animations && gltf.animations.length){
          const mix=new THREE.AnimationMixer(obj);
          const idle=gltf.animations.find(a=>a.name===u.clipA)
                   ||gltf.animations.find(a=>/idle/i.test(a.name))||gltf.animations[0];
          const act=mix.clipAction(idle); act.timeScale=(u.spA||0.8); act.play();
          mixers.push(mix);
        }
      },undefined,fallback);
    } else fallback();

    // generous invisible hit volume - clicking anywhere near the beast counts
    const hitVol=new THREE.Mesh(new THREE.CylinderGeometry(4.8,4.8,10,10),
      new THREE.MeshBasicMaterial({transparent:true,opacity:0.0,depthWrite:false}));
    hitVol.position.y=4; hitVol.userData.gi=i; platformGroup.add(hitVol);

    stations.push({group:platformGroup,holder:holder,ring:ring,underLight:underLight,
      glowDiskMat:glowDiskMat,baseY:baseY,phaseOffset:i*1.25,ang:ang,x:x,z:z});
  });

  // ---- rising embers ----
  particleGeo=new THREE.BufferGeometry();
  const particlePos=new Float32Array(PARTICLE_COUNT*3);
  for(let i=0;i<PARTICLE_COUNT;i++){
    particlePos[i*3]=(Math.random()-0.5)*60;
    particlePos[i*3+1]=Math.random()*20;
    particlePos[i*3+2]=(Math.random()-0.5)*60;
  }
  particleGeo.setAttribute('position',new THREE.BufferAttribute(particlePos,3));
  const embers=new THREE.Points(particleGeo,new THREE.PointsMaterial({
    color:0xffcc55,size:0.2,transparent:true,opacity:0.75,
    blending:THREE.AdditiveBlending,depthWrite:false}));
  scene.add(embers);

  addEventListener('resize',()=>{
    camera.aspect=innerWidth/innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth,innerHeight);
  });
  renderer.domElement.addEventListener('click',onClick);
}

function makeMonster(shape,col){
  const mat=new THREE.MeshStandardMaterial({color:col,metalness:.8,roughness:.12,flatShading:true});
  const wire=new THREE.MeshBasicMaterial({color:0xfff1e2,wireframe:true,transparent:true,opacity:.35});
  let m,w;
  if(shape==='shard'){m=new THREE.Mesh(new THREE.OctahedronGeometry(1.5,0),mat);m.scale.y=2;
    w=new THREE.Mesh(new THREE.OctahedronGeometry(1.62,0),wire);w.scale.y=2;}
  else if(shape==='knot'){m=new THREE.Mesh(new THREE.TorusKnotGeometry(.8,.3,100,16),mat);
    w=new THREE.Mesh(new THREE.TorusKnotGeometry(.85,.32,100,16),wire);}
  else if(shape==='blob'){m=new THREE.Mesh(new THREE.IcosahedronGeometry(1.4,2),mat);
    w=new THREE.Mesh(new THREE.IcosahedronGeometry(1.5,2),wire);}
  else if(shape==='poly'){m=new THREE.Mesh(new THREE.DodecahedronGeometry(1.5,0),mat);
    w=new THREE.Mesh(new THREE.DodecahedronGeometry(1.62,0),wire);}
  else {m=new THREE.Mesh(new THREE.TorusGeometry(1.2,.42,16,50),mat);m.rotateX(Math.PI/2);
    w=new THREE.Mesh(new THREE.TorusGeometry(1.25,.46,16,50),wire);w.rotateX(Math.PI/2);}
  const g=new THREE.Group(); g.add(m); g.add(w);
  // eyes so it reads as a creature
  for(const sx of [-0.45,0.45]){
    const eye=new THREE.Group();
    const ball=new THREE.Mesh(new THREE.SphereGeometry(.19,12,12),
      new THREE.MeshBasicMaterial({color:0xfff6ec}));
    const pup=new THREE.Mesh(new THREE.SphereGeometry(.09,10,10),
      new THREE.MeshBasicMaterial({color:0x14101c}));
    pup.position.z=.13; eye.add(ball); eye.add(pup);
    eye.position.set(sx,.35,1.35); g.add(eye);
  }
  return g;
}

// ---- the card's glass pane: a live close-up of the monster walking toward you ----
function ensureMini(){
  if(miniR) return;
  const stage=document.getElementById('c-stage');
  miniR=new THREE.WebGLRenderer({antialias:true,alpha:true});
  stage.innerHTML=''; stage.appendChild(miniR.domElement);
  miniScene=new THREE.Scene();
  miniCam=new THREE.PerspectiveCamera(40,2,0.1,50);
  miniCam.position.set(0,1.6,3.6); miniCam.lookAt(0,1.15,0);
  miniScene.add(new THREE.AmbientLight(0xffffff,0.95));
  const sp=new THREE.SpotLight(0xfff3e0,2.6,30,Math.PI/4,0.5);
  sp.position.set(0,6,3); miniScene.add(sp);
}
function showMini(name){
  const u=UNITS[name]; ensureMini();
  const stage=document.getElementById('c-stage');
  const wpx=Math.max(stage.clientWidth,240);
  miniR.outputEncoding=THREE.sRGBEncoding; miniR.setSize(wpx,132); miniCam.aspect=wpx/132; miniCam.updateProjectionMatrix();
  if(miniObj){ miniScene.remove(miniObj); miniObj=null; } miniMix=null;
  if(loader && u.model){
    loader.load((window.__ORIGIN||'')+u.model,(gltf)=>{
      const obj=gltf.scene;
      const box=new THREE.Box3().setFromObject(obj);
      const size=box.getSize(new THREE.Vector3());
      const sc=3.0/Math.max(size.x,size.y,size.z,0.001); obj.scale.setScalar(sc);
      const b2=new THREE.Box3().setFromObject(obj);
      const c=b2.getCenter(new THREE.Vector3());
      obj.position.set(-c.x,-b2.min.y,-c.z);
      obj.userData.t0=performance.now();
      miniScene.add(obj); miniObj=obj;
      if(gltf.animations&&gltf.animations.length){
        miniMix=new THREE.AnimationMixer(obj);
        const clip=gltf.animations.find(a=>a.name===u.clipA)
                 ||gltf.animations.find(a=>/idle/i.test(a.name))
                 ||gltf.animations[0];
        const act=miniMix.clipAction(clip);
        act.timeScale=(u.spA||0.8)*0.85;   // calm, menacing - never frantic
        act.play();
      }
    });
  }
}

function svgMini(col){
  return '<svg width="72" height="72" viewBox="0 0 40 40"><circle cx="20" cy="20" r="14" fill="'+col+'" opacity="0.85"/><circle cx="20" cy="20" r="17" fill="none" stroke="'+col+'" stroke-width="1.4" opacity="0.5"/></svg>';
}

let __downXY=null;
addEventListener('pointerdown',e=>{ __downXY=[e.clientX,e.clientY]; });

function stationAtPointer(e){
  mouse.x=(e.clientX/innerWidth)*2-1; mouse.y=-(e.clientY/innerHeight)*2+1;
  ray.setFromCamera(mouse,camera);
  const hit=ray.intersectObjects(groups,true);
  if(hit.length){
    let o=hit[0].object;
    while(o.parent && o.userData.gi===undefined) o=o.parent;
    if(o.userData.gi!==undefined) return o.userData.gi;
  }
  // fallback: nearest station within 70px on screen
  let best=-1,bd=70;
  const v=new THREE.Vector3();
  stations.forEach((st2,i2)=>{
    st2.holder.getWorldPosition(v); v.project(camera);
    const sx=(v.x+1)/2*innerWidth, sy=(-v.y+1)/2*innerHeight;
    const d=Math.hypot(sx-e.clientX, sy-e.clientY);
    if(v.z<1 && d<bd){ bd=d; best=i2; }
  });
  return best>=0 ? best : undefined;
}

function onClick(e){
  if(e.target.closest && e.target.closest('#ui a, #ui button, #card, input')) return;
  if(__downXY && Math.hypot(e.clientX-__downXY[0], e.clientY-__downXY[1])>7) return; // was a drag
  const gi=stationAtPointer(e);
  if(gi!==undefined) focus(gi);
}

addEventListener('pointermove',(function(){
  let cool=false;
  return function(e){
    if(cool) return; cool=true; setTimeout(()=>cool=false,120);
    if(!renderer) return;
    const gi=stationAtPointer(e);
    renderer.domElement.style.cursor = (gi!==undefined) ? 'pointer' : 'default';
  };
})());

function focus(i){
  if(selected===i) return; selected=i;
  const name=NAMES[i], u=UNITS[name];
  const st=stations[i], ang=st.ang;
  controls.autoRotate=false;
  // vantage: outside the ring, slightly above, looking at the monster
  gsap.to(camera.position,{
    x:Math.cos(ang)*(RING_R+12), y:8.5, z:Math.sin(ang)*(RING_R+12),
    duration:1.8, ease:'power3.inOut'});
  gsap.to(controls.target,{
    x:st.x, y:st.baseY+2.0, z:st.z,
    duration:1.8, ease:'power3.inOut'});
  // turn the monster to face the camera
  gsap.to(st.holder.rotation,{y:Math.PI/2-ang,duration:0.9,ease:'power2.out'});
  const card=document.getElementById('card');
  card.style.setProperty('--mc',u.color);
  document.getElementById('c-unit').textContent=name.toUpperCase()+' UNIT';
  document.getElementById('c-name').textContent=u.monster;
  document.getElementById('c-lore').textContent='"'+u.lore+'"';
  try{ showMini(name); }catch(e){ document.getElementById('c-stage').innerHTML=svgMini(u.color); }
  const fbtn=document.getElementById('c-fight');
  fbtn.onclick=null;
  const hero=(localStorage.getItem('gwb_hero')||'').trim();
  fbtn.href=base+'?station='+encodeURIComponent(name)
           +(hero?'&hero='+encodeURIComponent(hero):'');
  fbtn.target='_blank'; fbtn.rel='opener';
  card.classList.add('active');
}

function resetCamera(){
  selected=null; document.getElementById('card').classList.remove('active');
  gsap.to(camera.position,{x:HOME.x,y:HOME.y,z:HOME.z,duration:1.8,ease:'power2.inOut'});
  gsap.to(controls.target,{x:HOME_T.x,y:HOME_T.y,z:HOME_T.z,duration:1.8,ease:'power2.inOut',
    onComplete:()=>{ controls.autoRotate=true; }});
}

function animate(){
  requestAnimationFrame(animate);
  const dt=Math.min(0.05,clock.getDelta());
  const time=clock.getElapsedTime();

  mixers.forEach(m=>m.update(dt));

  // torch flicker (gate torches + platform torches)
  torchLights.forEach((t,i)=>{
    t.light.intensity=t.baseIntensity+Math.sin(time*12+i)*0.4+(Math.random()-0.5)*0.3;
  });

  // hover bob, pulsing underglow, spinning rune rings
  stations.forEach((p)=>{
    const hoverOffset=Math.sin(time*2.0+p.phaseOffset)*0.35;
    p.group.position.y=p.baseY+hoverOffset;
    const pulse=Math.sin(time*4.0+p.phaseOffset)*0.5+0.5;
    p.underLight.intensity=2.0+pulse*2.5;
    p.glowDiskMat.opacity=0.5+pulse*0.45;
    p.ring.rotation.z=time*0.4+p.phaseOffset;
  });

  // sway bioluminescent plants
  animatedPlants.forEach((plant)=>{
    plant.mesh.rotation.z=plant.baseRotZ+Math.sin(time*2.5+plant.offset)*0.08;
  });

  // gate seal breathes: the citadel is locked from the outside
  if(sealRing){
    const sp=Math.sin(time*1.4)*0.5+0.5;
    sealRing.material.opacity=0.35+sp*0.35;
    sealRing.rotation.z=time*0.25;
    sealLight.intensity=1.0+sp*0.9;
  }

  // rising embers
  const pArr=particleGeo.attributes.position.array;
  for(let i=0;i<PARTICLE_COUNT;i++){
    pArr[i*3+1]+=0.015;
    if(pArr[i*3+1]>20) pArr[i*3+1]=0;
  }
  particleGeo.attributes.position.needsUpdate=true;

  // idle spin for unselected monsters
  monsters.forEach((m,i)=>{
    if(selected!==i) m.rotation.y+=0.0035;
  });

  if(miniMix) miniMix.update(dt);
  if(miniObj){
    const tt=(performance.now()-miniObj.userData.t0)*0.001;
    miniObj.position.z=Math.min(1.15,tt*0.55)+Math.sin(tt*1.7)*0.07;
  }
  if(miniR && document.getElementById('card').classList.contains('active'))
    miniR.render(miniScene,miniCam);

  controls.update();
  renderer.render(scene,camera);
}

// hero name: ask once, remember forever
(function(){
  const box=document.getElementById('herobox'), tag=document.getElementById('herotag');
  const saved=(localStorage.getItem('gwb_hero')||'').trim();
  function show(n){ tag.textContent='CHALLENGER: '+n.toUpperCase(); tag.style.display='inline';
                    box.style.display='none'; }
  if(saved){ show(saved); } else { box.style.display='inline'; }
  // click your name tag to change it
  tag.style.cursor='pointer';
  tag.title='Click to change your name';
  tag.onclick=function(){
    const cur=(localStorage.getItem('gwb_hero')||'').trim();
    document.getElementById('heroname').value=cur;
    box.style.display='inline'; tag.style.display='none';
    document.getElementById('heroname').focus();
  };
  function saveHero(){
    const n=document.getElementById('heroname').value.trim();
    if(n){ localStorage.setItem('gwb_hero', n); show(n); } }
  document.getElementById('herogo').onclick=saveHero;
  document.getElementById('heroname').addEventListener('keydown',function(e){
    if(e.key==='Enter') saveHero(); });
  // the Begin link picks up the hero name at CLICK time, not card-open time
  const fb=document.getElementById('c-fight');
  fb.addEventListener('pointerdown',function(){
    try{
      if(!this.href || this.href.indexOf('?station=')<0) return;
      const u2=new URL(this.href);
      const h=(localStorage.getItem('gwb_hero')||'').trim();
      if(h) u2.searchParams.set('hero',h); else u2.searchParams.delete('hero');
      this.href=u2.toString();
    }catch(e){}
  });
})();
window.resetCamera = resetCamera;

// --- nexus theme: dark cinematic loop (starts on first interaction) ---
// A mute toggle lives in the header for anyone who prefers quiet; the choice
// persists (when the browser allows) and the battle arenas honour it too.
(function(){
  function saved(){ try{ return localStorage.getItem('gm_mute')==='1'; }catch(e){ return false; } }
  window.__muted = saved();
  const mb=document.getElementById('mutebtn');
  function paint(){ if(mb) mb.textContent = window.__muted ? 'Sound: off' : 'Sound: on'; }
  paint();
  if(mb) mb.addEventListener('click', function(){
    window.__muted = !window.__muted;
    try{ localStorage.setItem('gm_mute', window.__muted ? '1' : '0'); }catch(e){}
    const t=window.__theme;
    if(t){ if(window.__muted) t.pause(); else t.play().catch(function(){}); }
    paint();
  });
  let started=false;
  addEventListener('pointerdown', function(){
    if(started) return; started=true;
    fetch((window.__ORIGIN||'')+'/app/static/audio/nexus-theme.mp3')
      .then(r=>r.blob())
      .then(b=>{
        const a=new Audio(URL.createObjectURL(new Blob([b],{type:'audio/mpeg'})));
        a.loop=true; a.volume=0.0;
        if(!window.__muted) a.play().catch(function(){});
        // gentle fade in, plus a duck near the end of each loop (the track swells)
        const BASE=0.30, DUCK_S=6;
        let fade=0; const t2=setInterval(function(){ fade=Math.min(1,fade+0.06);
          if(fade>=1) clearInterval(t2); },120);
        a.addEventListener('timeupdate',function(){
          let duck=1;
          if(isFinite(a.duration)){
            const left=a.duration-a.currentTime;
            if(left<DUCK_S) duck=Math.max(0.55, left/DUCK_S);
          }
          a.volume=BASE*fade*duck;
        });
        window.__theme=a;
      }).catch(function(){});
  }, {once:true});
})();
window.__focus = focus;

});
</script>
"""


_VENDOR_FILES = ["three.min.js", "gsap.min.js", "OrbitControls.js", "EffectComposer.js", "RenderPass.js",
                 "ShaderPass.js", "CopyShader.js", "LuminosityHighPassShader.js",
                 "UnrealBloomPass.js", "GLTFLoader.js"]
_vendor_cache = None  # dict of tuple(files)->joined script tags


def _vendor_js(files=None) -> str:
    global _vendor_cache
    key = tuple(files) if files else tuple(_VENDOR_FILES)
    if _vendor_cache is None:
        _vendor_cache = {}
    if key not in _vendor_cache:
        parts = []
        vdir = Path(__file__).parent / "static" / "vendor"
        for f in key:
            p = vdir / f
            if p.exists():
                parts.append("<script>\n" + p.read_text() + "\n</script>")
        _vendor_cache[key] = "\n".join(parts)
    return _vendor_cache[key]


def _hub_html():
    data = {n: {"monster": m["monster"], "color": m["color"], "shape": m["shape"],
                "lore": m["lore"], "model": m.get("model", ""),
                "clipA": m.get("clip_ambient", ""), "spA": m.get("sp_ambient", 0.8),
                "ns": m.get("ns", 1.0)}
            for n, m in MONSTERS.items()}
    return (_HUB_TEMPLATE
            .replace("__VENDOR__", _vendor_js())
            .replace("__UNITS__", json.dumps(data)))


def to_dashboard():
    reset()
    st.session_state.adventure = False
    st.session_state.stage = "intro"


_TAUNT_TEMPLATE = r"""
<style>html,body{margin:0;background:#0b0710;overflow:hidden}</style>
<div id="v"></div>
<script>
(function(){ let o='';
  try{ o=window.parent.location.origin; }catch(e){ try{ o=new URL(document.referrer).origin; }catch(_){} }
  window.__ORIGIN=o; })();
</script>
__VENDOR__
<script>
window.addEventListener('load', function(){
  const W=170,H=170;
  const r=new THREE.WebGLRenderer({antialias:true,alpha:true});
  r.setSize(W,H); r.outputEncoding=THREE.sRGBEncoding; document.getElementById('v').appendChild(r.domElement);
  const sc=new THREE.Scene();
  const cam=new THREE.PerspectiveCamera(38,W/H,0.1,50);
  cam.position.set(0,1.6,4.6); cam.lookAt(0,1.1,0);
  sc.add(new THREE.AmbientLight(0xffffff,0.95));
  const sp=new THREE.SpotLight(0xfff3e0,3.0,30,Math.PI/4,0.5);
  sp.position.set(0,7,3); sc.add(sp);
  let mix=null,obj=null;
  new THREE.GLTFLoader().load((window.__ORIGIN||'')+"__MODEL__",(g)=>{
    obj=g.scene;
    const b=new THREE.Box3().setFromObject(obj), sz=b.getSize(new THREE.Vector3());
    obj.scale.setScalar(2.6/Math.max(sz.x,sz.y,sz.z,0.001));
    const b2=new THREE.Box3().setFromObject(obj), c=b2.getCenter(new THREE.Vector3());
    obj.position.set(-c.x,-b2.min.y,-c.z); sc.add(obj);
    const hh=b2.max.y-b2.min.y;
    cam.position.set(0, hh*0.55, 3.4);
    cam.lookAt(0, hh*0.5, 0);
    if(g.animations&&g.animations.length){
      mix=new THREE.AnimationMixer(obj);
      const clip=g.animations.find(a=>a.name==="__CLIPPREF__")
               ||g.animations.find(a=>/idle/i.test(a.name))||g.animations[0];
      const act=mix.clipAction(clip); act.timeScale=__TS__; act.play();
    }
  });
  let pt=0;
  (function loop(t){ requestAnimationFrame(loop);
    const tt=(t||0)*0.001, dt=Math.min(0.05,tt-pt); pt=tt;
    if(mix) mix.update(dt);
    if(obj) obj.rotation.y=Math.sin(tt*0.7)*0.35;
    r.render(sc,cam); })(0);
});
</script>
"""


_FIGHT_TEMPLATE = r"""
<style>
html,body{margin:0;background:#0b0710;overflow:hidden;font-family:'Trebuchet MS',sans-serif}
#hud{position:absolute;inset:0;pointer-events:none;color:#f2e8dc}
#title{position:absolute;top:8px;left:12px;font-size:.68rem;letter-spacing:.16em;color:#e08d6d;font-weight:900}
#hp{position:absolute;top:8px;right:12px;width:170px}
#hp .lbl{font-size:.6rem;letter-spacing:.14em;color:#b9a794;text-align:right}
#hp .bar{height:10px;border:1px solid #3a2a35;border-radius:6px;background:#160e18;overflow:hidden}
#hp .fill{height:100%;width:100%;background:linear-gradient(90deg,#ff6b6b,__COLOR__);transition:width .2s}
#bub{position:absolute;bottom:10px;left:12px;max-width:60%;background:#1c1119;
  border:1px solid __COLOR__;border-radius:12px 12px 12px 2px;padding:7px 11px;
  font-size:.78rem;box-shadow:0 0 14px __COLOR__55}
#win{position:absolute;inset:0;display:none;align-items:center;justify-content:center;
  font-size:1.1rem;font-weight:900;letter-spacing:.14em;color:#ffefdd;
  text-shadow:0 0 18px __COLOR__}
</style>
<div id="v"></div>
<div id="hud">
  <div id="title">WHILE GEMMA FORGES YOUR GUIDE... CLICK THE MONSTER</div>
  <div id="hp"><div class="lbl">__NAME__ HP</div><div class="bar"><div class="fill" id="fill"></div></div></div>
  <div id="bub"><strong>__NAME__:</strong> <span id="line"></span></div>
  <div id="win">DOWN - NOW FINISH IT WITH THE MATH BELOW</div>
</div>
<script>
(function(){ let o='';
  try{ o=window.parent.location.origin; }catch(e){ try{ o=new URL(document.referrer).origin; }catch(_){} }
  window.__ORIGIN=o; })();
</script>
__VENDOR__
<script>
window.addEventListener('load', function(){
  const TAUNTS=__TAUNTS__;
  let li=0; const lineEl=document.getElementById('line');
  lineEl.textContent=TAUNTS[0];
  setInterval(()=>{ li=(li+1)%TAUNTS.length; lineEl.textContent=TAUNTS[li]; },3600);
  const W=innerWidth,H=innerHeight;
  const r=new THREE.WebGLRenderer({antialias:true});
  r.setSize(W,H); r.outputEncoding=THREE.sRGBEncoding; r.setClearColor(0x0b0710);
  document.getElementById('v').appendChild(r.domElement);
  const sc=new THREE.Scene();
  const cam=new THREE.PerspectiveCamera(36,W/H,0.1,60);
  cam.position.set(0,1.8,5.4); cam.lookAt(0,1.1,0);
  sc.add(new THREE.AmbientLight(0xffffff,0.9));
  const sp=new THREE.SpotLight(0xfff3e0,3.2,40,Math.PI/4,0.5); sp.position.set(0,8,4); sc.add(sp);
  let mix=null,obj=null,hp=100,down=false,flash=0;
  new THREE.GLTFLoader().load((window.__ORIGIN||'')+"__MODEL__",(g)=>{
    obj=g.scene;
    const b=new THREE.Box3().setFromObject(obj), sz=b.getSize(new THREE.Vector3());
    obj.scale.setScalar(2.8/Math.max(sz.x,sz.y,sz.z,0.001));
    const b2=new THREE.Box3().setFromObject(obj), c=b2.getCenter(new THREE.Vector3());
    obj.position.set(-c.x,-b2.min.y,-c.z); sc.add(obj);
    if(g.animations&&g.animations.length){
      mix=new THREE.AnimationMixer(obj);
      const clip=g.animations.find(a=>a.name==="__FCLIP__")
               ||g.animations.find(a=>/idle/i.test(a.name))||g.animations[0];
      const act=mix.clipAction(clip); act.timeScale=__FTS__; act.play();
    }
  });
  addEventListener('click',()=>{
    if(down||!obj) return;
    hp=Math.max(0,hp-9); flash=1;
    document.getElementById('fill').style.width=hp+'%';
    if(hp===0){ down=true;
      document.getElementById('win').style.display='flex';
      document.getElementById('bub').style.display='none'; }
  });
  let pt=0;
  (function loop(t){ requestAnimationFrame(loop);
    const tt=(t||0)*0.001, dt=Math.min(0.05,tt-pt); pt=tt;
    if(mix) mix.update(dt);
    if(obj){
      obj.rotation.y=Math.sin(tt*0.8)*0.4;
      if(flash>0){ flash-=dt*4; obj.position.x=Math.sin(tt*60)*0.06*flash; }
      if(down){ obj.rotation.z=Math.min(Math.PI/2,obj.rotation.z+dt*2); }
    }
    r.render(sc,cam); })(0);
});
</script>
"""


def _fight_html(mon, score, total):
    taunts = [
        f"{score} out of {total}? I barely felt that.",
        "Keep clicking, hero - the real fight is the math below.",
        "I have devoured sharper answers for breakfast.",
        f"Gemma is writing your rescue plan. You will need it after {score}/{total}.",
        "Hit me all you want - only understanding defeats me.",
    ]
    return (_FIGHT_TEMPLATE
            .replace("__VENDOR__", _vendor_js(["three.min.js", "GLTFLoader.js"]))
            .replace("__MODEL__", mon["model"])
            .replace("__COLOR__", mon["color"])
            .replace("__NAME__", mon["monster"])
            .replace("__FCLIP__", mon.get("clip_fight", ""))
            .replace("__FTS__", str(mon.get("sp_fight", 0.7)))
            .replace("__TAUNTS__", json.dumps(taunts)))


def _taunt_html(model, clip_pref="walk", speed=0.55):
    return (_TAUNT_TEMPLATE
            .replace("__VENDOR__", _vendor_js(["three.min.js", "GLTFLoader.js"]))
            .replace("__MODEL__", model)
            .replace("__CLIPPREF__", clip_pref)
            .replace("__TS__", str(speed)))


_ENCOUNTER_TEMPLATE = r"""
<style>
html,body{margin:0;background:#0b0710;overflow:hidden;font-family:'Trebuchet MS',sans-serif}
#stage{position:relative;width:100%;height:100vh}
#bub{position:absolute;left:50%;bottom:26px;transform:translateX(-50%);
  width:min(560px,86%);background:#1c1119;border:1px solid __COLOR__;
  border-radius:14px;padding:14px 16px;color:#f2e8dc;font-size:1rem;
  box-shadow:0 0 22px __COLOR__66}
#bub .who{font-size:.68rem;letter-spacing:.16em;color:__COLOR__;font-weight:900}
#next{position:absolute;right:10px;bottom:8px;background:__COLOR__;color:#14090c;
  font-weight:900;border:none;border-radius:8px;padding:5px 14px;cursor:pointer;
  letter-spacing:.08em}
</style>
<div id="stage"><div id="v"></div>
  <div id="bub"><div class="who">__NAME__</div>
    <div id="line" style="margin:6px 40px 10px 0"></div>
    <button id="next">NEXT</button></div>
</div>
<script>
(function(){ let o='';
  try{ o=window.parent.location.origin; }catch(e){ try{ o=new URL(document.referrer).origin; }catch(_){} }
  window.__ORIGIN=o; })();
</script>
__VENDOR__
<script>
window.addEventListener('load', function(){
  const LINES=__LINES__; let li=0;
  const lineEl=document.getElementById('line'), btn=document.getElementById('next');
  lineEl.textContent=LINES[0];
  btn.onclick=()=>{ li++;
    if(li>=LINES.length){ lineEl.textContent="Enough talk. Step in - if you dare.";
      btn.style.display='none'; return; }
    lineEl.textContent=LINES[li]; };
  const W=innerWidth,H=innerHeight;
  const r=new THREE.WebGLRenderer({antialias:true});
  r.setSize(W,H); r.outputEncoding=THREE.sRGBEncoding; r.setClearColor(0x0b0710);
  document.getElementById('v').appendChild(r.domElement);
  const sc=new THREE.Scene();
  const cam=new THREE.PerspectiveCamera(40,W/H,0.1,60);
  cam.position.set(0,2.0,5.6); cam.lookAt(0,1.5,0);
  sc.add(new THREE.AmbientLight(0xffffff,0.85));
  const sp=new THREE.SpotLight(0xfff3e0,3.4,40,Math.PI/4,0.5); sp.position.set(0,9,4); sc.add(sp);
  const rim=new THREE.PointLight(new THREE.Color("__COLOR__"),2.2,18); rim.position.set(0,3,-3); sc.add(rim);
  let mix=null,obj=null;
  new THREE.GLTFLoader().load((window.__ORIGIN||'')+"__MODEL__",(g)=>{
    obj=g.scene;
    const b=new THREE.Box3().setFromObject(obj), sz=b.getSize(new THREE.Vector3());
    obj.scale.setScalar(3.6/Math.max(sz.x,sz.y,sz.z,0.001));
    const b2=new THREE.Box3().setFromObject(obj), c=b2.getCenter(new THREE.Vector3());
    obj.position.set(-c.x,-b2.min.y,-c.z); sc.add(obj);
    if(g.animations&&g.animations.length){
      mix=new THREE.AnimationMixer(obj);
      const clip=g.animations.find(a=>a.name==="__ECLIP__")
               ||g.animations.find(a=>/idle/i.test(a.name))||g.animations[0];
      const act=mix.clipAction(clip); act.timeScale=__ETS__; act.play();
    }
  });
  let pt=0;
  (function loop(t){ requestAnimationFrame(loop);
    const tt=(t||0)*0.001, dt=Math.min(0.05,tt-pt); pt=tt;
    if(mix) mix.update(dt);
    if(obj) obj.rotation.y=Math.sin(tt*0.5)*0.25;
    r.render(sc,cam); })(0);
});
</script>
"""


_BOSS_TEMPLATE = r"""
<style>
html,body{margin:0;background:#050308;overflow:hidden;font-family:'Trebuchet MS',sans-serif}
#stage{position:relative;width:100%;height:100vh}
#stage.shake{animation:sh .35s}
@keyframes sh{0%,100%{transform:none}20%{transform:translate(-9px,4px)}40%{transform:translate(8px,-5px)}60%{transform:translate(-6px,-3px)}80%{transform:translate(5px,3px)}}
#vig2{position:absolute;inset:0;pointer-events:none;z-index:3;
  background:radial-gradient(ellipse 70% 60% at 50% 40%,transparent 50%,rgba(2,1,4,.75) 85%,#020104 100%)}
#hud2{position:absolute;inset:0;z-index:5;pointer-events:none;color:#e8dfd2}
#btitle{position:absolute;top:14px;left:18px;font-size:1.5rem;font-weight:900;
  letter-spacing:.2em;color:#cfd4ff;text-shadow:0 0 18px #6672ff}
#bsub{position:absolute;top:52px;left:19px;font-size:.7rem;letter-spacing:.16em;color:#8a86a8}
#lives{position:absolute;top:16px;right:18px;display:flex;gap:7px}
.pip{width:20px;height:20px;background:linear-gradient(135deg,#ff6b6b,#a8434f);
  border-radius:4px;transform:rotate(45deg);box-shadow:0 0 10px #ff6b6b88}
.pip.gone{background:#241a22;box-shadow:none}
#qbox{position:absolute;left:50%;bottom:30px;transform:translateX(-50%);
  width:min(480px,88%);text-align:center;pointer-events:auto}
#qq{font-size:2rem;font-weight:900;color:#fff;text-shadow:0 0 16px #6672ff;margin-bottom:8px}
#timer{height:7px;background:#181226;border-radius:4px;overflow:hidden;margin:0 0 12px}
#tfill{height:100%;width:100%;background:linear-gradient(90deg,#6672ff,#cfd4ff);transition:width .1s linear}
#ans{background:#120d1c;border:2px solid #6672ff;border-radius:10px;color:#fff;
  font-size:1.4rem;text-align:center;width:150px;padding:9px;outline:none}
#go2{background:#6672ff;border:none;border-radius:10px;color:#0a0714;font-weight:900;
  font-size:1rem;padding:12px 22px;margin-left:10px;cursor:pointer;letter-spacing:.1em}
#bline{position:absolute;left:50%;top:70px;transform:translateX(-50%);max-width:80%;
  background:rgba(10,7,18,.85);border:1px solid #6672ff;border-radius:12px;
  padding:9px 15px;font-size:.95rem;color:#dfe2ff;text-align:center;
  box-shadow:0 0 20px #6672ff44}
#endcard{display:none;position:absolute;inset:0;z-index:6;align-items:center;justify-content:center;
  flex-direction:column;background:rgba(3,2,7,.72);text-align:center;padding:0 8%}
#endtitle{font-size:2.2rem;font-weight:900;letter-spacing:.16em;color:#fff;text-shadow:0 0 24px #6672ff}
#endsub{margin-top:10px;color:#b9b4d6;font-size:1rem}
</style>
<div id="stage">
  <div id="v"></div><div id="vig2"></div>
  <div id="hud2">
    <div id="btitle">THE COLLECTOR</div>
    <div id="bsub">HE TESTS WHAT SHOULD ALREADY BE YOURS</div>
    <div id="lives"><div class="pip"></div><div class="pip"></div><div class="pip"></div></div>
    <div id="bline">So. __HERO__. The one the little ones whisper about. Answer fast - I have no patience for slow minds.</div>
    <div id="qbox">
      <div id="qq"></div>
      <div id="timer"><div id="tfill"></div></div>
      <input id="ans" inputmode="numeric" autocomplete="off">
      <button id="go2">STRIKE</button>
    </div>
  </div>
  <div id="endcard"><div id="endtitle"></div><div id="endsub"></div></div>
</div>
<script>
(function(){ let o='';
  try{ o=window.parent.location.origin; }catch(e){ try{ o=new URL(document.referrer).origin; }catch(_){} }
  window.__ORIGIN=o; })();
</script>
__VENDOR__
<script>
window.addEventListener('load', function(){
  // procedural battle audio (no files): thud on hit, resolution chord at the end
  let __actx=null;
  function __a(){ if(!__actx) __actx=new (window.AudioContext||window.webkitAudioContext)(); return __actx; }
  function __gmMuted(){ try{ return localStorage.getItem('gm_mute')==='1'; }catch(e){ return false; } }
  function sndThud(){ if(__gmMuted()) return; try{ const c=__a(),o=c.createOscillator(),g=c.createGain();
    o.type='sine'; o.frequency.setValueAtTime(110,c.currentTime);
    o.frequency.exponentialRampToValueAtTime(38,c.currentTime+0.25);
    g.gain.setValueAtTime(0.5,c.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+0.3);
    o.connect(g); g.connect(c.destination); o.start(); o.stop(c.currentTime+0.32);}catch(e){} }
  function sndEnd(won){ if(__gmMuted()) return; try{ const c=__a();
    const freqs=won?[523.25,659.25,783.99,1046.5]:[220,207.65,196,185];
    freqs.forEach((f,i)=>{ const o=c.createOscillator(),g=c.createGain();
      o.type=won?'triangle':'sawtooth'; o.frequency.value=f; g.gain.value=0.0;
      o.connect(g); g.connect(c.destination); o.start(c.currentTime+i*0.12);
      g.gain.setValueAtTime(0.12,c.currentTime+i*0.12);
      g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+i*0.12+(won?0.9:1.4));
      o.stop(c.currentTime+i*0.12+1.5); });}catch(e){} }

  const W=innerWidth,H=innerHeight;
  const r=new THREE.WebGLRenderer({antialias:true});
  r.setSize(W,H); r.outputEncoding=THREE.sRGBEncoding; r.setClearColor(0x050308);
  document.getElementById('v').appendChild(r.domElement);
  const sc=new THREE.Scene(); sc.fog=new THREE.FogExp2(0x050308,0.05);
  const cam=new THREE.PerspectiveCamera(42,W/H,0.1,80);
  cam.position.set(0,2.6,7.5); cam.lookAt(0,2.4,0);
  sc.add(new THREE.AmbientLight(0x9aa0ff,0.5));
  const key=new THREE.SpotLight(0xcfd4ff,2.6,50,Math.PI/3,0.5); key.position.set(0,12,6); sc.add(key);
  const under=new THREE.PointLight(0x6672ff,2.2,20); under.position.set(0,0.4,1.5); sc.add(under);
  const floor=new THREE.Mesh(new THREE.CircleGeometry(30,48),
    new THREE.MeshStandardMaterial({color:0x0a0712,metalness:.4,roughness:.85}));
  floor.rotation.x=-Math.PI/2; sc.add(floor);
  let mix=null,obj=null,entrance=0,actIdle=null,actHit=null;
  new THREE.GLTFLoader().load((window.__ORIGIN||'')+"__MODEL__",(g)=>{
    obj=g.scene;
    const b=new THREE.Box3().setFromObject(obj), sz=b.getSize(new THREE.Vector3());
    obj.scale.setScalar(0.15);
    obj.userData.fullScale=5.2/Math.max(sz.x,sz.y,sz.z,0.001);
    const b2=new THREE.Box3().setFromObject(obj), c=b2.getCenter(new THREE.Vector3());
    obj.position.set(-c.x,3.2,-c.z-1); sc.add(obj);
    if(g.animations&&g.animations.length){
      mix=new THREE.AnimationMixer(obj);
      const fi=g.animations.find(a=>/Flying_Idle/.test(a.name))||g.animations[0];
      const hb=g.animations.find(a=>/Headbutt|Punch/.test(a.name));
      actIdle=mix.clipAction(fi); actIdle.timeScale=0.85; actIdle.play();
      if(hb){ actHit=mix.clipAction(hb); actHit.setLoop(THREE.LoopOnce); actHit.timeScale=1.0; }
    }
    entrance=1;
  });
  
  
  
  
  
  function attack(){
    sndThud();
    document.getElementById('stage').classList.add('shake');
    setTimeout(()=>document.getElementById('stage').classList.remove('shake'),380);
    if(actHit&&actIdle){ actHit.reset().fadeIn(0.1).play(); actIdle.fadeOut(0.1);
      setTimeout(()=>{ actHit.fadeOut(0.2); actIdle.reset().fadeIn(0.2).play(); },900); }
  }
  // ---- quick-fire engine (all client-side, deterministic) ----
  const LINES_HIT=["Too slow. That answer is MINE now.","Wrong. I collect those, you know.",
    "Your teachers would weep, __HERO__.","Again you hesitate. Delicious."];
  const LINES_OK=["Hmph. Lucky.","Fine. Keep it.","Sharp. For now.","That one escapes me. Barely."];
  let qi=0,lives=3,score=0,cur=null,tleft=0,timerId=null;
  const QMAX=10,TIME=8;
  function newQ(){
    if(qi>=QMAX){ return end(true); }
    qi++;
    const kind=Math.random();
    let a2,b2,ans;
    if(kind<0.55){ a2=2+Math.floor(Math.random()*11); b2=2+Math.floor(Math.random()*11); ans=a2*b2;
      document.getElementById('qq').textContent=a2+" x "+b2+" = ?"; }
    else if(kind<0.8){ a2=11+Math.floor(Math.random()*79); b2=6+Math.floor(Math.random()*79); ans=a2+b2;
      document.getElementById('qq').textContent=a2+" + "+b2+" = ?"; }
    else { a2=30+Math.floor(Math.random()*69); b2=6+Math.floor(Math.random()*(a2-9)); ans=a2-b2;
      document.getElementById('qq').textContent=a2+" - "+b2+" = ?"; }
    cur=ans; tleft=TIME;
    const inp=document.getElementById('ans'); inp.value=''; inp.focus();
    clearInterval(timerId);
    timerId=setInterval(()=>{ tleft-=0.1;
      document.getElementById('tfill').style.width=Math.max(0,tleft/TIME*100)+'%';
      if(tleft<=0){ miss("Time's up. "); } },100);
  }
  function say(msg){ document.getElementById('bline').textContent=msg.replace(/__HERO__/g,"__HERO__"); }
  function miss(prefix){
    clearInterval(timerId); lives--; attack();
    const pips=document.querySelectorAll('.pip:not(.gone)');
    if(pips.length) pips[pips.length-1].classList.add('gone');
    say((prefix||"")+LINES_HIT[Math.floor(Math.random()*LINES_HIT.length)]+"  (answer: "+cur+")");
    if(lives<=0) return end(false);
    setTimeout(newQ,900);
  }
  function hit(){
    clearInterval(timerId); score++;
    say(LINES_OK[Math.floor(Math.random()*LINES_OK.length)]);
    setTimeout(newQ,500);
  }
  function submit(){
    const v=parseFloat(document.getElementById('ans').value);
    if(isNaN(v)) return;
    (v===cur)?hit():miss("");
  }
  document.getElementById('go2').onclick=submit;
  document.getElementById('ans').addEventListener('keydown',e=>{ if(e.key==='Enter') submit(); });
  function end(won){
    clearInterval(timerId);
    const ec=document.getElementById('endcard');
    sndEnd(won); ec.style.display='flex';
    document.getElementById('endtitle').textContent= won?"HE RETREATS":"COLLECTED";
    document.getElementById('endsub').textContent= won
      ? "\"Adequate... for now. Your basics are still yours, __HERO__. I will be back for the rest.\"  Score: "+score+" of "+QMAX
      : "\"Your basics belong to me now. Train with the little ones and buy them back.\"  Score: "+score+" of "+QMAX;
    document.getElementById('qbox').style.display='none';
  }
  let pt=0;
  (function loop(t){ requestAnimationFrame(loop);
    const tt=(t||0)*0.001, dt=Math.min(0.05,tt-pt); pt=tt;
    if(mix) mix.update(dt);
    if(obj){
      if(entrance>0&&entrance<2){ entrance+=dt*0.55;
        const k=Math.min(1,entrance-1+0.55);
        const fs=obj.userData.fullScale;
        const e2=Math.min(1,Math.max(0,(entrance-1)*1.4+0.4));
        obj.scale.setScalar(0.15+(fs-0.15)*e2);
        obj.position.y=3.2-1.4*e2;
      }
      obj.position.x=Math.sin(tt*0.35)*0.5;
      obj.rotation.y=Math.sin(tt*0.3)*0.2;
    }
    r.render(sc,cam); })(0);
  setTimeout(newQ,2600);
});
</script>
"""


def _boss_html(name):
    html = (_BOSS_TEMPLATE
            .replace("__VENDOR__", _vendor_js(["three.min.js", "GLTFLoader.js"]))
            .replace("__MODEL__", "/app/static/monsters/skull.glb"))
    return html.replace("__HERO__", _hescape(name))


_SKIRMISH_TEMPLATE = r"""
<style>
html,body{margin:0;background:#050308;overflow:hidden;font-family:'Trebuchet MS',sans-serif}
#stage{position:relative;width:100%;height:100vh}
#stage.shake{animation:sh .35s}
@keyframes sh{0%,100%{transform:none}20%{transform:translate(-9px,4px)}40%{transform:translate(8px,-5px)}60%{transform:translate(-6px,-3px)}80%{transform:translate(5px,3px)}}
#vig2{position:absolute;inset:0;pointer-events:none;z-index:3;
  background:radial-gradient(ellipse 70% 60% at 50% 40%,transparent 50%,rgba(2,1,4,.75) 85%,#020104 100%)}
#hud2{position:absolute;inset:0;z-index:5;pointer-events:none;color:#e8dfd2}
#btitle{position:absolute;top:14px;left:18px;font-size:1.5rem;font-weight:900;
  letter-spacing:.2em;color:#fff;text-shadow:0 0 18px __COLOR__}
#bsub{position:absolute;top:52px;left:19px;font-size:.7rem;letter-spacing:.16em;color:#8a86a8}
#lives{position:absolute;top:16px;right:18px;display:flex;gap:7px}
.pip{width:20px;height:20px;background:linear-gradient(135deg,#ff6b6b,#a8434f);
  border-radius:4px;transform:rotate(45deg);box-shadow:0 0 10px #ff6b6b88}
.pip.gone{background:#241a22;box-shadow:none}
#streakbox{position:absolute;top:52px;right:18px;font-size:.75rem;letter-spacing:.14em;
  color:__COLOR__;text-shadow:0 0 10px __COLOR__66;text-align:right}
#qbox{position:absolute;left:50%;bottom:30px;transform:translateX(-50%);
  width:min(480px,88%);text-align:center;pointer-events:auto}
#qq{font-size:2rem;font-weight:900;color:#fff;text-shadow:0 0 16px __COLOR__;margin-bottom:8px}
#timer{height:7px;background:#181226;border-radius:4px;overflow:hidden;margin:0 0 12px}
#tfill{height:100%;width:100%;background:linear-gradient(90deg,__COLOR__,#fff);transition:width .1s linear}
#ans{background:#120d1c;border:2px solid __COLOR__;border-radius:10px;color:#fff;
  font-size:1.4rem;text-align:center;width:150px;padding:9px;outline:none}
#go2{background:__COLOR__;border:none;border-radius:10px;color:#0a0714;font-weight:900;
  font-size:1rem;padding:12px 22px;margin-left:10px;cursor:pointer;letter-spacing:.1em}
#bline{position:absolute;left:50%;top:70px;transform:translateX(-50%);max-width:80%;
  background:rgba(10,7,18,.85);border:1px solid __COLOR__;border-radius:12px;
  padding:9px 15px;font-size:.95rem;color:#efe9ff;text-align:center;
  box-shadow:0 0 20px __COLOR__44}
#endcard{display:none;position:absolute;inset:0;z-index:6;align-items:center;justify-content:center;
  flex-direction:column;background:rgba(3,2,7,.72);text-align:center;padding:0 8%}
#endtitle{font-size:2.2rem;font-weight:900;letter-spacing:.16em;color:#fff;text-shadow:0 0 24px __COLOR__}
#endsub{margin-top:10px;color:#b9b4d6;font-size:1rem}
#coachlink{display:inline-block;margin-top:22px;pointer-events:auto;text-decoration:none;
  background:__COLOR__;color:#0a0714;font-weight:900;letter-spacing:.12em;
  border-radius:10px;padding:13px 26px;font-size:1rem;box-shadow:0 0 24px __COLOR__66}
</style>
<div id="stage">
  <div id="v"></div><div id="vig2"></div>
  <div id="hud2">
    <div id="btitle">__MONSTER__</div>
    <div id="bsub">LIEUTENANT OF THE COLLECTOR - WAR CLOCK 90s</div>
    <div id="lives"><div class="pip"></div><div class="pip"></div><div class="pip"></div></div>
    <div id="streakbox">STREAK 0 &middot; SCORE 0</div>
    <div id="bline">Ninety seconds, __HERO__. The Collector sent me to soften you up. Keep the numbers moving or lose them.</div>
    <div id="qbox">
      <div id="qq"></div>
      <div id="timer"><div id="tfill"></div></div>
      <input id="ans" inputmode="numeric" autocomplete="off">
      <button id="go2">STRIKE</button>
    </div>
  </div>
  <div id="endcard">
    <div id="endtitle"></div>
    <div id="endsub"></div>
    <a id="coachlink" target="_blank" rel="opener">GET COACHED BY GEMMA</a>
  </div>
</div>
<script>
(function(){ let o='';
  try{ o=window.parent.location.origin; }catch(e){ try{ o=new URL(document.referrer).origin; }catch(_){} }
  window.__ORIGIN=o; })();
</script>
__VENDOR__
<script>
window.addEventListener('load', function(){
  // procedural battle audio (no files): thud on hit, resolution chord at the end
  let __actx=null;
  function __a(){ if(!__actx) __actx=new (window.AudioContext||window.webkitAudioContext)(); return __actx; }
  function __gmMuted(){ try{ return localStorage.getItem('gm_mute')==='1'; }catch(e){ return false; } }
  function sndThud(){ if(__gmMuted()) return; try{ const c=__a(),o=c.createOscillator(),g=c.createGain();
    o.type='sine'; o.frequency.setValueAtTime(110,c.currentTime);
    o.frequency.exponentialRampToValueAtTime(38,c.currentTime+0.25);
    g.gain.setValueAtTime(0.5,c.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+0.3);
    o.connect(g); g.connect(c.destination); o.start(); o.stop(c.currentTime+0.32);}catch(e){} }
  function sndEnd(won){ if(__gmMuted()) return; try{ const c=__a();
    const freqs=won?[523.25,659.25,783.99,1046.5]:[220,207.65,196,185];
    freqs.forEach((f,i)=>{ const o=c.createOscillator(),g=c.createGain();
      o.type=won?'triangle':'sawtooth'; o.frequency.value=f; g.gain.value=0.0;
      o.connect(g); g.connect(c.destination); o.start(c.currentTime+i*0.12);
      g.gain.setValueAtTime(0.12,c.currentTime+i*0.12);
      g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+i*0.12+(won?0.9:1.4));
      o.stop(c.currentTime+i*0.12+1.5); });}catch(e){} }

  const W=innerWidth,H=innerHeight;
  const r=new THREE.WebGLRenderer({antialias:true});
  r.setSize(W,H); r.outputEncoding=THREE.sRGBEncoding; r.setClearColor(0x050308);
  document.getElementById('v').appendChild(r.domElement);
  const sc=new THREE.Scene(); sc.fog=new THREE.FogExp2(0x050308,0.05);
  const cam=new THREE.PerspectiveCamera(42,W/H,0.1,80);
  cam.position.set(0,2.6,7.5); cam.lookAt(0,2.4,0);
  const tint=new THREE.Color("__COLOR__");
  sc.add(new THREE.AmbientLight(0x9aa0ff,0.5));
  const key=new THREE.SpotLight(0xcfd4ff,2.6,50,Math.PI/3,0.5); key.position.set(0,12,6); sc.add(key);
  const under=new THREE.PointLight(tint,2.2,20); under.position.set(0,0.4,1.5); sc.add(under);
  const floor=new THREE.Mesh(new THREE.CircleGeometry(30,48),
    new THREE.MeshStandardMaterial({color:0x0a0712,metalness:.4,roughness:.85}));
  floor.rotation.x=-Math.PI/2; sc.add(floor);
  let mix=null,obj=null,entrance=0,actIdle=null,actHit=null;
  new THREE.GLTFLoader().load((window.__ORIGIN||'')+"__MODEL__",(g)=>{
    obj=g.scene;
    const b=new THREE.Box3().setFromObject(obj), sz=b.getSize(new THREE.Vector3());
    obj.scale.setScalar(0.15);
    obj.userData.fullScale=5.2/Math.max(sz.x,sz.y,sz.z,0.001);
    const b2=new THREE.Box3().setFromObject(obj), c=b2.getCenter(new THREE.Vector3());
    obj.position.set(-c.x,3.2,-c.z-1); sc.add(obj);
    if(g.animations&&g.animations.length){
      mix=new THREE.AnimationMixer(obj);
      const fi=g.animations.find(a=>/Flying_Idle/.test(a.name))
             ||g.animations.find(a=>/idle/i.test(a.name))||g.animations[0];
      const hb=g.animations.find(a=>/Headbutt|Punch/.test(a.name));
      actIdle=mix.clipAction(fi); actIdle.timeScale=0.85; actIdle.play();
      if(hb){ actHit=mix.clipAction(hb); actHit.setLoop(THREE.LoopOnce); actHit.timeScale=1.0; }
    }
    entrance=1;
  });
  function attack(){
    sndThud();
    document.getElementById('stage').classList.add('shake');
    setTimeout(()=>document.getElementById('stage').classList.remove('shake'),380);
    if(actHit&&actIdle){ actHit.reset().fadeIn(0.1).play(); actIdle.fadeOut(0.1);
      setTimeout(()=>{ actHit.fadeOut(0.2); actIdle.reset().fadeIn(0.2).play(); },900); }
  }
  // ---- skirmish engine: 90s war clock, streaks, three lanes ----
  const LANE="__LANE__", TOTAL=90;
  const LINES_HIT=["Snap. That one is ours now.","Wrong. The Collector pays me per mistake.",
    "Slower than the rumors said, __HERO__.","Feel that? That was a number leaving you."];
  const LINES_OK=["Tch. Faster than you look.","Keep it. For now.","One trick. Anyone can do one trick.",
    "The Collector will not be pleased with me, __HERO__."];
  function ri(a,b){ return a+Math.floor(Math.random()*(b-a+1)); }
  function evenIn(a,b){ let n=ri(a,b); if(n%2) n+=(n<b?1:-1); return n; }
  function tier(s){ return s<3?0:(s<6?1:2); }
  function genDoubles(t){
    if(t===0){ const n=ri(6,30); return {txt:"double "+n,key:"double "+n,ans:2*n}; }
    if(t===1){
      if(Math.random()<0.5){ const n=ri(31,80); return {txt:"double "+n,key:"double "+n,ans:2*n}; }
      const n=evenIn(40,160); return {txt:"half of "+n,key:"half "+n,ans:n/2};
    }
    const p=Math.random();
    if(p<0.4){ const n=ri(13,26); return {txt:"4 x "+n,key:"4x"+n,ans:4*n}; }
    if(p<0.7){ const n=evenIn(100,300); return {txt:"half of "+n,key:"half "+n,ans:n/2}; }
    const n=ri(60,140); return {txt:"double "+n,key:"double "+n,ans:2*n};
  }
  function genNines(t){
    if(t===0){
      if(Math.random()<0.5){ const n=ri(2,6); return {txt:"9 x "+n,key:"9x"+n,ans:9*n}; }
      const n=ri(12,40); return {txt:n+" + 9",key:n+"+9",ans:n+9};
    }
    if(t===1){
      const p=Math.random();
      if(p<0.35){ const n=ri(3,12); return {txt:"9 x "+n,key:"9x"+n,ans:9*n}; }
      if(p<0.6){ const n=ri(20,80);
        if(Math.random()<0.5) return {txt:n+" + 9",key:n+"+9",ans:n+9};
        return {txt:n+" - 9",key:n+"-9",ans:n-9}; }
      const n=ri(5,60); return {txt:"19 + "+n,key:"19+"+n,ans:19+n};
    }
    const p=Math.random();
    if(p<0.4){ const n=ri(6,65); return {txt:"29 + "+n,key:"29+"+n,ans:29+n}; }
    if(p<0.7){ const n=ri(30,95); return {txt:n+" - 9",key:n+"-9",ans:n-9}; }
    const n=ri(7,12); return {txt:"9 x "+n,key:"9x"+n,ans:9*n};
  }
  function crossPair(lo,hi){
    let a,b,i=0;
    do{ a=ri(lo,hi); b=ri(lo,hi); i++; }
    while(i<200&&((a%10)+(b%10)<10||a%10===0||b%10===0));
    return [a,b];
  }
  function genSplit(t){
    if(t===0){ const p=crossPair(12,48); return {txt:p[0]+" + "+p[1],key:p[0]+"+"+p[1],ans:p[0]+p[1]}; }
    if(t===1){ const p=crossPair(25,78); return {txt:p[0]+" + "+p[1],key:p[0]+"+"+p[1],ans:p[0]+p[1]}; }
    if(Math.random()<0.5){ const p=crossPair(35,89); return {txt:p[0]+" + "+p[1],key:p[0]+"+"+p[1],ans:p[0]+p[1]}; }
    let a,b,i=0;
    do{ a=ri(41,95); b=ri(13,a-12); i++; }
    while(i<200&&((b%10)<=(a%10)||b%10===0));
    if((b%10)<=(a%10)||b%10===0){ a=73; b=27; }
    return {txt:a+" - "+b,key:a+"-"+b,ans:a-b};
  }
  function gen(){
    const t=tier(streak);
    if(LANE==="doubles") return genDoubles(t);
    if(LANE==="nines") return genNines(t);
    return genSplit(t);
  }
  let lives=3,score=0,streak=0,best=0,cur=null,qShown=0,over=false;
  const misses=[],rts=[];
  let clock=TOTAL;
  const warId=setInterval(()=>{
    clock-=0.1;
    document.getElementById('tfill').style.width=Math.max(0,clock/TOTAL*100)+'%';
    if(clock<=0) end(true);
  },100);
  function hud(){
    document.getElementById('streakbox').innerHTML='STREAK '+streak+' &middot; SCORE '+score;
  }
  function say(msg){ document.getElementById('bline').textContent=msg; }
  function newQ(){
    if(over) return;
    cur=gen();
    document.getElementById('qq').textContent=cur.txt+" = ?";
    const inp=document.getElementById('ans'); inp.value=''; inp.focus();
    qShown=performance.now();
  }
  function clockRt(){ rts.push(Math.round((performance.now()-qShown)/100)*100); }
  function miss(prefix){
    if(over) return;
    clockRt(); misses.push(cur.key);
    lives--; streak=0; hud(); attack();
    const pips=document.querySelectorAll('.pip:not(.gone)');
    if(pips.length) pips[pips.length-1].classList.add('gone');
    say((prefix||"")+LINES_HIT[Math.floor(Math.random()*LINES_HIT.length)]+"  (answer: "+cur.ans+")");
    if(lives<=0) return end(false);
    setTimeout(newQ,900);
  }
  function hit(){
    if(over) return;
    clockRt(); score++; streak++; if(streak>best) best=streak; hud();
    say(LINES_OK[Math.floor(Math.random()*LINES_OK.length)]);
    setTimeout(newQ,400);
  }
  function submit(){
    if(over||!cur) return;
    const v=parseFloat(document.getElementById('ans').value);
    if(isNaN(v)) return miss("An empty strike. ");
    (v===cur.ans)?hit():miss("");
  }
  document.getElementById('go2').onclick=submit;
  document.getElementById('ans').addEventListener('keydown',e=>{ if(e.key==='Enter') submit(); });
  function end(won){
    if(over) return;
    over=true; clearInterval(warId);
    const ec=document.getElementById('endcard');
    sndEnd(won); ec.style.display='flex';
    document.getElementById('endtitle').textContent= won?"CLOCK SURVIVED":"OVERRUN";
    document.getElementById('endsub').textContent= won
      ? "\"The clock saved you, __HERO__. Not your speed.\"  Score: "+score+"  Best streak: "+best
      : "\"Three cracks and you fell. The Collector thanks you for the donation.\"  Score: "+score+"  Best streak: "+best;
    document.getElementById('qbox').style.display='none';
    let base='/';
    try{ base=window.parent.location.pathname||'/'; }
    catch(e){ try{ base=new URL(document.referrer).pathname||'/'; }catch(_){} }
    document.getElementById('coachlink').href=
      base+'?coach='+LANE
      +'&misses='+encodeURIComponent(misses.slice(0,8).join(','))
      +'&score='+score
      +'&streak='+best
      +'&hero='+encodeURIComponent(localStorage.getItem('gwb_hero')||'');
  }
  let pt=0;
  (function loop(t){ requestAnimationFrame(loop);
    const tt=(t||0)*0.001, dt=Math.min(0.05,tt-pt); pt=tt;
    if(mix) mix.update(dt);
    if(obj){
      if(entrance>0&&entrance<2){ entrance+=dt*0.55;
        const fs=obj.userData.fullScale;
        const e2=Math.min(1,Math.max(0,(entrance-1)*1.4+0.4));
        obj.scale.setScalar(0.15+(fs-0.15)*e2);
        obj.position.y=3.2-1.4*e2;
      }
      obj.position.x=Math.sin(tt*0.35)*0.5;
      obj.rotation.y=Math.sin(tt*0.3)*0.2;
    }
    r.render(sc,cam); })(0);
  setTimeout(newQ,2200);
});
</script>
"""


def _skirmish_html(name, lane, monster_model, color):
    lieutenants = {"doubles": "Twinfang", "nines": "The Niner", "split": "Splitjaw"}
    html = (_SKIRMISH_TEMPLATE
            .replace("__VENDOR__", _vendor_js(["three.min.js", "GLTFLoader.js"]))
            .replace("__MODEL__", monster_model)
            .replace("__COLOR__", color)
            .replace("__MONSTER__", lieutenants.get(lane, "Lieutenant").upper())
            .replace("__LANE__", lane))
    return html.replace("__HERO__", _hescape(name))


_LIEUTENANTS = {
    "doubles": {"monster": "Twinfang", "model": "/app/static/monsters/frog.glb",
                "color": "#4ade80",
                "whisper": "doubling: to double, add the number to itself; to multiply by 4, double twice. Halving undoes it."},
    "nines": {"monster": "The Niner", "model": "/app/static/monsters/alien.glb",
              "color": "#ffd166",
              "whisper": "nines: multiply by 10, then subtract the number once. Adding 9 is adding 10 then stepping back one."},
    "split": {"monster": "Splitjaw", "model": "/app/static/monsters/fish.glb",
              "color": "#35d0c0",
              "whisper": "make a ten: split the smaller number to complete a ten first. 47+38 is 47+3, then +35."},
}


def skirmish_stage():
    lane = st.session_state.get("skirmish_lane", "doubles")
    lt = _LIEUTENANTS[lane]
    st.markdown("""<style>
      [data-testid="stHeader"]{display:none}
      [data-testid="stMainBlockContainer"], .block-container{
        padding:0 0 1rem 0 !important; max-width:100% !important}
      [data-testid="stElementContainer"]:has(iframe){width:100% !important}
    </style>""", unsafe_allow_html=True)
    # Gemma whispers the mental strategy before the war (cached per lane)
    wkey = f"whisper_{lane}"
    if wkey not in st.session_state:
        try:
            from gemma_client import ask_gemma, plainify
            st.session_state[wkey] = plainify(ask_gemma(
                "TASK: explain\nIn TWO short sentences, teach a Grade 9 student the "
                f"mental-math trick of {lt['whisper']} Plain text, encouraging, no examples "
                "longer than one, address them as a warrior sharpening a blade.",
                max_new_tokens=90))
        except Exception:
            st.session_state[wkey] = lt["whisper"]
    note("GEMMA WHISPERS A WAR SECRET", esc_note(st.session_state[wkey]))
    components.html(_skirmish_html(st.session_state.get("player_name", "Challenger"),
                                   lane, lt["model"], lt["color"]),
                    height=560, scrolling=False)
    mid = st.columns([2, 2, 2])
    mid[1].button("Retreat to the nexus", key="sk_flee", on_click=back_to_map,
                  use_container_width=True)


def coach_stage():
    d = st.session_state.get("coach_data", {})
    lane = d.get("lane", "doubles")
    lt = _LIEUTENANTS[lane]
    st.markdown('<div class="gwb-kicker">After-battle debrief</div>', unsafe_allow_html=True)
    st.title("Gemma reads your battle")
    misses = [m for m in d.get("misses", []) if m]
    ck = f"coach_{lane}_{d.get('score')}_{len(misses)}"
    if ck not in st.session_state:
        try:
            from gemma_client import ask_gemma, plainify
            st.session_state[ck] = plainify(ask_gemma(
                "TASK: coach\nYou are a sharp, kind mental-math coach. A Grade 9 student "
                f"named {st.session_state.get('player_name', 'Challenger')} just fought a "
                f"90-second speed battle on the skill: {lane}. Score {d.get('score')} correct, "
                f"best streak {d.get('streak')}. The exact questions they MISSED: "
                f"{', '.join(misses) if misses else 'none - a clean sweep'}.\n"
                "In plain text (no LaTeX): (1) name the specific pattern you see in those "
                "misses in one sentence; (2) teach the ONE mental trick that fixes it, in two "
                "sentences; (3) give a mini drill of exactly three practice questions of that "
                "type (questions only, no answers). If they missed nothing, congratulate them "
                "and raise the challenge with three harder questions of the same skill.",
                max_new_tokens=320))
        except Exception:
            st.session_state[ck] = ("Your speed is building. Drill the ones that got away: "
                                    + (", ".join(misses) if misses else "raise the difficulty next run."))
    with st.container(border=True):
        st.markdown(esc(st.session_state[ck]))
    c = st.columns(3)
    c[0].button("Rematch " + lt["monster"], key="coach_rematch",
                on_click=lambda: st.session_state.update(stage="skirmish", skirmish_lane=lane),
                use_container_width=True)
    c[1].button("Back to the nexus", key="coach_home", on_click=back_to_map,
                use_container_width=True)


_FINALE_TEMPLATE = r"""
<style>
html,body{margin:0;background:#050308;overflow:hidden;font-family:'Trebuchet MS',sans-serif}
#stage{position:relative;width:100%;height:100vh}
#hud3{position:absolute;inset:0;z-index:5;pointer-events:none;color:#f3e5ab;text-align:center}
#ftitle{position:absolute;top:7%;width:100%;font-size:2rem;font-weight:900;letter-spacing:.22em;
  text-shadow:0 0 24px rgba(226,192,125,.8);opacity:0;transition:opacity 3s}
#fsub{position:absolute;bottom:9%;width:100%;font-size:1rem;color:#d9ceb4;opacity:0;transition:opacity 3s}
</style>
<div id="stage"><div id="v"></div>
  <div id="hud3">
    <div id="ftitle">THE SEAL BREAKS</div>
    <div id="fsub">Five tricks defeated. The gate opens, __HERO__ — the one they kept from you steps into the light.</div>
  </div>
</div>
<script>
(function(){ let o='';
  try{ o=window.parent.location.origin; }catch(e){ try{ o=new URL(document.referrer).origin; }catch(_){} }
  window.__ORIGIN=o; })();
</script>
__VENDOR__
<script>
window.addEventListener('load', function(){
  const W=innerWidth,H=innerHeight;
  const r=new THREE.WebGLRenderer({antialias:true});
  r.setSize(W,H); r.outputEncoding=THREE.sRGBEncoding;
  r.toneMapping=THREE.ACESFilmicToneMapping; r.toneMappingExposure=0.9;
  r.setClearColor(0x050308);
  document.getElementById('v').appendChild(r.domElement);
  const sc=new THREE.Scene(); sc.fog=new THREE.FogExp2(0x0d1424,0.02);
  const cam=new THREE.PerspectiveCamera(46,W/H,0.1,120);
  cam.position.set(0,4,26); cam.lookAt(0,4,0);
  sc.add(new THREE.AmbientLight(0x141c30,0.9));
  const moon=new THREE.DirectionalLight(0x9fb6e8,1.0); moon.position.set(-20,30,-10); sc.add(moon);

  const stone=new THREE.MeshStandardMaterial({color:0x2a2d36,roughness:.7,metalness:.2});
  const ground=new THREE.Mesh(new THREE.PlaneGeometry(120,120),
    new THREE.MeshStandardMaterial({color:0x121722,roughness:.9}));
  ground.rotation.x=-Math.PI/2; sc.add(ground);

  // the gate wall
  const wallL=new THREE.Mesh(new THREE.BoxGeometry(14,16,2),stone); wallL.position.set(-10.5,8,0); sc.add(wallL);
  const wallR=new THREE.Mesh(new THREE.BoxGeometry(14,16,2),stone); wallR.position.set(10.5,8,0); sc.add(wallR);
  const arch=new THREE.Mesh(new THREE.BoxGeometry(8,4,2),stone); arch.position.set(0,14,0); sc.add(arch);

  // double doors
  const doorMat=new THREE.MeshStandardMaterial({color:0x2b1e16,roughness:.8});
  const doorL=new THREE.Group(), doorR=new THREE.Group();
  const dL=new THREE.Mesh(new THREE.BoxGeometry(3.5,12,0.5),doorMat); dL.position.x=1.75; doorL.add(dL);
  const dR=new THREE.Mesh(new THREE.BoxGeometry(3.5,12,0.5),doorMat); dR.position.x=-1.75; doorR.add(dR);
  doorL.position.set(-3.5,6,0); doorR.position.set(3.5,6,0);
  sc.add(doorL); sc.add(doorR);

  // light inside the keep
  const innerGlow=new THREE.PointLight(0xffe9b0,0,40); innerGlow.position.set(0,6,-4); sc.add(innerGlow);

  // the freed one: a glowing faceless figure (placeholder until the hero model arrives)
  const figMat=new THREE.MeshStandardMaterial({color:0xffe9b0,emissive:0xffd98c,
    emissiveIntensity:1.2,roughness:.4});
  const fig=new THREE.Group();
  const body=new THREE.Mesh(new THREE.CapsuleGeometry?new THREE.CapsuleGeometry(0.7,1.6,8,16):new THREE.CylinderGeometry(0.7,0.7,2.6,16),figMat);
  body.position.y=2.2; fig.add(body);
  const head=new THREE.Mesh(new THREE.SphereGeometry(0.55,20,20),figMat);
  head.position.y=4.0; fig.add(head);
  const halo=new THREE.PointLight(0xffe9b0,2.5,16); halo.position.y=3.4; fig.add(halo);
  fig.position.set(0,0,-3); fig.scale.setScalar(0.001); sc.add(fig);

  // golden particles
  const N=220, g2=new THREE.BufferGeometry(), pp=new Float32Array(N*3);
  for(let i=0;i<N;i++){ pp[i*3]=(Math.random()-0.5)*30; pp[i*3+1]=Math.random()*14;
    pp[i*3+2]=(Math.random()-0.5)*20; }
  g2.setAttribute('position',new THREE.BufferAttribute(pp,3));
  const stars=new THREE.Points(g2,new THREE.PointsMaterial({color:0xffd98c,size:0.14,
    transparent:true,opacity:0.0,blending:THREE.AdditiveBlending}));
  sc.add(stars);

  // gentle victory chord (procedural)
  function chord(){ try{
    const c=new (window.AudioContext||window.webkitAudioContext)();
    [261.6,329.6,392.0,523.25].forEach((f,i)=>{
      const o=c.createOscillator(),g=c.createGain();
      o.type='triangle'; o.frequency.value=f; g.gain.value=0;
      o.connect(g); g.connect(c.destination); o.start(c.currentTime+i*0.25);
      g.gain.setValueAtTime(0.1,c.currentTime+i*0.25);
      g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+i*0.25+2.4);
      o.stop(c.currentTime+i*0.25+2.5); });}catch(e){} }

  // cinematic timeline
  setTimeout(()=>{ gsap.to(doorL.rotation,{y:-1.9,duration:4,ease:"power2.inOut"});
    gsap.to(doorR.rotation,{y:1.9,duration:4,ease:"power2.inOut"});
    gsap.to(innerGlow,{intensity:5,duration:4}); chord(); },1200);
  setTimeout(()=>{ gsap.to(fig.scale,{x:1,y:1,z:1,duration:2.5,ease:"back.out(1.4)"});
    gsap.to(fig.position,{z:5,duration:6,ease:"power1.inOut"});
    gsap.to(stars.material,{opacity:0.85,duration:3});
    document.getElementById('ftitle').style.opacity=1; },3600);
  setTimeout(()=>{ document.getElementById('fsub').style.opacity=1; },6500);

  let pt=0;
  (function loop(t){ requestAnimationFrame(loop);
    const tt=(t||0)*0.001, dt=Math.min(0.05,tt-pt); pt=tt;
    fig.position.y=Math.sin(tt*1.2)*0.15;
    fig.rotation.y=Math.sin(tt*0.4)*0.2;
    stars.rotation.y+=dt*0.03;
    r.render(sc,cam); })(0);
});
</script>
"""


def _finale_html(name):
    return (_FINALE_TEMPLATE
            .replace("__VENDOR__", _vendor_js(["three.min.js", "gsap.min.js"]))
            .replace("__HERO__", _hescape(name)))


def finale_stage():
    st.markdown("""<style>
      [data-testid="stHeader"]{display:none}
      [data-testid="stMainBlockContainer"], .block-container{
        padding:0 0 1rem 0 !important; max-width:100% !important}
      [data-testid="stElementContainer"]:has(iframe){width:100% !important}
    </style>""", unsafe_allow_html=True)
    components.html(_finale_html(st.session_state.get("player_name", "Challenger")),
                    height=620, scrolling=False)
    mid = st.columns([2, 2, 2])
    mid[1].button("Return to the nexus", key="fin_home", on_click=back_to_map,
                  use_container_width=True)


def boss_stage():
    st.markdown("""<style>
      [data-testid="stHeader"]{display:none}
      [data-testid="stMainBlockContainer"], .block-container{
        padding:0 0 1rem 0 !important; max-width:100% !important}
      [data-testid="stElementContainer"]:has(iframe){width:100% !important}
    </style>""", unsafe_allow_html=True)
    components.html(_boss_html(st.session_state.get("player_name", "Challenger")),
                    height=620, scrolling=False)
    mid = st.columns([2, 2, 2])
    mid[1].button("Retreat to the nexus", key="boss_flee", on_click=back_to_map,
                  use_container_width=True)
    st.markdown('<div style="text-align:center;letter-spacing:.14em;font-size:.72rem;'
                'color:#8a86a8;font-weight:700;margin-top:6px">OR SHARPEN YOUR SPEED AGAINST HIS LIEUTENANTS</div>',
                unsafe_allow_html=True)
    lc = st.columns(3)
    for _i, (_lane, _lt) in enumerate(_LIEUTENANTS.items()):
        lc[_i].button(_lt["monster"], key=f"lt_{_lane}",
                      on_click=lambda l=_lane: st.session_state.update(stage="skirmish", skirmish_lane=l),
                      use_container_width=True)
    if "msession" in st.session_state:
        mid[1].button("Back to training", key="boss_train",
                      on_click=lambda: st.session_state.update(stage="mastery"),
                      use_container_width=True)


def _encounter_html(mon, name):
    # .replace, not .format: one line is Gemma-written, and stray braces in
    # model output would crash str.format for the whole encounter
    lines = [ln.replace("{name}", name) for ln in mon.get("lines", [mon.get("taunt", "...")])]
    return (_ENCOUNTER_TEMPLATE
            .replace("__VENDOR__", _vendor_js(["three.min.js", "GLTFLoader.js"]))
            .replace("__MODEL__", mon["model"])
            .replace("__COLOR__", mon["color"])
            .replace("__NAME__", mon["monster"].upper())
            .replace("__ECLIP__", mon.get("clip_ambient", ""))
            .replace("__ETS__", str(mon.get("sp_ambient", 0.8)))
            .replace("__LINES__", json.dumps(lines)))


def encounter_stage():
    strand = st.session_state.get("enc_strand")
    mon = monster_for(strand)
    if not mon:
        back_to_map(); st.rerun()
    st.markdown("""<style>
      [data-testid="stHeader"]{display:none}
      [data-testid="stMainBlockContainer"], .block-container{
        padding:0 0 1rem 0 !important; max-width:100% !important}
      [data-testid="stElementContainer"]:has(iframe){width:100% !important}
    </style>""", unsafe_allow_html=True)
    mem_key = f"enc_line_{strand}"
    if mem_key not in st.session_state:
        facts = {
            "mastered_tricks": st.session_state.get("mastered_names", []),
            "defeated_monsters": [r.get("monster", "") for r in st.session_state.get("relics", [])],
            "last_score": st.session_state.get("last_score", ""),
            "attempts_here": st.session_state.get(f"visits_{strand}", 0),
        }
        st.session_state[f"visits_{strand}"] = facts["attempts_here"] + 1
        if any([facts["mastered_tricks"], facts["defeated_monsters"], facts["last_score"]]):
            with st.spinner("It recognizes you..."):
                st.session_state[mem_key] = rewards.battle_memory_line(
                    st.session_state.get("player_name", "Challenger"),
                    mon["monster"], facts)
        else:
            st.session_state[mem_key] = ""
    mon_l = dict(mon)
    if st.session_state.get(mem_key):
        mon_l["lines"] = [st.session_state[mem_key]] + list(mon.get("lines", []))
    components.html(_encounter_html(mon_l, st.session_state.get("player_name", "Challenger")),
                    height=520, scrolling=False)
    mid = st.columns([2, 2, 2])
    if mid[1].button(f"FACE {mon['monster'].upper()}", type="primary",
                     use_container_width=True, key="enc_go"):
        st.session_state.quiz = pick_quiz(strand, 5)
        st.session_state.answers = {}
        st.session_state.stage = "quiz"
        st.rerun()
    mid[1].button("Retreat to the nexus", key="enc_flee", on_click=back_to_map,
                  use_container_width=True)


def back_to_map():
    for k in ("quiz", "answers", "guides", "mastered", "teacher_report", "escal_report",
              "msession", "mprobe", "mlesson", "mlesson_why", "mfeedback", "mtranscript"):
        st.session_state.pop(k, None)
    st.session_state.stage = "map"


def map_stage():
    # full-bleed: strip Streamlit chrome so the game IS the screen (this stage only)
    st.markdown("""<style>
      [data-testid="stHeader"]{display:none}
      [data-testid="stMainBlockContainer"], .block-container{
        padding:0 !important; max-width:100% !important}
      [data-testid="stAppViewContainer"]{background:#0b0710}
      [data-testid="stElementContainer"]:has(iframe){width:100% !important}
    </style>""", unsafe_allow_html=True)
    components.html(_hub_html(), height=800, scrolling=False)


# ---------------- QUIZ ----------------
def quiz():
    if st.session_state.get("adventure"):
        strand0 = st.session_state.quiz[0]["strand"] if st.session_state.get("quiz") else None
        mon = MONSTERS.get(strand0)
        st.markdown('<div class="gwb-kicker">GEMMA MONSTERS</div>', unsafe_allow_html=True)
        st.title(f"Face {mon['monster']}" if mon else "The Challenge")
        if mon:
            # markdown turns indented HTML into a code block - keep this flush-left
            taunt_html = (
                '<style>'
                '[data-testid="stElementContainer"]:has(iframe) {'
                'position:fixed; bottom:14px; right:14px; width:180px !important;'
                'z-index:998; margin:0;'
                f'filter:drop-shadow(0 0 14px {mon["color"]}66);'
                'animation:gwbBob 3.2s ease-in-out infinite}'
                '</style>'
                '<div class="gwb-taunt" style="bottom:190px;right:18px">'
                f'<div class="gwb-bubble"><strong>{mon["monster"]}:</strong> '
                f'{mon.get("taunt", "")}</div></div>'
            )
            st.markdown(taunt_html, unsafe_allow_html=True)
            components.html(_taunt_html(mon["model"],
                                        mon.get("clip_ambient", ""),
                                        mon.get("sp_ambient", 0.8) * 0.85), height=170)
        st.caption("Answer every question, then submit. Wrong answers feed the monster.")
        st.button("Back to the nexus", key="quiz_to_nexus", on_click=back_to_map)
    else:
        st.title("Quiz")
        st.caption("Answer every question, then submit.")
    for i, q in enumerate(st.session_state.quiz, 1):
        st.markdown(f"**{i}. {esc(q['question'])}**")
        labels = [o["label"] for o in q["options"]]
        choice = st.radio(
            f"q_{q['id']}",
            labels,
            format_func=lambda l, q=q: f"{l})  " + esc(next(o['text'] for o in q['options'] if o['label'] == l)),
            index=None,
            key=f"radio_{q['id']}",
            label_visibility="collapsed",
        )
        st.session_state.answers[q["id"]] = choice
        st.divider()

    answered = sum(1 for q in st.session_state.quiz if st.session_state.answers.get(q["id"]))
    st.progress(answered / len(st.session_state.quiz), text=f"{answered} of {len(st.session_state.quiz)} answered")
    if st.button("Submit", type="primary", disabled=answered < len(st.session_state.quiz)):
        st.session_state.stage = "results"
        st.rerun()


# ---------------- RESULTS ----------------
def results():
    if "quiz" not in st.session_state:
        back_to_map()
        st.rerun()
    result = agent.grade_quiz(st.session_state.quiz, st.session_state.answers)
    analysis = agent.analyze(result)

    if st.session_state.get("adventure"):
        st.markdown('<div class="gwb-kicker">GEMMA MONSTERS</div>', unsafe_allow_html=True)
        st.title("The Battle Report")
    else:
        st.title("Results")
    st.session_state.last_score = f"{result['correct']} of {result['total']}"
    st.metric("Score", f"{result['correct']} / {result['total']}",
              f"{result['score_pct']}%", delta_color="off")

    if not result["wrong"]:
        st.write("A perfect score — nothing got past you this time.")
        st.button("Take another quiz", key="again_perfect", on_click=reset)
        return

    # --- the agent's decision: what matters most ---
    priority = analysis["priority"]
    mastered = st.session_state.get("mastered", set())
    adventure = st.session_state.get("adventure")
    if adventure and priority and priority["id"] not in mastered and result["wrong"]:
        strand = result["wrong"][0]["item"]["strand"]
        mon = monster_for(strand)
        if mon:
            bcols = st.columns([1, 3])
            with bcols[0]:
                components.html(_taunt_html(mon["model"],
                                            clip_pref=mon.get("clip_fight", ""),
                                            speed=mon.get("sp_fight", 0.7)), height=175)
            with bcols[1]:
                st.markdown(
                    f'<div style="border-left:3px solid {mon["color"]};padding:6px 0 6px 16px;'
                    f'margin-top:14px">'
                    f'<div style="font-size:.72rem;letter-spacing:.16em;color:{mon["color"]};'
                    f'font-weight:700">A GEMMA MONSTER GOT YOU</div>'
                    f'<div style="font-size:1.55rem;color:#ffefdd;font-weight:900;'
                    f'text-transform:uppercase">{mon["monster"]} strikes!</div>'
                    f'<div style="color:#cbb8a4;font-size:.95rem">It feeds on '
                    f'<strong style="color:#ffefdd">{priority["name"].lower()}</strong> '
                    f'— learn its weakness below and defeat it.</div></div>',
                    unsafe_allow_html=True)
    if priority and priority["id"] in mastered:
        note(
            "Mastered",
            f"You've closed your main gap — <strong>{priority['name']}</strong>. "
            "Well done.",
        )
        st.write("Not feeling fully confident yet? Take another quiz to prove it sticks.")
        st.button("Take another quiz", type="primary", key="again_top", on_click=reset)
    elif priority:
        n = priority["count"]
        reason = (f"you missed it {n} times — more than any other gap"
                  if len(analysis["patterns"]) > 1 and n > 1
                  else f"it's the clearest gap in your answers")
        note(
            "Why the agent starts here",
            f"Your main gap is <strong>{priority['name']}</strong>. The agent tackles this "
            f"first because {reason}. The study guide starts there.",
        )
        st.button(
            ("Defeat the monster — practice to mastery"
             if st.session_state.get("adventure") else "Practice until I've mastered it"),
            type="primary",
            on_click=start_mastery, args=(result, analysis),
            help="The agent keeps teaching and checking, switching approaches "
                 "when one doesn't land, until you get two in a row right.",
        )
    # only nudge the parents when the main gap is still open
    if analysis["escalate"] and not (priority and priority["id"] in mastered):
        note(
            "For mum and dad to see",
            "Several questions were missed. The agent writes your parents a report they "
            "can act on — not just a score.",
        )
        with st.expander("See the report for mum and dad", expanded=True):
            if "teacher_report" not in st.session_state:
                with st.spinner("Writing a note your parents can act on..."):
                    st.session_state.teacher_report = agent.teacher_report(result, analysis)
            with st.container(border=True):
                st.markdown(st.session_state.teacher_report)
            st.download_button("Download report", st.session_state.teacher_report,
                               file_name="parent_report.md", key="dl_teacher")

    # --- a study-guide card per missed question ---
    st.subheader("Your study guide")
    if "guides" not in st.session_state:
        fight_ph = st.empty()
        if st.session_state.get("adventure") and result["wrong"]:
            try:
                fmon = monster_for(result["wrong"][0]["item"]["strand"])
                if fmon:
                    with fight_ph.container():
                        components.html(
                            _fight_html(fmon, result["correct"], result["total"]),
                            height=240)
            except Exception:
                pass  # the mini-fight must never break the results page
        with st.spinner("The agent is studying your mistakes and writing your guide..."):
            seen = {q["id"] for q in st.session_state.quiz}
            st.session_state.guides = agent.build_study_guides(result, QUESTIONS, seen_ids=seen)
        fight_ph.empty()
    for i, guide in enumerate(st.session_state.guides):
        with st.container(border=True):
            st.markdown(f"**{esc(guide['question'])}**")
            st.markdown(f"You picked **{esc(guide['chosen'])}** — the correct answer is **{esc(guide['correct'])}**")
            if guide["trick"].get("name"):
                gmon = monster_for(guide["strand"]) if st.session_state.get("adventure") else None
                if gmon:
                    st.markdown(
                        f"<div style='font-size:.85rem;color:#8a8378'>"
                        f"<span style='color:{gmon['color']};font-size:1rem'>&#9670;</span> "
                        f"<strong style='color:{gmon['color']}'>{gmon['monster']}</strong>"
                        f"&nbsp;&middot;&nbsp;{guide['trick']['name']}</div>",
                        unsafe_allow_html=True)
                else:
                    st.caption(f"The trick that got you: {guide['trick']['name']}")
            st.markdown("**Why:** " + esc(guide["explanation"]))
            if guide["worked_solution"]:
                with st.expander("See the worked solution"):
                    st.markdown(steps_md(guide["worked_solution"]))

            # --- interactive "Now you try" ---
            p = guide["practice"]
            challenge_title = (f"{gmon['monster']}'s next challenge — "
                               f"let's see you slip this time:" if gmon else "Now you try:")
            st.markdown(f"**{challenge_title}** " + esc(p["question"]))
            if not p.get("options"):
                st.caption("Work it out on paper — then prove it in the training grounds."
                           if st.session_state.get("adventure")
                           else "Work it out on paper — then check it in practice mode above.")
            if p.get("options"):
                choice = st.radio(
                    f"practice_{i}",
                    [o["label"] for o in p["options"]],
                    format_func=lambda l, p=p: f"{l})  " + esc(next(
                        o["text"] for o in p["options"] if o["label"] == l)),
                    index=None, key=f"practice_{i}", label_visibility="collapsed",
                )
                # a hint (a nudge, never the answer) is available before attempting
                if guide.get("hint"):
                    with st.expander("Stuck? Show a hint"):
                        st.markdown(esc(guide["hint"]))
                # feedback + the full worked solution appear ONLY after an attempt,
                # so the answer isn't handed over before the student tries
                if choice:
                    if choice == p["correct"]:
                        note("Correct", "That's exactly it.")
                    else:
                        o = next(o for o in p["options"] if o["label"] == choice)
                        trap = o.get("trick_name")
                        note("Not quite",
                             f"That's the <strong>{trap}</strong> trap again — "
                             "open a hint and try once more." if trap else
                             "Take another look, or open a hint.")
                    if p.get("solution"):
                        with st.expander("See this one worked out"):
                            st.markdown(steps_md(p["solution"]))

    if st.session_state.get("adventure"):
        st.button("Back to the nexus", key="tomap_bottom", on_click=back_to_map)
    st.button("Take another quiz", key="again_bottom", on_click=reset)


# ---------------- MASTERY LOOP ----------------
def check_answer():
    s = st.session_state.msession
    probe = st.session_state.mprobe
    chosen = st.session_state.get("mastery_choice")
    if not chosen:
        return
    explanation = st.session_state.get("mastery_reason", "")

    with st.spinner("The agent is reading your answer..."):
        outcome = m.submit_answer(s, probe, chosen, explanation)
    st.session_state.mfeedback = outcome
    if outcome["state"] == m.IN_PROGRESS:
        with st.spinner("The agent is deciding what to try next..."):
            if outcome["strategy_changed"]:
                st.session_state.mlesson = m.teach(s)
                st.session_state.mlesson_why = (
                    outcome.get("strategy_why")
                    or f"Trying a different approach: {s.strategy_name}.")
            st.session_state.mprobe = m.next_probe(s, QUESTIONS)
    st.session_state.pop("mastery_choice", None)
    st.session_state.pop("mastery_reason", None)


def mastery_stage():
    if "msession" not in st.session_state:
        # nothing to train (e.g. arrived from the boss debug route) - go home
        back_to_map()
        st.rerun()
    s = st.session_state.msession
    st.markdown('<div class="gwb-kicker">' +
                ("GEMMA MONSTERS · TRAINING GROUNDS" if st.session_state.get("adventure")
                 else "Autonomous practice") + '</div>', unsafe_allow_html=True)
    st.title(("Defeat the trick: " if st.session_state.get("adventure") else "Mastering: ")
             + s.trick_name)

    # one quiet status line + an escape hatch while practising
    if s.state == m.IN_PROGRESS:
        st.caption(f"Attempt {s.attempts + 1} of {m.MAX_ATTEMPTS} · "
                   f"{s.strategy_name} · streak {s.consecutive_correct} of {m.MASTERY_BAR}")
        st.button("← Back to results", key="leave_practice",
                  on_click=lambda: st.session_state.update(stage="results"),
                  help="Leave practice — you can start it again from your results anytime.")

    # terminal screens
    if s.state == m.MASTERED:
        # remember it: the results page now shows this gap as closed
        st.session_state.setdefault("mastered", set()).add(s.trick_id)
        st.session_state.setdefault("mastered_names", []).append(s.trick_name)
        st.session_state.setdefault("defeated_strands", set()).add(s.strand)
        relic_key = f"relic_{s.trick_id}"
        if relic_key not in st.session_state:
            gmon = monster_for(s.strand) or {}
            tried = [h["strategy"] for h in s.history if h["kind"] == "lesson"]
            with st.spinner("The monster drops something..."):
                st.session_state[relic_key] = rewards.forge_relic(
                    st.session_state.get("player_name", "Challenger"),
                    gmon.get("monster", "the monster"), s.trick_name,
                    s.attempts, tried)
            st.session_state.setdefault("relics", []).append(
                {**st.session_state[relic_key], "monster": gmon.get("monster", "")})
        _relic = st.session_state[relic_key]
        note("IT DROPS A RELIC",
             f"<strong>{_relic['name']}</strong> — {_relic['power']}")
        if len(st.session_state.get("defeated_strands", set())) >= 5:
            note("THE FIFTH SEAL SHATTERS",
                 "Across the citadel, the gate is opening. Someone is waiting for you.")
            st.button("GO TO THE GATE", type="primary", key="to_finale",
                      on_click=lambda: st.session_state.update(stage="finale"))
        note("Why the agent declared mastery",
             "Two fresh questions in a row, answered correctly — and your reasoning showed "
             "real understanding, not a lucky guess. That's the evidence bar for mastery.")
        st.code(m.mastery_recap(s))
        st.button("Back to my results", key="back_mastered",
                  on_click=lambda: st.session_state.update(stage="results"))
        st.button("Take another quiz", key="again_mastered", on_click=reset)
        return
    if s.state == m.ESCALATED:
        if st.session_state.get("adventure"):
            # the whispered warning comes true
            note("THE AIR GOES COLD",
                 "The little monsters have gone silent. Something older has noticed "
                 f"how many answers you've dropped, "
                 f"{_hescape(st.session_state.get('player_name', 'Challenger'))}. "
                 "<strong>The Collector is here.</strong>")
            st.button("FACE THE COLLECTOR — the speed trial", type="primary",
                      key="boss_go",
                      on_click=lambda: st.session_state.update(stage="boss"))
        note("For mum and dad to see",
             "The agent tried every approach it has. Time for a human — here is a report "
             "your parents can act on, informed by what already didn't work.")
        if "escal_report" not in st.session_state:
            with st.spinner("Writing a note your parents can act on..."):
                st.session_state.escal_report = m.escalation_report(s)
        with st.container(border=True):
            st.markdown(st.session_state.escal_report)
        st.download_button("Download report", st.session_state.escal_report,
                           file_name="parent_report.md", key="dl_escal")
        st.button("Back to my results", key="back_escalated",
                  on_click=lambda: st.session_state.update(stage="results"))
        st.button("Take another quiz", key="again_escalated", on_click=reset)
        return

    # feedback from the previous answer
    fb = st.session_state.get("mfeedback")

    if fb and fb.get("reaction"):
        # Gemma read the student's own typed words and answers them directly
        note("The citadel heard you", esc_note(fb["reaction"]))
    if fb and fb.get("rationale"):
        # explainable AI: every decision shows its evidence-based "why"
        headline = ("Correct" if fb["correct"] and fb.get("label") == "RESOLVED"
                    else "Right answer — but not yet" if fb["correct"]
                    else "Not yet")
        note(f"Why the agent decided this · {headline}", esc_note(fb["rationale"]))

    # the lesson for the current strategy, with the reason this approach was chosen
    with st.container(border=True):
        st.caption(f"Lesson — {s.strategy_name}")
        st.markdown(esc(st.session_state.mlesson))
        if st.session_state.get("mlesson_why"):
            st.caption("Why this approach: " + esc(st.session_state.mlesson_why))

    # the probe
    probe = st.session_state.mprobe
    if probe is None:
        s.state = m.ESCALATED
        s.escalation_reason = "no fresh check question available"
        st.rerun()
    st.markdown(f"**Check yourself: {esc(probe['question'])}**")
    st.radio(
        "mastery probe",
        [o["label"] for o in probe["options"]],
        format_func=lambda l: f"{l})  " + esc(next(o["text"] for o in probe["options"] if o["label"] == l)),
        index=None,
        key="mastery_choice",
        label_visibility="collapsed",
    )
    st.text_input(
        "In one line: how did you get your answer? (optional — the agent reads it and answers back)",
        key="mastery_reason",
        placeholder="e.g. I found a common denominator of 12, then added the tops",
    )

    st.button("Check my answer", type="primary", on_click=check_answer,
              disabled=st.session_state.get("mastery_choice") is None)


# ---------------- ROUTER ----------------
# Stepping through a maze portal navigates here with ?station=<strand>; turn that
# into the real quiz for that strand (survives the reload — a quiz needs no prior state).
if st.query_params.get("exit"):
    st.query_params.clear()
    to_dashboard()
_station = st.query_params.get("station")
if _station in STATIONS:
    st.session_state.adventure = True
    hero = (st.query_params.get("hero") or "").strip()
    if hero:
        st.session_state.player_name = hero[:24]
    # the monster confronts you before its trial begins
    st.session_state.enc_strand = _station
    st.session_state.stage = "encounter"
    st.query_params.clear()

if st.query_params.get("finale"):
    st.session_state.adventure = True
    st.session_state.stage = "finale"
    st.query_params.clear()
if st.query_params.get("boss"):
    st.session_state.adventure = True
    st.session_state.stage = "boss"
    st.query_params.clear()
_skl = st.query_params.get("skirmish")
if _skl in ("doubles", "nines", "split"):
    st.session_state.adventure = True
    hero = (st.query_params.get("hero") or "").strip()
    if hero:
        st.session_state.player_name = hero[:24]
    st.session_state.skirmish_lane = _skl
    st.session_state.stage = "skirmish"
    st.query_params.clear()
_cl = st.query_params.get("coach")
if _cl in ("doubles", "nines", "split"):
    st.session_state.adventure = True
    st.session_state.coach_data = {
        "lane": _cl,
        "misses": (st.query_params.get("misses") or "").split(",")[:8],
        "score": st.query_params.get("score") or "0",
        "streak": st.query_params.get("streak") or "0",
    }
    hero = (st.query_params.get("hero") or "").strip()
    if hero:
        st.session_state.player_name = hero[:24]
    st.session_state.stage = "coach"
    st.query_params.clear()

stage = st.session_state.get("stage", "intro")
{"intro": intro, "map": map_stage, "encounter": encounter_stage, "quiz": quiz,
 "results": results, "mastery": mastery_stage, "boss": boss_stage,
 "skirmish": skirmish_stage, "coach": coach_stage, "finale": finale_stage}[stage]()
