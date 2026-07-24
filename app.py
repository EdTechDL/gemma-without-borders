"""
app.py  —  Gemma Without Borders (student-facing quiz + AI study guide).

Run it:   streamlit run app.py

Flow:  take a short quiz  ->  submit  ->  score + a personalized study guide the
AGENT builds from your wrong answers (explanation + fresh practice per mistake),
plus the agent's read on your #1 trick and a teacher hand-off if needed.
"""
import json
import re
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

import agent
import mastery as m
import tutor
from gemma_client import vision_available, transcribe_image, plainify

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


def esc(text) -> str:
    """Prepare text for display: (1) escape currency '$' so $3.60 shows literally
    instead of the run between two '$' rendering as LaTeX; (2) turn plain integer
    fractions like 3/7 into proper stacked fractions via KaTeX. Decimals and
    money (3.60 / 1.5, $3.60) are left alone by the fraction rule."""
    t = str(text).replace("$", "\\$")                 # currency first
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
        "monster": "Fractis", "taunt": "Ready to watch you crumble like a bad fraction.", "lines": ["So... {name}. You found my shard field.", "Braver visitors than you have left here counting on their fingers, {name}.", "Show me your fractions - or become part of my collection."], "color": "#ff8a5c", "shape": "shard", "model": "/app/static/monsters/alien.glb",
        "lore": "Feeds on fractions added straight across. Weak to common denominators."},
    "Algebra": {
        "monster": "Equazor", "taunt": "I am ready to watch you lose this battle. Your signs will slip.", "lines": ["Well, well. {name} dares to balance equations with ME watching.", "One slipped sign, {name}, and your answers belong to me.", "I hope you brought more than luck, kid."], "color": "#ff6b9d", "shape": "knot", "model": "/app/static/monsters/dragon.glb",
        "lore": "Twists equations until the signs flip wrong. Weak to balanced moves."},
    "Data": {
        "monster": "Statiq", "taunt": "Your answers will drown in my noise.", "lines": ["Splash... {name}, was it? The data here gets... murky.", "Means, medians - it all blurs together down here, {name}.", "Let's see if you can keep your numbers in order. I doubt it."], "color": "#35d0c0", "shape": "blob", "model": "/app/static/monsters/fish.glb",
        "lore": "Blurs means and medians into noise. Weak to ordered data."},
    "Geometry & Measurement": {
        "monster": "Polygor", "taunt": "Every angle you pick will be the wrong one, little hero.", "lines": ["Hop hop, {name}. Welcome to my angle hoard.", "Every formula in here is ALMOST right. That's how I catch clever ones like you.", "Draw your diagrams carefully, kid. I feast on sloppy sketches."], "color": "#a78bfa", "shape": "poly", "model": "/app/static/monsters/frog.glb",
        "lore": "Hoards angles and stolen area formulas. Weak to a true diagram."},
    "Financial Literacy": {
        "monster": "Ledgerling", "taunt": "I collect mistakes - and I charge interest.", "lines": ["Ah, a new account. Name: {name}. Balance: doubtful.", "I skim a little interest off every mistake, {name}. Business is booming.", "Check the math or sign it all away. Your move, kid."], "color": "#ffd166", "shape": "coin", "model": "/app/static/monsters/demon.glb",
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
  #ui{position:absolute;inset:0;z-index:10;pointer-events:none;display:flex;
    flex-direction:column;justify-content:space-between;padding:28px}
  header h1{font-size:2.6rem;font-weight:900;letter-spacing:-1px;text-transform:uppercase;
    background:linear-gradient(135deg,#ffe9d6 25%,#e08d6d 70%,#b98868);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    filter:drop-shadow(0 0 14px rgba(224,141,109,.55))}
  header p{color:#b9a794;font-size:.95rem;margin-top:4px;max-width:430px}
  header{display:flex;justify-content:space-between;align-items:flex-start}
  .hbtns{display:flex;gap:10px}
  .hbtn{pointer-events:auto;background:rgba(255,240,225,.06);border:1px solid rgba(255,240,225,.16);
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
</style>
<div id="canvas-container"></div>
<div id="ui">
  <header>
    <div>
      <h1>Gemma Monsters</h1>
      <p>Every monster is here to make you forget your math. Defeat them by proving you remember.</p>
    </div>
    <div class="hbtns">
      <button class="hbtn" onclick="resetCamera()">Nexus view</button>
      <a class="hbtn" target="_top" id="exitlink" href="#">Simple dashboard</a>
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
function go(url){
  // Streamlit sandboxes this iframe without ancestor-navigation permission,
  // so open the challenge in a fresh tab (explicitly allowed to escape the sandbox).
  const w = window.open(url, '_blank');
  if(!w){
    const el = document.getElementById('obj');
    el.textContent = 'POP-UP BLOCKED — USE ITS PORTAL KEY BELOW THE NEXUS';
  }
}
(function(){var x=document.getElementById('exitlink');
  x.href=base+'?exit=1'; x.target='_blank';})();

let scene,camera,renderer,composer,selected=null;
const monsters=[],groups=[],mixers=[],ray=new THREE.Raycaster(),mouse=new THREE.Vector2();
let prevT=0;
let miniR=null,miniScene=null,miniCam=null,miniMix=null,miniObj=null;
let loader=null;
const CAM={x:0,y:20,z:34},look={x:0,y:0,z:0};

init(); animate();

function init(){
  const el=document.getElementById('canvas-container');
  scene=new THREE.Scene(); scene.fog=new THREE.FogExp2(0x0b0710,0.016);
  camera=new THREE.PerspectiveCamera(55,innerWidth/innerHeight,0.1,1000);
  camera.position.set(CAM.x,CAM.y,CAM.z); camera.lookAt(0,0,0);
  renderer=new THREE.WebGLRenderer({antialias:true});
  renderer.setSize(innerWidth,innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.outputEncoding=THREE.sRGBEncoding;
  el.appendChild(renderer.domElement);
  scene.add(new THREE.AmbientLight(0x2a1f22,1.1));
  const warm=new THREE.PointLight(0xffd9b8,1.6,60); warm.position.set(0,12,0); scene.add(warm);

  // nexus core
  const plat=new THREE.Mesh(new THREE.CylinderGeometry(6,6.5,1,6),
    new THREE.MeshStandardMaterial({color:0x1a1016,roughness:.55,metalness:.85,flatShading:true}));
  plat.position.y=-0.5; scene.add(plat);
  const core=new THREE.Mesh(new THREE.IcosahedronGeometry(1.8,1),
    new THREE.MeshBasicMaterial({color:0xffe9d6,wireframe:true,transparent:true,opacity:.65}));
  core.position.y=3; scene.add(core);
  const cl=new THREE.PointLight(0xe08d6d,2.6,22); cl.position.y=3; scene.add(cl);
  gsap.to(core.rotation,{y:Math.PI*2,duration:22,repeat:-1,ease:"none"});

  // stations with REAL monster models (Quaternius, CC0); procedural fallback
  const R=15; loader=(typeof THREE.GLTFLoader!=='undefined')?new THREE.GLTFLoader():null;
  NAMES.forEach((name,i)=>{
    const u=UNITS[name], col=new THREE.Color(u.color);
    const ang=(i/NAMES.length)*Math.PI*2, x=Math.cos(ang)*R, z=Math.sin(ang)*R;
    const g=new THREE.Group(); g.position.set(x,0,z); g.userData={gi:i}; groups.push(g);
    const p=new THREE.Mesh(new THREE.CylinderGeometry(3,3.2,.6,6),
      new THREE.MeshStandardMaterial({color:0x180f16,metalness:.8}));
    g.add(p);
    const ringG=new THREE.TorusGeometry(3.1,.06,16,6); ringG.rotateX(Math.PI/2);
    const ring=new THREE.Mesh(ringG,new THREE.MeshBasicMaterial({color:col}));
    ring.position.y=.35; g.add(ring);
    const holder=new THREE.Group(); holder.position.y=1.1;
    holder.userData={i,baseY:1.1}; g.add(holder); monsters.push(holder);
    const fallback=()=>{ const m=makeMonster(u.shape,col); m.position.y=2.3; holder.add(m); };
    if(loader && u.model){
      loader.load((window.__ORIGIN||'')+u.model, (gltf)=>{
        const obj=gltf.scene;
        const box=new THREE.Box3().setFromObject(obj);
        const size=box.getSize(new THREE.Vector3());
        const scale=4.7/Math.max(size.x,size.y,size.z,0.001);
        obj.scale.setScalar(scale);
        const box2=new THREE.Box3().setFromObject(obj);
        const c=box2.getCenter(new THREE.Vector3());
        obj.position.x-=c.x; obj.position.z-=c.z; obj.position.y-=box2.min.y;
        holder.add(obj);
        if(gltf.animations && gltf.animations.length){
          const mix=new THREE.AnimationMixer(obj);
          const idle=gltf.animations.find(a=>/idle|fly|swim/i.test(a.name))||gltf.animations[0];
          mix.clipAction(idle).play(); mixers.push(mix);
        }
      }, undefined, fallback);
    } else fallback();
    const lt=new THREE.PointLight(col,1.5,14); lt.position.y=3.2; g.add(lt);
    // a soft warm spotlight straight above the monster so it reads against the dark
    const spot=new THREE.SpotLight(0xfff3e0, 3.6, 24, Math.PI/4, 0.5, 1);
    spot.position.set(0,8.5,0.6); spot.target=holder; g.add(spot); g.add(spot.target);
    scene.add(g);
  });

  // dust
  const n=900,geo=new THREE.BufferGeometry(),pos=new Float32Array(n*3);
  for(let i=0;i<n*3;i+=3){pos[i]=(Math.random()-.5)*100;pos[i+1]=Math.random()*38-4;pos[i+2]=(Math.random()-.5)*100;}
  geo.setAttribute('position',new THREE.BufferAttribute(pos,3));
  scene.add(new THREE.Points(geo,new THREE.PointsMaterial({size:.1,color:0xe0a888,transparent:true,opacity:.35})));

  composer=new THREE.EffectComposer(renderer);
  composer.addPass(new THREE.RenderPass(scene,camera));
  composer.addPass(new THREE.UnrealBloomPass(new THREE.Vector2(innerWidth,innerHeight),0.75,.3,.32));

  addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();
    renderer.setSize(innerWidth,innerHeight);composer.setSize(innerWidth,innerHeight);});
  addEventListener('click',onClick);
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
        const clip=gltf.animations.find(a=>/walk/i.test(a.name))
                 ||gltf.animations.find(a=>/idle|swim|fly/i.test(a.name))
                 ||gltf.animations[0];
        const act=miniMix.clipAction(clip);
        act.timeScale=0.55;   // calm, menacing pace - not double speed
        act.play();
      }
    });
  }
}

