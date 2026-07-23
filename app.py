"""
app.py  —  Gemma Without Borders (student-facing quiz + AI study guide).

Run it:   streamlit run app.py

Flow:  take a short quiz  ->  submit  ->  score + a personalized study guide the
AGENT builds from your wrong answers (explanation + fresh practice per mistake),
plus the agent's read on your #1 misconception and a teacher hand-off if needed.
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

st.set_page_config(
    page_title=("GEMMA MONSTERS" if st.session_state.get("adventure") else "Gemma Without Borders"),
    layout="centered")

# ---- global styling: classic (ivory) or game skin (dark) — looks only, no logic ----
_GAME_SKIN = """
<style>
:root { --ink:#f2e8dc; --muted:#b9a794; --line:#3a2a35; --card:#1c1119; --accent:#e08d6d; }
[data-testid="stAppViewContainer"], [data-testid="stHeader"]{background:#0b0710 !important}
html,body,p,li,label,span,div{color:var(--ink)}
h1,h2,h3{font-family:Georgia,'Times New Roman',serif !important;font-weight:500 !important;
  color:#ffefdd !important;text-shadow:0 0 18px rgba(224,141,109,.35)}
.stCaption,[data-testid="stCaptionContainer"]{color:var(--muted) !important}
.stButton button, .stDownloadButton button{border-radius:8px;border:1px solid var(--line);
  background:#241322;color:#f2e8dc;box-shadow:none}
.stButton button[kind="primary"]{background:linear-gradient(135deg,#e08d6d,#b25638);
  border:1px solid #e08d6d;color:#1a0f14;font-weight:700;letter-spacing:.05em;
  box-shadow:0 0 18px rgba(224,141,109,.4)}
[data-testid="stVerticalBlockBorderWrapper"]{background:var(--card);
  border:1px solid var(--line) !important;border-radius:10px}
[data-testid="stExpander"]{border:1px solid var(--line);border-radius:8px;background:var(--card)}
[data-testid="stExpander"] summary{color:#f2e8dc}
[data-testid="stMetricValue"]{font-family:Georgia,serif;color:#ffefdd}
hr{border-color:var(--line) !important}
.stRadio label p, .stRadio label{color:#f2e8dc !important}
[data-testid="stWidgetLabel"] p{color:#d9c6b2 !important}
.stTextInput input{background:#241322;color:#f2e8dc;border:1px solid var(--line)}
[data-testid="stFileUploaderDropzone"]{background:#241322;border:1px dashed var(--line)}
code, pre{background:#241322 !important;color:#ffd9b8 !important}
.gwb-note{border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;
  background:var(--card);padding:.85rem 1.1rem;margin:.4rem 0 .9rem;color:var(--ink);
  box-shadow:0 0 14px rgba(224,141,109,.12)}
.gwb-note .label{display:block;font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--accent);margin-bottom:.25rem;font-weight:700}
.gwb-kicker{font-size:.75rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);margin-bottom:.2rem;font-weight:700}
.katex{color:#ffefdd}
</style>
"""

st.markdown("""
<style>
:root {
    --ink: #1F1E1B;
    --muted: #6E6B63;
    --line: #E4E1D7;
    --card: #FFFFFF;
    --accent: #C96442;
}
h1, h2, h3 {
    font-family: Georgia, 'Times New Roman', serif !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em;
    color: var(--ink) !important;
}
.stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
.stButton button {
    border-radius: 6px;
    border: 1px solid var(--line);
    box-shadow: none;
}
.stButton button[kind="primary"] {
    background: var(--accent);
    border: 1px solid var(--accent);
    color: #FFFFFF;
}
.stButton button[kind="primary"]:hover { background: #B25638; border-color: #B25638; }
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card);
    border: 1px solid var(--line) !important;
    border-radius: 8px;
}
[data-testid="stExpander"] {
    border: 1px solid var(--line);
    border-radius: 6px;
    background: var(--card);
}
[data-testid="stMetricValue"] {
    font-family: Georgia, 'Times New Roman', serif;
    color: var(--ink);
}
hr { border-color: var(--line) !important; }
.gwb-note {
    border: 1px solid var(--line);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    background: var(--card);
    padding: 0.85rem 1.1rem;
    margin: 0.4rem 0 0.9rem 0;
    color: var(--ink);
}
.gwb-note .label {
    display: block;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.25rem;
}
.gwb-kicker {
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.2rem;
}
</style>
""" if not st.session_state.get("adventure") else _GAME_SKIN, unsafe_allow_html=True)


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
    """Enter the autonomous practice loop, targeting the priority misconception."""
    pid = analysis["priority"]["id"]
    seed = next(w for w in result["wrong"]
                if w["misconception"] and w["misconception"].get("id") == pid)
    s = m.MasterySession(
        misconception_id=pid,
        misconception_name=analysis["priority"]["name"],
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
    st.markdown('<div class="gwb-kicker">Grade 9 EQAO Mathematics</div>', unsafe_allow_html=True)
    st.title("Gemma Without Borders")
    st.caption("An autonomous study agent, running privately on device.")
    st.write(
        "Take a short quiz. When you submit, the agent identifies why you missed "
        "what you missed, teaches each gap, and gives you a fresh question to "
        "confirm you understand."
    )
    col1, col2 = st.columns(2)
    strand = col1.selectbox("Topic", ["Mixed"] + STRANDS)
    n = col2.slider("Questions", 3, 8, 5)
    if st.button("Start quiz", type="primary"):
        st.session_state.stage = "quiz"
        st.session_state.quiz = pick_quiz(strand, n)
        st.session_state.answers = {}
        st.rerun()

    st.divider()
    st.caption("Or explore a different way:")
    if st.button("Play GEMMA Monsters  (beta)"):
        st.session_state.adventure = True
        st.session_state.stage = "map"
        st.rerun()


# ---------------- GEMMA MONSTERS (optional, additive game layer) ----------------
# Every unit is guarded by a Gemma Monster — a personified misconception. The hub
# is a 3D nexus (three.js, bloom). Clicking a monster shows its game card; Begin
# enters that unit's real quiz via ?station=. Deliberately NOT the app's clean
# design language — it's a different world.
MONSTERS = {
    "Number": {
        "monster": "Fractis", "color": "#ff8a5c", "shape": "shard",
        "lore": "Feeds on fractions added straight across. Weak to common denominators."},
    "Algebra": {
        "monster": "Equazor", "color": "#ff6b9d", "shape": "knot",
        "lore": "Twists equations until the signs flip wrong. Weak to balanced moves."},
    "Data": {
        "monster": "Statiq", "color": "#35d0c0", "shape": "blob",
        "lore": "Blurs means and medians into noise. Weak to ordered data."},
    "Geometry & Measurement": {
        "monster": "Polygor", "color": "#a78bfa", "shape": "poly",
        "lore": "Hoards angles and stolen area formulas. Weak to a true diagram."},
    "Financial Literacy": {
        "monster": "Ledgerling", "color": "#ffd166", "shape": "coin",
        "lore": "Skims your interest while you sleep. Weak to a sharp budget."},
}
STATIONS = MONSTERS  # router alias: ?station= keys


def monster_for(misconception_strand):
    return MONSTERS.get(misconception_strand)


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
  #card{align-self:flex-end;width:320px;opacity:0;transform:translateY(26px) rotate(1.5deg) scale(.96);
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
  .mstage{height:96px;margin:8px 14px;border-radius:8px;position:relative;
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
      <a class="hbtn" target="_top" id="exitlink" href="#">Exit game</a>
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
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/EffectComposer.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/RenderPass.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/ShaderPass.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/shaders/CopyShader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/shaders/LuminosityHighPassShader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/UnrealBloomPass.js"></script>
<script>
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
document.getElementById('exitlink').addEventListener('click',function(ev){ev.preventDefault();go(base+'?exit=1');});

let scene,camera,renderer,composer,selected=null;
const monsters=[],groups=[],ray=new THREE.Raycaster(),mouse=new THREE.Vector2();
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

  // stations
  const R=15;
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
    const monster=makeMonster(u.shape,col); monster.position.y=3.4;
    monster.userData={i,baseY:3.4}; g.add(monster); monsters.push(monster);
    const lt=new THREE.PointLight(col,1.3,12); lt.position.y=3.4; g.add(lt);
    scene.add(g);
  });

  // dust
  const n=900,geo=new THREE.BufferGeometry(),pos=new Float32Array(n*3);
  for(let i=0;i<n*3;i+=3){pos[i]=(Math.random()-.5)*100;pos[i+1]=Math.random()*38-4;pos[i+2]=(Math.random()-.5)*100;}
  geo.setAttribute('position',new THREE.BufferAttribute(pos,3));
  scene.add(new THREE.Points(geo,new THREE.PointsMaterial({size:.1,color:0xe0a888,transparent:true,opacity:.35})));

  composer=new THREE.EffectComposer(renderer);
  composer.addPass(new THREE.RenderPass(scene,camera));
  composer.addPass(new THREE.UnrealBloomPass(new THREE.Vector2(innerWidth,innerHeight),1.35,.55,.12));

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

function svgMini(col){
  return '<svg width="72" height="72" viewBox="0 0 40 40"><path d="M20 3 C31 3 37 12 37 21 C37 32 30 37 20 37 C10 37 3 32 3 21 C3 12 9 3 20 3 Z" fill="'+col+'"/><circle cx="14" cy="18" r="4.2" fill="#14101c"/><circle cx="26" cy="18" r="4.2" fill="#14101c"/><circle cx="15.4" cy="16.6" r="1.4" fill="#fff"/><circle cx="27.4" cy="16.6" r="1.4" fill="#fff"/><path d="M13 28 Q20 33 27 28" stroke="#14101c" stroke-width="2.4" fill="none" stroke-linecap="round"/></svg>';
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
  gsap.to(camera.position,{x:Math.cos(ang)*(R+8),y:6,z:Math.sin(ang)*(R+8),duration:1.8,ease:"power3.inOut"});
  gsap.to(look,{x:sx,y:3.4,z:sz,duration:1.8,ease:"power3.inOut",
    onUpdate:()=>camera.lookAt(look.x,look.y,look.z)});
  const card=document.getElementById('card');
  card.style.setProperty('--mc',u.color);
  document.getElementById('c-unit').textContent=name.toUpperCase()+' UNIT';
  document.getElementById('c-name').textContent=u.monster;
  document.getElementById('c-lore').textContent='"'+u.lore+'"';
  document.getElementById('c-stage').innerHTML=svgMini(u.color);
  const fbtn=document.getElementById('c-fight');
  fbtn.onclick=function(ev){ev.preventDefault();go(base+'?station='+encodeURIComponent(name));};
  card.classList.add('active');
}

function resetCamera(){
  selected=null; document.getElementById('card').classList.remove('active');
  gsap.to(camera.position,{x:CAM.x,y:CAM.y,z:CAM.z,duration:1.8,ease:"power2.inOut"});
  gsap.to(look,{x:0,y:0,z:0,duration:1.8,ease:"power2.inOut",
    onUpdate:()=>camera.lookAt(look.x,look.y,look.z)});
}

function animate(time){
  requestAnimationFrame(animate);
  const t=(time||0)*0.001;
  monsters.forEach((m,i)=>{
    m.rotation.y+=(selected===i?0.045:0.006);
    m.position.y=m.userData.baseY+Math.sin(t*2+i)*(selected===i?.12:.3);
  });
  // slow nexus orbit while nothing selected
  if(selected===null){
    const a=t*0.015;
    camera.position.x=Math.sin(a)*34; camera.position.z=Math.cos(a)*34;
    camera.lookAt(0,0,0);
  }
  composer.render();
}
</script>
"""


def _hub_html():
    data = {n: {"monster": m["monster"], "color": m["color"], "shape": m["shape"],
                "lore": m["lore"]} for n, m in MONSTERS.items()}
    return _HUB_TEMPLATE.replace("__UNITS__", json.dumps(data))


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
    components.html(_hub_html(), height=720, scrolling=False)
    st.markdown(
        '<div style="text-align:center;letter-spacing:.18em;font-size:.72rem;'
        'color:#e08d6d;font-weight:700;margin:2px 0 6px">PORTAL KEYS — JUMP STRAIGHT INTO A CHALLENGE</div>',
        unsafe_allow_html=True)
    cols = st.columns(len(MONSTERS) + 2)
    for i, (sname, mon) in enumerate(MONSTERS.items()):
        if cols[i + 1].button(mon["monster"], key=f"portal_{i}", use_container_width=True):
            st.session_state.quiz = pick_quiz(sname, 5)
            st.session_state.answers = {}
            st.session_state.stage = "quiz"
            st.rerun()
    mid = st.columns([2, 1, 2])
    mid[1].button("Leave the game", key="leave_game", on_click=reset, use_container_width=True)


# ---------------- QUIZ ----------------
def quiz():
    if st.session_state.get("adventure"):
        strand0 = st.session_state.quiz[0]["strand"] if st.session_state.get("quiz") else None
        mon = MONSTERS.get(strand0)
        st.markdown('<div class="gwb-kicker">GEMMA MONSTERS</div>', unsafe_allow_html=True)
        st.title(f"Face {mon['monster']}" if mon else "The Challenge")
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
            st.markdown(
                f'''<div style="background:linear-gradient(160deg,#1a1016,#241322);
                border:2px solid {mon["color"]};border-radius:14px;padding:20px 24px;
                margin:6px 0 14px;display:flex;align-items:center;gap:20px;
                box-shadow:0 0 26px {mon["color"]}44">
                <div style="flex-shrink:0">{monster_svg(mon["color"], 96)}</div>
                <div><div style="font-size:.72rem;letter-spacing:.16em;color:{mon["color"]};
                font-weight:700">A GEMMA MONSTER GOT YOU</div>
                <div style="font-family:Georgia,serif;font-size:1.6rem;color:#ffefdd">
                {mon["monster"]} strikes!</div>
                <div style="color:#cbb8a4;font-size:.95rem">It feeds on
                <strong style="color:#ffefdd">{priority["name"].lower()}</strong> —
                learn its weakness below and defeat it.</div></div></div>''',
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
        with st.spinner("The agent is studying your mistakes and writing your guide..."):
            seen = {q["id"] for q in st.session_state.quiz}
            st.session_state.guides = agent.build_study_guides(result, QUESTIONS, seen_ids=seen)
    for i, guide in enumerate(st.session_state.guides):
        with st.container(border=True):
            st.markdown(f"**{esc(guide['question'])}**")
            st.markdown(f"You picked **{esc(guide['chosen'])}** — the correct answer is **{esc(guide['correct'])}**")
            if guide["misconception"].get("name"):
                gmon = monster_for(guide["strand"]) if st.session_state.get("adventure") else None
                if gmon:
                    st.markdown(
                        f"<div style='font-size:.85rem;color:#8a8378'>"
                        f"{monster_svg(gmon['color'], 20)} "
                        f"<strong>{gmon['monster']}</strong>&nbsp;&middot;&nbsp;"
                        f"{guide['misconception']['name']}</div>",
                        unsafe_allow_html=True)
                else:
                    st.caption(f"The trick that got you: {guide['misconception']['name']}")
            st.markdown("**Why:** " + esc(guide["explanation"]))
            if guide["worked_solution"]:
                with st.expander("See the worked solution"):
                    st.markdown(esc(plainify(guide["worked_solution"])))

            # --- interactive "Now you try" ---
            p = guide["practice"]
            st.markdown("**Now you try:** " + esc(p["question"]))
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
                        trap = o.get("misconception_name")
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
             + s.misconception_name)

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
        st.session_state.setdefault("mastered", set()).add(s.misconception_id)
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
    reset()
_station = st.query_params.get("station")
if _station in STATIONS:
    st.session_state.adventure = True
    st.session_state.quiz = pick_quiz(_station, 5)
    st.session_state.answers = {}
    st.session_state.stage = "quiz"
    st.query_params.clear()

stage = st.session_state.get("stage", "intro")
{"intro": intro, "map": map_stage, "quiz": quiz, "results": results, "mastery": mastery_stage}[stage]()
