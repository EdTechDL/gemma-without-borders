"""First-run intro for GEMMA MONSTERS.

A five-beat opening scene rendered in the same 3D world as the citadel hub and
the encounter halls: title, the roster of five, how a battle goes, the
Collector, and a close that hands the player the gate.

Conventions copied from app.py deliberately, because they are load-bearing:

* three.js r128 is vendored and INLINED into the srcdoc iframe. Streamlit
  serves .js as text/plain and Chrome refuses to execute it from a <script src>.
* ``window.__ORIGIN`` is derived from the parent frame (or document.referrer),
  because relative URLs do not resolve inside a srcdoc iframe.
* GLB models load from ``(window.__ORIGIN||'') + "/app/static/monsters/x.glb"``
  and animate through an AnimationMixer bound to an exactly named clip.
* Audio is fetched as a blob first. Streamlit serves .mp3 with a text content
  type that the browser will not play directly.
* Model placement is self-fitting for any model: measure the Box3, normalise on
  the blended metric ``max(sz.y, 0.62 * max(sz.x, sz.z))`` so squat and winged
  models come out alike, centre on x/z, and seat with a small proportional lift
  so nothing looks sunk into the stone. Nothing is tuned to one model.

Public surface:

    onboarding_html(vendor_js: str, monsters: list, collector: dict) -> str

Template tokens (all substituted by ``onboarding_html``):

    __ROSTER__      JSON list of the five monsters
    __COLLECTOR__   JSON object for the Collector
    __VENDOR__      inlined <script> blocks for three.min.js + GLTFLoader.js

The only surviving double-underscore names in the output are JS identifiers
this module owns: ``__ORIGIN`` and ``__gmMuted``.
"""

import json

# The Collector rides the same model and idle clip as his boss arena
# (_BOSS_TEMPLATE in app.py loads skull.glb and plays the Flying_Idle clip).
COLLECTOR_MODEL = "/app/static/monsters/skull.glb"
COLLECTOR_CLIP = "CharacterArmature|Flying_Idle"