function svgMini(col){
  return '<svg width="72" height="72" viewBox="0 0 40 40"><circle cx="20" cy="20" r="14" fill="'+col+'" opacity="0.85"/><circle cx="20" cy="20" r="17" fill="none" stroke="'+col+'" stroke-width="1.4" opacity="0.5"/></svg>';
}

function onClick(e){
  if(e.target.closest && e.target.closest('#ui a, #ui button, #card')) return;
  mouse.x=(e.clientX/innerWidth)*2-1; mouse.y=-(e.clientY/innerHeight)*2+1;
  ray.setFromCamera(mouse,camera);
  const hit=ray.intersectObjects(groups,true);
  if(hit.length){
    let o=hit[0].object;
    while(o.parent && o.userData.gi===undefined) o=o.parent;
    if(o.userData.gi!==undefined) focus(o.userData.gi);
  }
}

function focus(i){
  if(selected===i) return; selected=i;
  const name=NAMES[i], u=UNITS[name];
  const R=15, ang=(i/NAMES.length)*Math.PI*2;
  const sx=Math.cos(ang)*R, sz=Math.sin(ang)*R;
  gsap.to(camera.position,{x:Math.cos(ang)*(R+11),y:4.6,z:Math.sin(ang)*(R+11),duration:1.8,ease:"power3.inOut"});
  monsters.forEach((m,j)=>{ gsap.to(m.scale,{x:j===i?1.6:1,y:j===i?1.6:1,z:j===i?1.6:1,duration:0.9,ease:"power2.out"}); });
  gsap.to(monsters[i].rotation,{y:Math.PI/2-ang,duration:0.9,ease:'power2.out'});
  gsap.to(look,{x:sx,y:3.4,z:sz,duration:1.8,ease:"power3.inOut",
    onUpdate:()=>camera.lookAt(look.x,look.y,look.z)});
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
  gsap.to(camera.position,{x:CAM.x,y:CAM.y,z:CAM.z,duration:1.8,ease:"power2.inOut"});
  monsters.forEach(m=>gsap.to(m.scale,{x:1,y:1,z:1,duration:0.7}));
  gsap.to(look,{x:0,y:0,z:0,duration:1.8,ease:"power2.inOut",
    onUpdate:()=>camera.lookAt(look.x,look.y,look.z)});
}

