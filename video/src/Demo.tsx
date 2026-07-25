import React from 'react';
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';

export const FPS = 30;
const TOTAL_SEC = 120;
export const TOTAL_FRAMES = TOTAL_SEC * FPS;

const C = {
  bg: '#0b0710',
  ink: '#f2e8dc',
  muted: '#cbb8a4',
  accent: '#e08d6d',
  gold: '#ffd87a',
};
const FONT = "'Trebuchet MS','DejaVu Sans',Verdana,sans-serif";
const GRAD = `linear-gradient(135deg,#ffe9d6 25%,${C.accent} 70%,#b98868)`;

type Cap = {text: string; from: number; dur?: number; gold?: boolean};
type Clip = {
  kind: 'clip' | 'phone';
  sec: number;
  src: string;
  from: number;
  rate?: number;
  caps: Cap[];
};
type Card = {kind: 'title' | 'hook' | 'closing'; sec: number; caps?: Cap[]};
type Scene = Clip | Card;

// Source timestamps come from the scripted capture (desktop-beats.json).
const SCENES: Scene[] = [
  {kind: 'title', sec: 6},
  {kind: 'hook', sec: 8.5},
  {kind: 'clip', sec: 6.5, src: 'desktop.webm', from: 12.0, caps: [
    {text: 'Tell the citadel your name — the monsters will use it.', from: 0.4},
  ]},
  {kind: 'clip', sec: 7.5, src: 'desktop.webm', from: 25.7, caps: [
    {text: 'Five monsters, one per curriculum strand — each one IS a wrong idea that feels right.', from: 0.3, dur: 4.6},
    {text: 'And one more, for students who keep slipping…', from: 5.1, gold: true},
  ]},
  {kind: 'clip', sec: 9, src: 'desktop.webm', from: 61.5, rate: 1.32, caps: [
    {text: 'The nexus. Streamlit + three.js + Gemma 4 through Ollama — everything on one laptop.', from: 0.6},
  ]},
  {kind: 'clip', sec: 7.6, src: 'desktop.webm', from: 136.6, caps: [
    {text: 'Pick your battle. Equazor guards Algebra.', from: 0.4},
  ]},
  {kind: 'clip', sec: 7.6, src: 'desktop.webm', from: 144.6, caps: [
    {text: 'Into its lair.', from: 0.5, dur: 3.4},
    {text: 'It already remembers you.', from: 4.2, gold: true},
  ]},
  {kind: 'clip', sec: 11, src: 'desktop.webm', from: 157.2, rate: 2.4, caps: [
    {text: 'Its questions are bent around its favourite snare.', from: 0.3, dur: 4.6},
    {text: 'We answer wrong the way real students do — the minus sign slips.', from: 5.2},
  ]},
  {kind: 'clip', sec: 9.6, src: 'desktop.webm', from: 184.3, caps: [
    {text: 'The wrong answer NAMES the wrong idea — a verified lookup, not a model guess.', from: 0.3, dur: 4.6},
    {text: 'Gemma explains why the method fails — grounded in the verified solution.', from: 5.1},
  ]},
  {kind: 'clip', sec: 11.5, src: 'desktop.webm', from: 194.8, rate: 1.62, caps: [
    {text: 'The training loop asks HOW you got your answer.', from: 0.3, dur: 4.8},
    {text: 'Right answer, thin reasoning? It does not count. The streak stays at zero.', from: 5.4, gold: true},
  ]},
  {kind: 'clip', sec: 9, src: 'desktop.webm', from: 214.0, rate: 1.45, caps: [
    {text: 'Miss again, and Gemma reads your own words — then switches teaching strategy, and says why.', from: 0.4},
  ]},
  {kind: 'clip', sec: 6.8, src: 'desktop.webm', from: 228.0, caps: [
    {text: 'Everything the agent learns goes home in plain language — with printable practice.', from: 0.3},
  ]},
  {kind: 'phone', sec: 10, src: 'phone.webm', from: 24.0, rate: 2, caps: [
    {text: 'And the whole citadel fits in a pocket.', from: 0.5},
  ]},
];

const usedSec = SCENES.reduce((a, s) => a + s.sec, 0);
SCENES.push({kind: 'closing', sec: TOTAL_SEC - usedSec});