ONBOARDING_TEMPLATE = r"""
<style>
  html,body{margin:0;height:100%;overflow:hidden;background:#0b0710;
    font-family:'Trebuchet MS','Segoe UI',sans-serif;color:#f2e8dc;user-select:none}
  #stage{position:relative;width:100%;height:100vh}
  #v{position:absolute;inset:0;z-index:1}
  #v canvas{filter:saturate(1.06) contrast(1.09) brightness(.96)}
  #vig{position:absolute;inset:0;pointer-events:none;z-index:2;transition:background .9s ease;
    background:radial-gradient(ellipse 75% 62% at 50% 42%,transparent 55%,rgba(4,3,8,.55) 82%,rgba(2,2,6,.9) 100%)}
  #vig.dread{background:
    radial-gradient(ellipse 62% 52% at 50% 46%,transparent 38%,rgba(38,4,8,.5) 74%,rgba(6,1,3,.97) 100%)}
  #ui{position:absolute;inset:0;z-index:10;pointer-events:none}

  /* ---- reserved bands: copy on top, models in the middle, controls below ---- */
  #copy{position:absolute;left:0;right:0;top:0;height:26vh;padding:3.2vh 4vw 0;
    box-sizing:border-box;text-align:center}
  .beat{position:absolute;left:4vw;right:4vw;top:3.2vh;opacity:0;transform:translateY(14px);
    transition:opacity .55s ease,transform .55s cubic-bezier(.16,1,.3,1);pointer-events:none}
  .beat.on{opacity:1;transform:none}
  .beat h1{margin:0;font-size:clamp(2.1rem,5.4vw,3.6rem);font-weight:900;letter-spacing:-1px;
    text-transform:uppercase;line-height:1.02;
    background:linear-gradient(135deg,#ffe9d6 25%,#e08d6d 70%,#b98868);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    filter:drop-shadow(0 0 14px rgba(224,141,109,.55))}
  .beat h2{margin:0;font-size:clamp(1.15rem,2.5vw,1.7rem);font-weight:900;letter-spacing:.22em;
    text-transform:uppercase;color:#ffd87a;text-shadow:0 0 16px rgba(255,216,122,.35)}
  .beat p{margin:10px auto 0;max-width:660px;color:#cbb8a4;line-height:1.55;
    font-size:clamp(.88rem,1.5vw,1.02rem);text-shadow:0 1px 4px rgba(0,0,0,.85)}
  .beat p.tight{margin-top:5px}
  .beat.cold h2{color:#ff8f7a;text-shadow:0 0 20px rgba(224,60,42,.55)}
  .beat.cold p{color:#d8bfb6}

  /* ---- the roster's name plates: one column per monster, never over a model ---- */
  #labels{position:absolute;left:0;right:0;bottom:max(13vh,76px);height:max(12vh,52px);
    opacity:0;transition:opacity .5s ease;pointer-events:none}
  #labels.on{opacity:1}
  .lab{position:absolute;top:0;width:19%;transform:translateX(-50%);text-align:center;
    box-sizing:border-box}
  .lname{font-weight:900;letter-spacing:.1em;text-transform:uppercase;
    font-size:clamp(.68rem,1.15vw,.92rem);text-shadow:0 0 12px rgba(0,0,0,.9)}
  .lstrand{color:#b9a794;font-size:clamp(.55rem,.82vw,.7rem);letter-spacing:.12em;
    text-transform:uppercase;margin-top:3px}
  .ltrick{color:#8d7c6b;font-size:clamp(.52rem,.78vw,.68rem);font-style:italic;
    margin-top:5px;line-height:1.35;overflow:hidden;display:-webkit-box;
    -webkit-line-clamp:2;-webkit-box-orient:vertical}

  /* ---- control bar ---- */
  #bar{position:absolute;left:0;right:0;bottom:0;height:max(13vh,74px);
    display:flex;align-items:center;justify-content:space-between;padding:0 4vw;
    box-sizing:border-box}
  #bar a,#bar button{pointer-events:auto}
  .ghost{background:rgba(255,240,225,.06);border:1px solid rgba(255,240,225,.16);
    color:#d9c6b2;padding:10px 20px;border-radius:24px;cursor:pointer;font-weight:700;
    text-transform:uppercase;letter-spacing:.1em;font-size:.7rem;text-decoration:none;
    font-family:inherit;transition:all .25s}
  .ghost:hover{background:rgba(255,240,225,.16);color:#fff}
  .prime{display:inline-flex;align-items:center;justify-content:center;
    border:none;border-radius:9px;padding:13px 26px;cursor:pointer;font-weight:900;
    letter-spacing:.14em;text-transform:uppercase;font-size:.8rem;text-decoration:none;
    color:#1a0f14;font-family:inherit;transition:transform .15s,box-shadow .25s;
    background:linear-gradient(135deg,#e08d6d,#b8604a);
    box-shadow:0 8px 22px rgba(224,141,109,.4)}
  .prime:hover{transform:translateY(-2px)}
  #enter{display:none;background:linear-gradient(135deg,#ffd87a,#e08d6d);
    box-shadow:0 10px 28px rgba(255,216,122,.45)}
  #dots{display:flex;gap:9px}
  .dot{width:8px;height:8px;border-radius:50%;background:rgba(255,240,225,.2);
    transition:all .4s ease}
  .dot.on{background:#e08d6d;box-shadow:0 0 10px rgba(224,141,109,.9);transform:scale(1.25)}
</style>
<div id="stage">
  <div id="v"></div>
  <div id="vig"></div>
  <div id="ui">
    <div id="copy">
      <div class="beat on" data-s="1">
        <h1>Gemma Monsters</h1>
        <p>Five monsters. One citadel. Every single one of them wants you to get it wrong.</p>
      </div>
      <div class="beat" data-s="2">
        <h2>The Five</h2>
        <p>Each one has a favourite way of tripping you up - a wrong move that
           feels completely right, right up until it isn't. Learn their faces
           now. You will be seeing them.</p>
      </div>
      <div class="beat" data-s="3">
        <h2>How a battle goes</h2>
        <p>Walk into its lair and it starts throwing questions - all of them bent
           around its own favourite trick.</p>
        <p class="tight">Lucky guesses will not save you here. It only goes down when
           you can show it exactly why its trick stopped working.</p>
      </div>
      <div class="beat cold" data-s="4">
        <h2>The Collector</h2>
        <p>The five are pests. He is something else. He waits for the students who keep
           slipping, and he takes back the maths they were supposed to already own -
           and he takes it against a clock.</p>
      </div>
      <div class="beat" data-s="5">
        <h2>Two last things</h2>
        <p>No internet. No cloud. Every monster in here lives on this laptop,
           and whatever happens in this castle stays in this castle.</p>
        <p class="tight"><svg viewBox="0 0 48 48" width="26" height="26" fill="none"
           stroke="#e08d6d" stroke-width="2.8" stroke-linecap="round"
           stroke-linejoin="round" style="vertical-align:-6px;margin-right:6px">
           <circle cx="15" cy="12" r="5.8"/>
           <path d="M5.5 42v-8.5C5.5 27.7 9.8 23.4 15 23.4"/>
           <circle cx="32.5" cy="24" r="4.4"/>
           <path d="M25 42v-5.6c0-4.1 3.4-7.5 7.5-7.5s7.5 3.4 7.5 7.5V42"/>
           <path d="M15.5 23.6c5.6 0 9.4 3.4 12 8.2"/></svg>
           This mark, wherever you see it, is where mum and dad can read what
           the citadel has noticed about your maths.</p>
      </div>
    </div>
    <div id="labels"></div>
    <div id="bar">
      <span class="ghost" id="skip" style="visibility:hidden">Skip intro</span>
      <div id="dots"></div>
      <button class="prime" id="next">Next</button>
      <span class="prime" id="enter">Scroll down to enter</span>
    </div>
  </div>
</div>
<script>
(function(){ var o='';
  try{ o=window.parent.location.origin; }catch(e){ try{ o=new URL(document.referrer).origin; }catch(_){} }
  window.__ORIGIN=o; })();
</script>
__VENDOR__
<script>
window.addEventListener('load', function(){
  var ROSTER=__ROSTER__, COLLECTOR=__COLLECTOR__;
  var STEPS=5, step=1;

  // ---- leaving: the parent page path plus ?onboarded=1, built at click time ----
  function navBase(){
    var b='/';
    try{ b=window.parent.location.pathname||'/'; }
    catch(e){ try{ b=new URL(document.referrer).pathname||'/'; }catch(_){} }
    return b;
  }

  // ---- the shared mute switch, exactly as the citadel and the arenas read it ----
  function __gmMuted(){ try{ return localStorage.getItem('gm_mute')==='1'; }catch(e){ return false; } }

  // ---- theme: a ten second loop, fetched as a blob because Streamlit serves
  // .mp3 with a text content type the browser will not play directly. Autoplay
  // needs a gesture, so it starts on the first pointer interaction. ----
  (function(){
    var VOL=0.30, started=false, theme=null;
    function begin(){
      if(started||__gmMuted()) return;
      started=true;
      fetch((window.__ORIGIN||'')+'/app/static/audio/onboarding.mp3')
        .then(function(res){ return res.blob(); })
        .then(function(b){
          theme=new Audio(URL.createObjectURL(new Blob([b],{type:'audio/mpeg'})));
          theme.loop=true; theme.volume=0;
          theme.play().catch(function(){});
          var fade=0;
          var t=setInterval(function(){
            fade=Math.min(1,fade+0.06);
            if(theme) theme.volume=VOL*fade;
            if(fade>=1) clearInterval(t);
          },110);
        }).catch(function(){ started=false; });
    }
    addEventListener('pointerdown',begin);
    addEventListener('keydown',begin);
  })();

  // ---------------- scene ----------------
  var W=innerWidth,H=innerHeight;
  var r=new THREE.WebGLRenderer({antialias:true});
  r.setSize(W,H); r.setPixelRatio(Math.min(devicePixelRatio,2));
  r.outputEncoding=THREE.sRGBEncoding;
  r.toneMapping=THREE.ACESFilmicToneMapping; r.toneMappingExposure=1.0;
  document.getElementById('v').appendChild(r.domElement);

  var sc=new THREE.Scene();
  var clearCol=new THREE.Color(0x0b0710);
  r.setClearColor(clearCol);
  sc.fog=new THREE.FogExp2(0x0b0710,0.042);

  var CAM_Z=9.0;
  var cam=new THREE.PerspectiveCamera(42,W/H,0.1,80);
  cam.position.set(0,1.8,CAM_Z); cam.lookAt(0,1.8,0);
  var camTargetY=1.8;

  // ---- canvas masonry, the same technique as the citadel ----
  function makeStoneTex(base,line,cols,rows,rx,ry){
    var cv=document.createElement('canvas'); cv.width=512; cv.height=512;
    var ctx=cv.getContext('2d');
    ctx.fillStyle=base; ctx.fillRect(0,0,512,512);
    ctx.strokeStyle=line; ctx.lineWidth=5;
    var rh=512/rows, cw=512/cols, i, j;
    for(i=0;i<rows;i++){
      var y=i*rh;
      ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(512,y); ctx.stroke();
      var off=(i%2===0)?0:cw/2;
      for(j=0;j<cols+1;j++){
        var x=j*cw+off;
        ctx.beginPath(); ctx.moveTo(x,y); ctx.lineTo(x,y+rh); ctx.stroke();
      }
    }
    for(i=0;i<9000;i++){
      var px=Math.random()*512, py=Math.random()*512;
      var sh=Math.floor(Math.random()*40);
      ctx.fillStyle='rgba('+sh+','+sh+','+sh+',0.16)';
      ctx.fillRect(px,py,2,2);
    }
    var tex=new THREE.CanvasTexture(cv);
    tex.wrapS=THREE.RepeatWrapping; tex.wrapT=THREE.RepeatWrapping;
    tex.repeat.set(rx,ry);
    return tex;
  }
  var floorMat=new THREE.MeshStandardMaterial({
    map:makeStoneTex('#1e1721','#0c0710',4,5,4,6),roughness:0.88,metalness:0.08});
  var wallMat=new THREE.MeshStandardMaterial({
    map:makeStoneTex('#221a28','#100a14',8,14,7,3),roughness:0.92,metalness:0.04});
  var colMat=new THREE.MeshStandardMaterial({
    map:makeStoneTex('#221a28','#100a14',6,10,1.2,2.4),roughness:0.88,metalness:0.06});
  var trimMat=new THREE.MeshStandardMaterial({color:0x17111c,roughness:0.92});
  var woodMat=new THREE.MeshStandardMaterial({color:0x241a13,roughness:0.85});
  var ironMat=new THREE.MeshStandardMaterial({color:0x141016,roughness:0.55,metalness:0.55});

  // ---- the hall: a long aisle so the far wall reads as distance, not backdrop ----
  var floor=new THREE.Mesh(new THREE.PlaneGeometry(34,52),floorMat);
  floor.rotation.x=-Math.PI/2; floor.position.set(0,0,-6); sc.add(floor);
  var runner=new THREE.Mesh(new THREE.PlaneGeometry(4.4,24),
    new THREE.MeshStandardMaterial({color:0x1b0810,roughness:0.98}));
  runner.rotation.x=-Math.PI/2; runner.position.set(0,0.015,-2); sc.add(runner);
  var backWall=new THREE.Mesh(new THREE.BoxGeometry(34,14,0.8),wallMat);
  backWall.position.set(0,7,-13.2); sc.add(backWall);
  var wallL=new THREE.Mesh(new THREE.BoxGeometry(0.6,14,52),wallMat);
  wallL.position.set(-11.5,7,-6); sc.add(wallL);
  var wallR=wallL.clone(); wallR.position.x=11.5; sc.add(wallR);
  var ceiling=new THREE.Mesh(new THREE.PlaneGeometry(34,52),
    new THREE.MeshStandardMaterial({color:0x0b0810,roughness:1}));
  ceiling.rotation.x=Math.PI/2; ceiling.position.set(0,10.4,-6); sc.add(ceiling);

  // ---- two rows of columns receding toward the gate ----
  (function(){
    [[-8.6,-3.4],[8.6,-3.4],[-8.6,-7.4],[8.6,-7.4],[-8.6,-11.0],[8.6,-11.0]]
      .forEach(function(p){
        var cg=new THREE.Group();
        var shaft=new THREE.Mesh(new THREE.CylinderGeometry(0.55,0.66,8.0,10),colMat);
        shaft.position.y=4.4; cg.add(shaft);
        var cb=new THREE.Mesh(new THREE.BoxGeometry(1.7,0.6,1.7),trimMat);
        cb.position.y=0.3; cg.add(cb);
        var cap=new THREE.Mesh(new THREE.BoxGeometry(1.6,0.5,1.6),trimMat);
        cap.position.y=8.6; cg.add(cap);
        cg.position.set(p[0],0,p[1]); sc.add(cg);
      });
  })();

  // ---- the sealed gate at the head of the hall ----
  var gate=new THREE.Group();
  var gFrame=new THREE.Mesh(new THREE.BoxGeometry(4.2,5.6,0.8),trimMat);
  gFrame.position.set(0,2.8,-12.5); gate.add(gFrame);
  var gDoor=new THREE.Mesh(new THREE.BoxGeometry(2.9,4.4,0.3),woodMat);
  gDoor.position.set(0,2.2,-12.1); gate.add(gDoor);
  var sealMat=new THREE.MeshBasicMaterial({color:0xffd87a,transparent:true,opacity:0.55,
    depthWrite:false,blending:THREE.AdditiveBlending});
  var sealRing=new THREE.Mesh(new THREE.TorusGeometry(1.0,0.05,10,44),sealMat);
  sealRing.position.set(0,2.3,-11.9); gate.add(sealRing);
  var sealBar=new THREE.Mesh(new THREE.BoxGeometry(1.8,0.055,0.03),
    new THREE.MeshBasicMaterial({color:0xffd87a,transparent:true,opacity:0.4,
      depthWrite:false,blending:THREE.AdditiveBlending}));
  sealBar.position.set(0,2.3,-11.88); sealBar.rotation.z=Math.PI/4; gate.add(sealBar);
  var sealBar2=sealBar.clone(); sealBar2.rotation.z=-Math.PI/4; gate.add(sealBar2);
  var sealLight=new THREE.PointLight(0xffd87a,1.1,9);
  sealLight.position.set(0,2.5,-11.2); gate.add(sealLight);
  sc.add(gate);

  // ---- lighting: a dark hall lit almost entirely by its own fires ----
  var amb=new THREE.AmbientLight(0x141c30,0.34); sc.add(amb);
  var key=new THREE.SpotLight(0xffd9a8,1.7,22,Math.PI/6,0.75);
  key.position.set(0,8.0,6.0); key.target.position.set(0,1.6,0);
  sc.add(key); sc.add(key.target);
  var rim=new THREE.PointLight(0xffd87a,1.3,20);
  rim.position.set(0,3.4,-4.2); sc.add(rim);

  // ---- torch and brazier flames, sprite glow plus emissive core ----
  var flameTex=(function(){
    var cv=document.createElement('canvas'); cv.width=64; cv.height=64;
    var ctx=cv.getContext('2d');
    var fg=ctx.createRadialGradient(32,36,2,32,32,30);
    fg.addColorStop(0,'rgba(255,236,180,0.95)');
    fg.addColorStop(0.35,'rgba(255,150,60,0.65)');
    fg.addColorStop(1,'rgba(255,90,20,0)');
    ctx.fillStyle=fg; ctx.fillRect(0,0,64,64);
    return new THREE.CanvasTexture(cv);
  })();
  var flames=[];
  function addFlame(x,y,z,intensity){
    var spr=new THREE.Sprite(new THREE.SpriteMaterial({map:flameTex,color:0xffc078,
      transparent:true,opacity:0.95,blending:THREE.AdditiveBlending,depthWrite:false}));
    spr.position.set(x,y,z); spr.scale.set(0.85,1.2,1); sc.add(spr);
    var core=new THREE.Mesh(new THREE.ConeGeometry(0.13,0.42,7),
      new THREE.MeshBasicMaterial({color:0xffb45e}));
    core.position.set(x,y-0.08,z); sc.add(core);
    var l=new THREE.PointLight(0xff8844,intensity,14);
    l.position.set(x,y+0.15,z); sc.add(l);
    flames.push({light:l,sprite:spr,core:core,base:intensity,x:x,y:y,z:z,seed:Math.random()*10});
  }
  function addBrazier(x,z){
    var ped=new THREE.Mesh(new THREE.CylinderGeometry(0.3,0.44,1.05,8),trimMat);
    ped.position.set(x,0.52,z); sc.add(ped);
    var bowl=new THREE.Mesh(new THREE.CylinderGeometry(0.54,0.3,0.4,10),ironMat);
    bowl.position.set(x,1.25,z); sc.add(bowl);
    addFlame(x,1.72,z,1.3);
  }
  function addTorch(x,z){
    var inward=(x<0)?1:-1;
    var stick=new THREE.Mesh(new THREE.CylinderGeometry(0.05,0.07,0.6,6),woodMat);
    stick.position.set(x-inward*0.12,3.0,z); stick.rotation.z=inward*0.45; sc.add(stick);
    addFlame(x,3.4,z,1.0);
  }
  // every fire sits behind or outside the roster row, so nothing ever lights a
  // model from in front of the camera or crowds the models on a wide window
  addBrazier(-6.6,-2.6); addBrazier(6.6,-2.6);
  addTorch(-8.0,-6.6); addTorch(8.0,-6.6);
  addTorch(-8.0,-10.4); addTorch(8.0,-10.4);

  // ---- warm embers rising off the fires, same trick as the citadel ----
  var EMBERS=140;
  var eGeo=new THREE.BufferGeometry();
  var ePos=new Float32Array(EMBERS*3);
  var eMeta=[];
  (function(){
    for(var i=0;i<EMBERS;i++){
      var f=flames[i%flames.length];
      var m={f:f,jx:(Math.random()-0.5)*0.9,jz:(Math.random()-0.5)*0.9,
        spd:0.008+Math.random()*0.015,ph:Math.random()*6.28};
      eMeta.push(m);
      ePos[i*3]=f.x+m.jx; ePos[i*3+1]=f.y+Math.random()*3.4; ePos[i*3+2]=f.z+m.jz;
    }
  })();
  eGeo.setAttribute('position',new THREE.BufferAttribute(ePos,3));
  var eMat=new THREE.PointsMaterial({color:0xffcc55,size:0.095,transparent:true,
    opacity:0.8,blending:THREE.AdditiveBlending,depthWrite:false});
  sc.add(new THREE.Points(eGeo,eMat));

  // ---------------- models ----------------
  // Every model is normalised to a UNIT box first, so the per-step sizing is a
  // single scale on its holder. Nothing below is tuned to one model: the
  // blended size metric treats squat frogs and wide-winged fliers alike, and
  // the seat lift is a fraction of the model's own height so an animation clip
  // that dips below the rest pose never looks swallowed by the floor.
  // extraLift is an artistic override in NORMALISED units (the model is scaled
  // into a unit box first, so 0.3 is three tenths of its own size). It is not
  // scaled by height on purpose: a flier animates in a horizontal pose, which
  // makes its height tiny, so a height-proportional nudge cannot lift it off
  // the floor - and a flier should hover anyway. Defaults to nothing.
  function fitUnit(obj,extraLift){
    var b=new THREE.Box3().setFromObject(obj);
    var sz=b.getSize(new THREE.Vector3());
    var eff=Math.max(sz.y,0.62*Math.max(sz.x,sz.z),0.001);
    obj.scale.setScalar(1/eff);
    var b2=new THREE.Box3().setFromObject(obj);
    var c=b2.getCenter(new THREE.Vector3());
    var h=b2.max.y-b2.min.y;
    var lift=Math.max(0.05,h*0.06)+(extraLift||0);
    obj.position.set(-c.x,-b2.min.y+lift,-c.z);
    var sx=b2.max.x-b2.min.x, sz=b2.max.z-b2.min.z;
    // r is the sweep diameter: the model turns on the spot, so a deep model
    // needs as much room as a wide one before it crosses a neighbour or the edge
    return {h:h+lift, w:Math.max(sx,sz,0.001), r:Math.max(Math.sqrt(sx*sx+sz*sz),0.001)};
  }

  var loader=(typeof THREE.GLTFLoader!=='undefined')?new THREE.GLTFLoader():null;
  var units=[];     // the five
  var collector=null;
  var mixers=[];

  function makeHolder(color){
    var holder=new THREE.Group();
    holder.visible=false;
    var pool=new THREE.Mesh(new THREE.CircleGeometry(0.5,32),
      new THREE.MeshBasicMaterial({color:new THREE.Color(color),transparent:true,
        opacity:0.26,depthWrite:false,blending:THREE.AdditiveBlending}));
    pool.rotation.x=-Math.PI/2; pool.position.y=0.02; holder.add(pool);
    holder.userData={app:0,want:0,mh:1.0,mw:1.0,mr:1.4,
                     k:1.0,tk:1.0,x:0,tx:0,z:0,tz:0,pool:pool};
    sc.add(holder);
    return holder;
  }

  function loadInto(entry,color){
    if(!loader||!entry.model) return;
    loader.load((window.__ORIGIN||'')+entry.model,function(g){
      var obj=g.scene;
      var m=fitUnit(obj,entry.lift||0);
      obj.traverse(function(o){ if(o.isMesh) o.castShadow=true; });
      entry.holder.add(obj);
      entry.holder.userData.mh=m.h;
      entry.holder.userData.mw=m.w;
      entry.holder.userData.mr=m.r;
      entry.obj=obj;
      if(g.animations&&g.animations.length){
        var mix=new THREE.AnimationMixer(obj);
        var clip=g.animations.find(function(a){ return a.name===entry.clip; })
              ||g.animations.find(function(a){ return /idle/i.test(a.name); })
              ||g.animations[0];
        var act=mix.clipAction(clip); act.timeScale=0.8; act.play();
        mixers.push(mix);
      }
      layout();
    },undefined,function(){});
  }

  ROSTER.forEach(function(mon){
    var entry={name:mon.name,strand:mon.strand,trick:mon.trick,color:mon.color||'#e08d6d',
               model:mon.model,clip:mon.clip,obj:null};
    entry.holder=makeHolder(entry.color);
    units.push(entry);
    loadInto(entry,entry.color);
  });
  (function(){
    collector={name:COLLECTOR.name,color:'#e03c2a',model:COLLECTOR.model,
               clip:COLLECTOR.clip,obj:null};
    collector.holder=makeHolder(collector.color);
    loadInto(collector,collector.color);
  })();
  var all=units.concat([collector]);

  // ---------------- name plates ----------------
  (function(){
    var box=document.getElementById('labels');
    units.forEach(function(u){
      var d=document.createElement('div'); d.className='lab';
      var n=document.createElement('div'); n.className='lname';
      n.style.color=u.color; n.textContent=u.name||'';
      var s=document.createElement('div'); s.className='lstrand';
      s.textContent=u.strand||'';
      d.appendChild(n); d.appendChild(s);
      if(u.trick){
        var t=document.createElement('div'); t.className='ltrick';
        t.textContent='"'+u.trick+'"';
        d.appendChild(t);
      }
      d.style.left='50%';
      box.appendChild(d);
      u.lab=d;
    });
    var dots=document.getElementById('dots');
    for(var i=1;i<=STEPS;i++){
      var dot=document.createElement('span');
      dot.className='dot'+(i===1?' on':'');
      dots.appendChild(dot);
    }
  })();

  // ---------------- layout: self-fitting for whatever loaded ----------------
  // Copy owns the top band and the plates own the lower band, so the models are
  // framed into the middle by aiming the camera rather than by moving text.
  function visH(dist){ return 2*Math.tan(cam.fov*Math.PI/360)*dist; }

  function frame(dist,tallest,centreFrac){
    var vh=visH(dist);
    camTargetY=(tallest*0.5)-(0.5-centreFrac)*vh;
  }

  // The band a model may occupy is measured off the reserved DOM strips, not
  // guessed: copy owns the top, the name plates and the control bar own the
  // bottom. Text can therefore never end up on top of a model at any window
  // size, and the models still use every pixel that is genuinely free.
  function band(withLabels){
    var hh=innerHeight||1;
    var top=document.getElementById('copy').getBoundingClientRect().bottom;
    var bot=document.getElementById(withLabels?'labels':'bar').getBoundingClientRect().top;
    var pad=Math.max(8,hh*0.018);
    top+=pad; bot-=pad;
    if(!(bot>top)){ top=hh*0.30; bot=hh*0.70; }
    return {frac:(bot-top)/hh, centre:((top+bot)*0.5)/hh};
  }

  // The band cap has to be measured on the height a model actually RENDERS at,
  // not on the normalised metric: a tall model and a squat one are deliberately
  // not the same height, and only the tallest may touch the top of the band. If
  // it would, every model in the shot shrinks by the same factor, so the group
  // keeps its relative proportions. This is what keeps copy and models apart on
  // a short window, where the reserved bands are only a few dozen pixels tall.
  function fitBand(list,vh,maxFrac){
    var tallest=0,i,u;
    for(i=0;i<list.length;i++){ u=list[i].holder.userData; tallest=Math.max(tallest,u.tk*u.mh); }
    if(tallest>maxFrac*vh && tallest>0){
      var s=maxFrac*vh/tallest;
      for(i=0;i<list.length;i++){ list[i].holder.userData.tk*=s; }
      tallest=maxFrac*vh;
    }
    return tallest;
  }
  function commit(list){
    for(var i=0;i<list.length;i++){
      var u=list[i].holder.userData;
      if(u.app<0.02){ u.k=u.tk; u.x=u.tx; u.z=u.tz; }   // not on screen yet: snap
    }
  }

  function layout(){
    var tallest=0,i,u;
    if(step===2){
      var b2=band(true);
      var d2=CAM_Z, vh2=visH(d2), halfW2=vh2*0.5*cam.aspect;
      var n=units.length, slot=(halfW2*2/n)*0.96;
      for(i=0;i<n;i++){
        u=units[i].holder.userData;
        u.tk=Math.min(0.40*vh2, slot/u.mr);   // never wider than its own slot
      }
      tallest=fitBand(units,vh2,Math.min(0.40,b2.frac));
      // pull the whole row in until the end monsters clear the frame edges
      var xs=[],need=0;
      for(i=0;i<n;i++){
        u=units[i].holder.userData;
        xs.push(((((i+0.5)/n)*2-1))*halfW2);
        need=Math.max(need,Math.abs(xs[i])+0.5*u.tk*u.mr);
      }
      var inset=(need>halfW2*0.97)?(halfW2*0.97/need):1;
      for(i=0;i<n;i++){
        u=units[i].holder.userData;
        u.tx=xs[i]*inset; u.tz=0;
        // the plate follows its monster, so a name never drifts off its owner
        units[i].lab.style.left=((0.5+u.tx/(2*halfW2))*100)+'%';
      }
      commit(units);
      frame(d2,tallest,b2.centre);
    } else if(step===3){
      var b3=band(false);
      var z3=1.0, d3=CAM_Z-z3, vh3=visH(d3), halfW3=vh3*0.5*cam.aspect;
      var hero=units[Math.min(2,units.length-1)];
      if(hero){
        u=hero.holder.userData;
        u.tk=Math.min(0.46*vh3, halfW3*1.5/u.mr); u.tx=0; u.tz=z3;
        tallest=fitBand([hero],vh3,Math.min(0.46,b3.frac));
        commit([hero]);
      }
      frame(d3,tallest,b3.centre);
    } else if(step===4){
      // he stands closer and reads bigger than any of the five ever did
      var b4=band(false);
      var z4=2.6, d4=CAM_Z-z4, vh4=visH(d4), halfW4=vh4*0.5*cam.aspect;
      if(collector){
        u=collector.holder.userData;
        u.tk=Math.min(0.60*vh4, halfW4*1.25/u.mr); u.tx=0; u.tz=z4;
        tallest=fitBand([collector],vh4,Math.min(0.60,b4.frac));
        commit([collector]);
      }
      frame(d4,tallest,b4.centre);
    } else {
      camTargetY=2.5;    // steps 1 and 5 look up the hall at the sealed gate
    }
  }

  // ---------------- mood ----------------
  // Step 4 is meant to land colder and harder than step 2: the fires drop back,
  // the key light swings low and red, the fog thickens and the embers go to ash.
  var WARM={amb:0x141c30,ambI:0.34,keyC:0xffd9a8,keyI:1.7,keyY:8.0,keyZ:6.0,
            rimC:0xffd87a,rimI:1.3,rimZ:-4.2,fog:0.050,clear:0x0b0710,
            flame:1.0,ember:0xffcc55,expo:0.92};
  var DREAD={amb:0x24080e,ambI:0.16,keyC:0xff3a24,keyI:2.6,keyY:2.6,keyZ:5.2,
             rimC:0xff2a18,rimI:2.4,rimZ:-2.6,fog:0.105,clear:0x050308,
             flame:0.26,ember:0x7f8590,expo:0.80};
  [WARM,DREAD].forEach(function(M){
    M.cAmb=new THREE.Color(M.amb); M.cKey=new THREE.Color(M.keyC);
    M.cRim=new THREE.Color(M.rimC); M.cEmb=new THREE.Color(M.ember);
    M.cClear=new THREE.Color(M.clear);
  });
  // the key light only comes up when there is something standing in it
  var keyWant=0.34, keyMul=0.34;
  var mood={}, moodTo=WARM;
  (function(){ for(var mk in WARM) mood[mk]=WARM[mk]; })();
  var ambC=new THREE.Color(WARM.amb), keyC=new THREE.Color(WARM.keyC),
      rimC=new THREE.Color(WARM.rimC), embC=new THREE.Color(WARM.ember),
      fogC=new THREE.Color(WARM.clear);

  function num(a,b,t){ return a+(b-a)*t; }

  // ---------------- steps ----------------
  var nextBtn=document.getElementById('next');
  var enterA=document.getElementById('enter');

  function setStep(n){
    step=Math.max(1,Math.min(STEPS,n));
    var beats=document.querySelectorAll('.beat');
    for(var i=0;i<beats.length;i++){
      if(parseInt(beats[i].getAttribute('data-s'),10)===step) beats[i].classList.add('on');
      else beats[i].classList.remove('on');
    }
    var dots=document.querySelectorAll('.dot');
    for(var j=0;j<dots.length;j++){
      if(j===step-1) dots[j].classList.add('on'); else dots[j].classList.remove('on');
    }
    document.getElementById('labels').classList.toggle('on',step===2);
    var heroIdx=Math.min(2,units.length-1);
    units.forEach(function(u,i){
      u.holder.userData.want=(step===2||(step===3&&i===heroIdx))?1:0;
    });
    if(collector) collector.holder.userData.want=(step===4)?1:0;
    gate.visible=(step===1||step===5);
    document.getElementById('vig').classList.toggle('dread',step===4);
    moodTo=(step===4)?DREAD:WARM;
    keyWant=(step===1||step===5)?0.34:1.0;
    // explicit values both ways: an empty string would fall back to the
    // stylesheet, and the stylesheet keeps the final control hidden
    nextBtn.style.display=(step>=STEPS)?'none':'inline-flex';
    enterA.style.display=(step>=STEPS)?'inline-flex':'none';

    layout();
  }

  nextBtn.addEventListener('click',function(){ setStep(step+1); });
  addEventListener('keydown',function(e){
    if(e.key==='Enter'||e.key===' '||e.code==='Space'){
      e.preventDefault();
      if(step>=STEPS){ return; }
      else setStep(step+1);
    }
  });

  addEventListener('resize',function(){
    W=innerWidth; H=innerHeight;
    cam.aspect=W/H; cam.updateProjectionMatrix();
    r.setSize(W,H);
    layout();
  });

  setStep(1);

  // ---------------- loop ----------------
  var prev=0;
  (function loop(t){
    requestAnimationFrame(loop);
    var tt=(t||0)*0.001;
    var dt=Math.min(0.05,tt-prev); prev=tt;
    var e=Math.min(1,dt*2.2);

    for(var i=0;i<mixers.length;i++) mixers[i].update(dt);

    // mood lerp
    mood.ambI=num(mood.ambI,moodTo.ambI,e);
    mood.keyI=num(mood.keyI,moodTo.keyI,e);
    mood.keyY=num(mood.keyY,moodTo.keyY,e);
    mood.keyZ=num(mood.keyZ,moodTo.keyZ,e);
    mood.rimI=num(mood.rimI,moodTo.rimI,e);
    mood.rimZ=num(mood.rimZ,moodTo.rimZ,e);
    mood.fog=num(mood.fog,moodTo.fog,e);
    mood.flame=num(mood.flame,moodTo.flame,e);
    mood.expo=num(mood.expo,moodTo.expo,e);
    ambC.lerp(moodTo.cAmb,e); amb.color.copy(ambC); amb.intensity=mood.ambI;
    keyMul+=(keyWant-keyMul)*e;
    keyC.lerp(moodTo.cKey,e); key.color.copy(keyC); key.intensity=mood.keyI*keyMul;
    key.position.set(0,mood.keyY,mood.keyZ);
    rimC.lerp(moodTo.cRim,e); rim.color.copy(rimC); rim.intensity=mood.rimI;
    rim.position.set(0,2.6,mood.rimZ);
    embC.lerp(moodTo.cEmb,e); eMat.color.copy(embC);
    fogC.lerp(moodTo.cClear,e);
    sc.fog.density=mood.fog; sc.fog.color.copy(fogC); r.setClearColor(fogC);
    r.toneMappingExposure=mood.expo;
    key.target.position.set(0,Math.max(0.8,camTargetY),(step===4)?2.0:0);

    // camera settles into the framing the current step asked for
    cam.position.y+=(camTargetY-cam.position.y)*Math.min(1,dt*3.0);
    cam.lookAt(0,cam.position.y,0);

    // holders: appear, slide to their step position, turn
    var glide=Math.min(1,dt*2.6);
    for(var a=0;a<all.length;a++){
      var h=all[a].holder, u=h.userData;
      u.app+=(u.want-u.app)*Math.min(1,dt*3.4);
      u.k+=(u.tk-u.k)*glide; u.x+=(u.tx-u.x)*glide; u.z+=(u.tz-u.z)*glide;
      if(u.app<0.012&&u.want===0){ h.visible=false; continue; }
      h.visible=true;
      h.scale.setScalar(u.k*(0.9+0.1*u.app));
      h.position.set(u.x,(1-u.app)*-0.35,u.z);
      u.pool.material.opacity=0.26*u.app*(step===4?1.4:1);
      if(step===2) h.rotation.y+=dt*0.36;
      else h.rotation.y=Math.sin(tt*0.45+a)*0.28;
    }

    // fires
    for(var f=0;f<flames.length;f++){
      var fl=flames[f];
      var lvl=fl.base*mood.flame;
      fl.light.intensity=lvl+Math.sin(tt*12+fl.seed*7)*0.3*mood.flame+(Math.random()-0.5)*0.25*mood.flame;
      var fs=(1+Math.sin(tt*11+fl.seed*9)*0.08)*(0.55+0.45*mood.flame);
      fl.sprite.scale.set(0.85*fs,1.2*fs,1);
      fl.sprite.material.opacity=0.95*(0.35+0.65*mood.flame);
      fl.core.visible=mood.flame>0.5;
    }

    // embers
    var ea=eGeo.attributes.position.array;
    for(var k2=0;k2<EMBERS;k2++){
      var m=eMeta[k2];
      ea[k2*3+1]+=m.spd*(0.4+0.6*mood.flame);
      ea[k2*3]=m.f.x+m.jx+Math.sin(tt*1.6+m.ph)*0.13;
      ea[k2*3+2]=m.f.z+m.jz+Math.cos(tt*1.3+m.ph)*0.13;
      if(ea[k2*3+1]>m.f.y+3.4) ea[k2*3+1]=m.f.y-0.1;
    }
    eGeo.attributes.position.needsUpdate=true;

    // the gate seal breathes: the citadel is locked from the outside
    if(gate.visible){
      var sp=Math.sin(tt*1.4)*0.5+0.5;
      sealMat.opacity=0.35+sp*0.35;
      sealRing.rotation.z=tt*0.25;
      sealLight.intensity=0.9+sp*0.9;
    }

    r.render(sc,cam);
  })(0);
});
</script>
"""