function animate(time){
  requestAnimationFrame(animate);
  const t=(time||0)*0.001, dt=Math.min(0.05, t-prevT); prevT=t;
  mixers.forEach(m=>m.update(dt));
  if(miniMix) miniMix.update(dt);
  if(miniObj){
    const tt=(performance.now()-miniObj.userData.t0)*0.001;
    miniObj.position.z=Math.min(1.15,tt*0.55)+Math.sin(tt*1.7)*0.07;
  }
  if(miniR && document.getElementById('card').classList.contains('active'))
    miniR.render(miniScene,miniCam);
  monsters.forEach((m,i)=>{
    if(selected===null) m.rotation.y+=0.0035;           // slow spin, nexus view only
    if(selected!==i) m.position.y=m.userData.baseY+Math.sin(t*2+i)*.2;
  });
  // slow nexus orbit while nothing selected
  if(selected===null){
    const a=t*0.015;
    camera.position.x=Math.sin(a)*34; camera.position.z=Math.cos(a)*34;
    camera.lookAt(0,0,0);
  }
  composer.render();
}
window.resetCamera = resetCamera;
// hero name: ask once, remember forever
(function(){
  const box=document.getElementById('herobox'), tag=document.getElementById('herotag');
  const saved=(localStorage.getItem('gwb_hero')||'').trim();
  function show(n){ tag.textContent='CHALLENGER: '+n.toUpperCase(); tag.style.display='inline';
                    box.style.display='none'; }
  if(saved){ show(saved); } else { box.style.display='inline'; }
  document.getElementById('herogo').onclick=function(){
    const n=document.getElementById('heroname').value.trim();
    if(n){ localStorage.setItem('gwb_hero', n); show(n); } };
})();
window.__focus = focus;
});
</script>
"""


_VENDOR_FILES = ["three.min.js", "gsap.min.js", "EffectComposer.js", "RenderPass.js",
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
                "lore": m["lore"], "model": m.get("model", "")} for n, m in MONSTERS.items()}
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
      const pref=new RegExp("__CLIPPREF__","i");
      const clip=g.animations.find(a=>pref.test(a.name))
               ||g.animations.find(a=>/idle|walk|swim|fly/i.test(a.name))||g.animations[0];
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
      const clip=g.animations.find(a=>/attack|bite|roar|jump/i.test(a.name))
               ||g.animations.find(a=>/walk|idle/i.test(a.name))||g.animations[0];
      const act=mix.clipAction(clip); act.timeScale=0.7; act.play();
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
      const clip=g.animations.find(a=>/roar|attack|bite|jump/i.test(a.name))
               ||g.animations.find(a=>/idle|walk/i.test(a.name))||g.animations[0];
      const act=mix.clipAction(clip); act.timeScale=0.6; act.play();
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


def _encounter_html(mon, name):
    lines = [ln.format(name=name) for ln in mon.get("lines", [mon.get("taunt", "...")])]
    return (_ENCOUNTER_TEMPLATE
            .replace("__VENDOR__", _vendor_js(["three.min.js", "GLTFLoader.js"]))
            .replace("__MODEL__", mon["model"])
            .replace("__COLOR__", mon["color"])
            .replace("__NAME__", mon["monster"].upper())
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
    components.html(_encounter_html(mon, st.session_state.get("player_name", "challenger")),
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
            components.html(_taunt_html(mon["model"]), height=170)
        st.caption("Answer every question, then submit. Wrong answers feed the monster.")
        st.button("Back to the Nexus", key="quiz_to_nexus", on_click=back_to_map)
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
    result = agent.grade_quiz(st.session_state.quiz, st.session_state.answers)
    analysis = agent.analyze(result)

    if st.session_state.get("adventure"):
        st.markdown('<div class="gwb-kicker">GEMMA MONSTERS</div>', unsafe_allow_html=True)
        st.title("The Battle Report")
    else:
        st.title("Results")
    st.metric("Score", f"{result['correct']} / {result['total']}", f"{result['score_pct']}%")

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
                                            clip_pref="attack|bite|jump|roar|hit|dance|yes",
                                            speed=0.7), height=175)
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
    # only nudge the teacher when the main gap is still open
    if analysis["escalate"] and not (priority and priority["id"] in mastered):
        note(
            "Teacher hand-off",
            "Several questions were missed. The agent writes the teacher a report they "
            "can act on — not just a score.",
        )
        with st.expander("See the teacher report", expanded=True):
            if "teacher_report" not in st.session_state:
                with st.spinner("Writing a report the teacher can act on..."):
                    st.session_state.teacher_report = agent.teacher_report(result, analysis)
            with st.container(border=True):
                st.markdown(st.session_state.teacher_report)
            st.download_button("Download report", st.session_state.teacher_report,
                               file_name="teacher_report.md", key="dl_teacher")

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
                    st.markdown(esc(plainify(guide["worked_solution"])))

            # --- interactive "Now you try" ---
            p = guide["practice"]
            challenge_title = (f"{gmon['monster']}'s next challenge — "
                               f"let's see you slip this time:" if gmon else "Now you try:")
            st.markdown(f"**{challenge_title}** " + esc(p["question"]))
            if not p.get("options"):
                st.caption("Work it out on paper — then prove it in the training grounds below.")
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
                            st.markdown(esc(plainify(p["solution"])))

    if st.session_state.get("adventure"):
        st.button("Back to the monster nexus", key="tomap_bottom", on_click=back_to_map)
    st.button("Take another quiz", key="again_bottom", on_click=reset)


# ---------------- MASTERY LOOP ----------------
def check_answer():
    s = st.session_state.msession
    probe = st.session_state.mprobe
    chosen = st.session_state.get("mastery_choice")
    if not chosen:
        return
    explanation = st.session_state.get("mastery_reason", "")
    photo = st.session_state.get(f"mastery_photo_{s.attempts}")
    st.session_state.mtranscript = None
    if photo is not None and vision_available():
        with st.spinner("Gemma is reading your written work (on-device)..."):
            transcript = transcribe_image(photo.getvalue())
        st.session_state.mtranscript = transcript
        explanation = (explanation + "\n" if explanation else "") + \
            f"My written work: {transcript}"
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
        note("Why the agent declared mastery",
             "Two fresh questions in a row, answered correctly — and your reasoning showed "
             "real understanding, not a lucky guess. That's the evidence bar for mastery.")
        st.code(m.mastery_recap(s))
        st.button("Back to my results", key="back_mastered",
                  on_click=lambda: st.session_state.update(stage="results"))
        st.button("Take another quiz", key="again_mastered", on_click=reset)
        return
    if s.state == m.ESCALATED:
        note("Teacher hand-off",
             "The agent tried every approach it has. Time for a human — here is a report "
             "the teacher can act on, informed by what already didn't work.")
        if "escal_report" not in st.session_state:
            with st.spinner("Writing a report the teacher can act on..."):
                st.session_state.escal_report = m.escalation_report(s)
        with st.container(border=True):
            st.markdown(st.session_state.escal_report)
        st.download_button("Download report", st.session_state.escal_report,
                           file_name="teacher_report.md", key="dl_escal")
        st.button("Back to my results", key="back_escalated",
                  on_click=lambda: st.session_state.update(stage="results"))
        st.button("Take another quiz", key="again_escalated", on_click=reset)
        return

    # feedback from the previous answer
    fb = st.session_state.get("mfeedback")
    if st.session_state.get("mtranscript"):
        note("What Gemma read from your photo",
             st.session_state.mtranscript.replace("\n", "<br>"))
    if fb and fb.get("rationale"):
        # explainable AI: every decision shows its evidence-based "why"
        headline = ("Correct" if fb["correct"] and fb.get("label") == "RESOLVED"
                    else "Right answer — but not yet" if fb["correct"]
                    else "Not yet")
        note(f"Why the agent decided this · {headline}", esc(fb["rationale"]))

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
        "In one line: how did you get your answer? (optional — the agent reads it)",
        key="mastery_reason",
        placeholder="e.g. I found a common denominator of 12, then added the tops",
    )
    if vision_available():
        st.file_uploader(
            "...or photograph your written work — Gemma reads it on this device",
            type=["png", "jpg", "jpeg"], key=f"mastery_photo_{s.attempts}",
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

stage = st.session_state.get("stage", "intro")
{"intro": intro, "map": map_stage, "encounter": encounter_stage, "quiz": quiz,
 "results": results, "mastery": mastery_stage}[stage]()