const Panel: React.FC<{cap: Cap; durF: number}> = ({cap, durF}) => {
  const f = useCurrentFrame();
  const start = Math.round(cap.from * FPS);
  const end = cap.dur ? Math.min(durF - 4, start + Math.round(cap.dur * FPS)) : durF - 6;
  if (f < start || f > end) return null;
  const t = f - start;
  const span = end - start;
  const o = interpolate(t, [0, 10, span - 8, span], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const y = interpolate(t, [0, 12], [16, 0], {extrapolateRight: 'clamp'});
  return (
    <div
      style={{
        position: 'absolute',
        left: 64,
        bottom: 56,
        maxWidth: 1100,
        transform: `translateY(${y}px)`,
        opacity: o,
        background: 'rgba(14,8,13,0.84)',
        borderLeft: `6px solid ${C.accent}`,
        borderRadius: 12,
        padding: '20px 30px',
        fontFamily: FONT,
        fontSize: 36,
        lineHeight: 1.38,
        fontWeight: 700,
        color: cap.gold ? C.gold : C.ink,
        textShadow: '0 2px 8px rgba(0,0,0,.8)',
      }}
    >
      {cap.text}
    </div>
  );
};

const EdgeFade: React.FC<{durF: number}> = ({durF}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 9, durF - 9, durF], [1, 0, 0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return <AbsoluteFill style={{background: '#000', opacity: o}} />;
};

const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        'radial-gradient(ellipse 82% 72% at 50% 44%, transparent 58%, rgba(4,3,8,.52) 100%)',
    }}
  />
);

const ClipScene: React.FC<{s: Clip; durF: number}> = ({s, durF}) => (
  <AbsoluteFill style={{background: '#000'}}>
    <OffthreadVideo
      muted
      src={staticFile(s.src)}
      startFrom={Math.round(s.from * FPS)}
      playbackRate={s.rate ?? 1}
      style={{width: '100%', height: '100%', objectFit: 'cover'}}
    />
    <Vignette />
    {s.caps.map((c, i) => (
      <Panel key={i} cap={c} durF={durF} />
    ))}
    <EdgeFade durF={durF} />
  </AbsoluteFill>
);

const PhoneScene: React.FC<{s: Clip; durF: number}> = ({s, durF}) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(ellipse 60% 55% at 50% 42%, #1c1119 0%, ${C.bg} 70%)`,
      alignItems: 'center',
      justifyContent: 'center',
    }}
  >
    <div
      style={{
        width: 424,
        height: 920,
        borderRadius: 38,
        overflow: 'hidden',
        border: '3px solid rgba(224,141,109,.55)',
        boxShadow: '0 30px 90px rgba(0,0,0,.8), 0 0 60px rgba(224,141,109,.25)',
      }}
    >
      <OffthreadVideo
        muted
        src={staticFile(s.src)}
        startFrom={Math.round(s.from * FPS)}
        playbackRate={s.rate ?? 1}
        style={{width: '100%', height: '100%', objectFit: 'cover'}}
      />
    </div>
    {s.caps.map((c, i) => (
      <Panel key={i} cap={c} durF={durF} />
    ))}
    <EdgeFade durF={durF} />
  </AbsoluteFill>
);

const BigTitle: React.FC<{size?: number}> = ({size = 148}) => (
  <div
    style={{
      fontFamily: FONT,
      fontSize: size,
      fontWeight: 900,
      letterSpacing: '-2px',
      textTransform: 'uppercase',
      background: GRAD,
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      filter: 'drop-shadow(0 0 28px rgba(224,141,109,.5))',
    }}
  >
    Gemma Monsters
  </div>
);

const TitleScene: React.FC<{durF: number}> = ({durF}) => {
  const f = useCurrentFrame();
  const scale = interpolate(f, [0, durF], [0.96, 1.02]);
  const o1 = interpolate(f, [4, 20], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const o2 = interpolate(f, [22, 38], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const o3 = interpolate(f, [40, 56], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse 70% 60% at 50% 38%, #1c1119 0%, ${C.bg} 75%)`,
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
      }}
    >
      <div style={{transform: `scale(${scale})`}}>
        <div style={{opacity: o1}}>
          <BigTitle />
        </div>
        <div
          style={{
            opacity: o2,
            fontFamily: FONT,
            fontSize: 46,
            color: C.muted,
            marginTop: 14,
          }}
        >
          The math tutor that fights back.
        </div>
        <div
          style={{
            opacity: o3,
            display: 'inline-block',
            marginTop: 44,
            padding: '14px 34px',
            border: `1px solid ${C.accent}`,
            borderRadius: 999,
            fontFamily: FONT,
            fontSize: 30,
            fontWeight: 800,
            letterSpacing: '.14em',
            textTransform: 'uppercase',
            color: C.gold,
          }}
        >
          Built on Gemma 4 · fully on-device with Ollama
        </div>
      </div>
      <EdgeFade durF={durF} />
    </AbsoluteFill>
  );
};