def onboarding_html(vendor_js: str, monsters: list, collector: dict) -> str:
    """Render the first-run intro scene.

    ``vendor_js``  inlined <script> blocks, e.g. _vendor_js(["three.min.js", "GLTFLoader.js"])
    ``monsters``   five dicts of {name, model, color, clip, strand, trick}, in strand order
    ``collector``  {name, model, clip} for the Collector (skull.glb / Flying_Idle)
    """
    roster = []
    for m in (monsters or []):
        m = m or {}
        roster.append({
            "name": str(m.get("name", "") or ""),
            "strand": str(m.get("strand", "") or ""),
            "trick": str(m.get("trick", "") or ""),
            "color": str(m.get("color", "") or "#e08d6d"),
            "model": str(m.get("model", "") or ""),
            "clip": str(m.get("clip", "") or ""),
            "lift": float(m.get("lift", 0) or 0),
        })
    collector = collector or {}
    boss = {
        "name": str(collector.get("name", "") or "The Collector"),
        "model": str(collector.get("model", "") or COLLECTOR_MODEL),
        "clip": str(collector.get("clip", "") or COLLECTOR_CLIP),
        "lift": float(collector.get("lift", 0) or 0),
    }
    # Vendor last: the inlined library is never scanned for template tokens.
    return (ONBOARDING_TEMPLATE
            .replace("__ROSTER__", json.dumps(roster))
            .replace("__COLLECTOR__", json.dumps(boss))
            .replace("__VENDOR__", vendor_js or ""))