const HOOK_LINES: Array<{text: string; at: number; gold?: boolean}> = [
  {text: 'Ask a Grade 9 student:  what is 2/3 + 1/4 ?', at: 0.3},
  {text: 'Many will answer 3/7 — tops with tops, bottoms with bottoms.', at: 2.8},
  {text: 'That rule feels completely right. Marking it wrong teaches nothing.', at: 5.4, gold: true},
];

const HookScene: React.FC<{durF: number}> = ({durF}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        background: C.bg,
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div style={{maxWidth: 1350, textAlign: 'center'}}>
        {HOOK_LINES.map((l, i) => {
          const s = Math.round(l.at * FPS);
          const o = interpolate(f, [s, s + 14], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const y = interpolate(f, [s, s + 14], [14, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return (
            <div
              key={i}
              style={{
                opacity: o,
                transform: `translateY(${y}px)`,
                fontFamily: FONT,
                fontSize: i === 0 ? 62 : 50,
                fontWeight: i === 0 ? 900 : 700,
                lineHeight: 1.35,
                color: l.gold ? C.gold : i === 0 ? C.ink : C.muted,
                marginTop: i === 0 ? 0 : 38,
              }}
            >
              {l.text}
            </div>
          );
        })}
      </div>
      <EdgeFade durF={durF} />
    </AbsoluteFill>
  );
};

const ClosingScene: React.FC<{durF: number}> = ({durF}) => {
  const f = useCurrentFrame();
  const o1 = interpolate(f, [4, 20], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const o2 = interpolate(f, [26, 42], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const o3 = interpolate(f, [50, 66], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const o4 = interpolate(f, [74, 90], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse 70% 60% at 50% 40%, #1c1119 0%, ${C.bg} 75%)`,
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
      }}
    >
      <div style={{opacity: o1}}>
        <BigTitle size={116} />
      </div>
      <div
        style={{
          opacity: o2,
          fontFamily: FONT,
          fontSize: 46,
          fontWeight: 800,
          color: C.ink,
          marginTop: 34,
        }}
      >
        No cloud. No accounts. Wi-Fi off — it keeps going.
      </div>
      <div
        style={{
          opacity: o3,
          fontFamily: FONT,
          fontSize: 38,
          color: C.muted,
          marginTop: 16,
        }}
      >
        A student's mistakes never leave the house.
      </div>
      <div
        style={{
          opacity: o4,
          fontFamily: FONT,
          fontSize: 30,
          fontWeight: 800,
          letterSpacing: '.16em',
          textTransform: 'uppercase',
          color: C.gold,
          marginTop: 52,
        }}
      >
        Gemma 4 · Ollama · Streamlit · three.js
      </div>
      <div
        style={{
          opacity: o4,
          fontFamily: FONT,
          fontSize: 27,
          color: C.muted,
          marginTop: 18,
        }}
      >
        github.com/EdTechDL/gemma-without-borders
      </div>
      <Audio src={staticFile('correct.mp3')} volume={0.5} />
      <EdgeFade durF={durF} />
    </AbsoluteFill>
  );
};

export const Demo: React.FC = () => {
  let acc = 0;
  const seqs = SCENES.map((s, i) => {
    const durF = Math.round(s.sec * FPS);
    const fromF = acc;
    acc += durF;
    let node: React.ReactNode;
    if (s.kind === 'clip') node = <ClipScene s={s} durF={durF} />;
    else if (s.kind === 'phone') node = <PhoneScene s={s} durF={durF} />;
    else if (s.kind === 'title') node = <TitleScene durF={durF} />;
    else if (s.kind === 'hook') node = <HookScene durF={durF} />;
    else node = <ClosingScene durF={durF} />;
    return (
      <Sequence key={i} from={fromF} durationInFrames={durF}>
        {node}
      </Sequence>
    );
  });
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {seqs}
      <Audio
        loop
        src={staticFile('nexus-theme.mp3')}
        volume={(f) =>
          interpolate(
            f,
            [0, 40, TOTAL_FRAMES - 90, TOTAL_FRAMES - 5],
            [0, 0.42, 0.42, 0],
            {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
          )
        }
      />
    </AbsoluteFill>
  );
};
