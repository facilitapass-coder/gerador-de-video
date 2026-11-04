import { Audio, Video } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FONTE } from "./marca";
import palavras from "./vento-palavras.json";

// Reels "Como acompanhar o vento na sua cidade" · Ventusky.
// Linha do tempo (s): rosto 0–8 · temporal 8–16,7 · tela 16,7–70,93 · encerramento até 74,6.
const FPS = 30;
const T_TEMPORAL = 8.0;
const T_TELA = 16.7;
const T_FIM_TELA = 70.93;
export const DURACAO_VENTO = Math.round(74.6 * FPS);

const AMARELO = "#FFD23F";
const VERMELHO = "#FF3B30";
const FUNDO = "#07111F";

const fr = (s: number) => Math.round(s * FPS);
const ease = Easing.bezier(0.45, 0, 0.2, 1);
const sombraTexto = "0 4px 18px rgba(0,0,0,.65), 0 2px 4px rgba(0,0,0,.8)";

// ---------- trechos mantidos da gravação de tela (pausas longas removidas) ----------
const TRECHOS: [number, number][] = [
  [0, 2.6],
  [3.05, 8.2],
  [8.8, 17.8],
  [18.55, 29.15],
  [29.5, 39.3],
  [39.65, 43.5],
  [43.85, 57.0],
];
const origemTela = (local: number) => {
  let acc = 0;
  for (const [a, b] of TRECHOS) {
    const d = b - a;
    if (local < acc + d) return a + (local - acc);
    acc += d;
  }
  const [a, b] = TRECHOS[TRECHOS.length - 1];
  return b + (local - acc) + 0 * a;
};

// ---------- câmera sobre a gravação (coordenadas da tela 1436×796) ----------
const TELA_W = 1436;
const TELA_H = 796;
const VP = { x: 40, y: 360, w: 1000, h: 960 };
type Tomada = { t: number; cx: number; cy: number; s: number };
const TOMADAS: Tomada[] = [
  { t: 0, cx: 265, cy: 70, s: 2.7 }, // barra de endereço
  { t: 3.05, cx: 370, cy: 175, s: 2.3 }, // busca
  { t: 5.6, cx: 718, cy: 398, s: 1.36 }, // mapa
  { t: 8.8, cx: 190, cy: 410, s: 2.5 }, // menu velocidade
  { t: 11.4, cx: 700, cy: 320, s: 1.6 }, // aproximar
  { t: 14.0, cx: 1290, cy: 540, s: 2.3 }, // legenda de cores
  { t: 15.3, cx: 760, cy: 330, s: 1.5 }, // linhas de direção
  { t: 18.55, cx: 190, cy: 430, s: 2.5 }, // menu rajadas
  { t: 22.8, cx: 600, cy: 280, s: 2.2 }, // 40 km/h
  { t: 29.5, cx: 660, cy: 478, s: 1.6 }, // linha do tempo
  { t: 35.0, cx: 600, cy: 300, s: 2.0 }, // previsão em Maringá
  { t: 39.65, cx: 1290, cy: 540, s: 2.3 }, // gráfico de cores
  { t: 43.85, cx: 718, cy: 398, s: 1.36 }, // visão geral
];
const limitar = (c: number, tam: number, total: number) =>
  tam >= total ? total / 2 : Math.min(Math.max(c, tam / 2), total - tam / 2);
const camera = (src: number) => {
  let k = 0;
  for (let i = 0; i < TOMADAS.length; i++) if (TOMADAS[i].t <= src) k = i;
  const atual = TOMADAS[k];
  const ant = TOMADAS[Math.max(0, k - 1)];
  const p = k === 0 ? 1 : interpolate(src, [atual.t, atual.t + 0.6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  let s = ant.s + (atual.s - ant.s) * p;
  // empurrão lento contínuo
  s *= 1 + Math.min(src - atual.t, 6) * 0.006;
  const cx = limitar(ant.cx + (atual.cx - ant.cx) * p, VP.w / s, TELA_W);
  const cy = limitar(ant.cy + (atual.cy - ant.cy) * p, VP.h / s, TELA_H);
  return { s, cx, cy };
};

type Destaque = { de: number; ate: number; tipo: "ret" | "circ"; x: number; y: number; w: number; h: number; x2?: number };
const DESTAQUES: Destaque[] = [
  { de: 0.3, ate: 2.6, tipo: "ret", x: 148, y: 44, w: 140, h: 32 },
  { de: 3.1, ate: 4.3, tipo: "ret", x: 200, y: 108, w: 242, h: 44 },
  { de: 4.3, ate: 5.6, tipo: "ret", x: 214, y: 162, w: 322, h: 80 },
  { de: 8.85, ate: 10.05, tipo: "ret", x: 10, y: 405, w: 192, h: 34 },
  { de: 10.05, ate: 11.4, tipo: "ret", x: 10, y: 370, w: 192, h: 34 },
  { de: 13.4, ate: 14.0, tipo: "circ", x: 664, y: 276, w: 70, h: 70 },
  { de: 14.2, ate: 15.3, tipo: "ret", x: 1386, y: 380, w: 48, h: 316 },
  { de: 18.6, ate: 21.8, tipo: "ret", x: 10, y: 437, w: 174, h: 34 },
  { de: 21.8, ate: 22.8, tipo: "ret", x: 10, y: 402, w: 174, h: 34 },
  { de: 23.0, ate: 29.15, tipo: "circ", x: 578, y: 268, w: 80, h: 80 },
  { de: 29.6, ate: 35.0, tipo: "ret", x: 336, y: 712, w: 1032, h: 42 },
  { de: 31.0, ate: 35.0, tipo: "circ", x: 992, y: 732, w: 34, h: 34, x2: 612 },
  { de: 35.2, ate: 39.3, tipo: "circ", x: 572, y: 248, w: 70, h: 70 },
  { de: 39.8, ate: 43.5, tipo: "ret", x: 1386, y: 380, w: 48, h: 316 },
];

const PASSOS: { de: number; n: string; titulo: string }[] = [
  { de: 0, n: "PASSO 1", titulo: "Acesse ventusky.com" },
  { de: 3.05, n: "PASSO 2", titulo: "Busque sua cidade" },
  { de: 8.8, n: "PASSO 3", titulo: "Velocidade e direção" },
  { de: 18.55, n: "PASSO 4", titulo: "Rajadas de vento" },
  { de: 29.5, n: "PASSO 5", titulo: "Previsão das próximas horas" },
  { de: 43.85, n: "⚠️ IMPORTANTE", titulo: "Use com responsabilidade" },
];

// ---------- elementos ----------
const Pilula: React.FC<{ children: React.ReactNode; cor?: string; texto?: string; style?: React.CSSProperties }> = ({
  children,
  cor = AMARELO,
  texto = "#111",
  style,
}) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 12,
      backgroundColor: cor,
      color: texto,
      fontWeight: 800,
      borderRadius: 999,
      padding: "12px 28px",
      boxShadow: "0 10px 30px rgba(0,0,0,.35)",
      ...style,
    }}
  >
    {children}
  </div>
);

const pop = (frame: number, inicio: number, fps: number) =>
  spring({ frame: frame - inicio, fps, config: { damping: 11, stiffness: 160, mass: 0.7 } });

// Linhas de vento animadas (decoração)
const LinhasVento: React.FC<{ opacidade: number; seed?: number }> = ({ opacidade, seed = 1 }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ opacity: opacidade, pointerEvents: "none" }}>
      <svg width={1080} height={1920}>
        {Array.from({ length: 22 }).map((_, i) => {
          const y = ((i * 97 + seed * 31) % 1920) + 0;
          const vel = 9 + ((i * 7) % 8);
          const len = 160 + ((i * 53) % 220);
          const x = ((frame * vel + i * 211) % (1080 + len * 2)) - len;
          return (
            <line
              key={i}
              x1={x}
              y1={y}
              x2={x + len}
              y2={y - len * 0.18}
              stroke="white"
              strokeOpacity={0.12 + ((i * 13) % 10) / 60}
              strokeWidth={2 + (i % 3)}
              strokeLinecap="round"
            />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

// ---------- legendas dinâmicas ----------
type Palavra = { w: string; i: number; f: number };
const PALAVRAS = palavras as Palavra[];
const CHAVE = new Set([
  "tornado", "f2", "maringá", "180", "250", "km/h", "gratuito", "gratuita", "site", "direção", "velocidade",
  "intensidade", "ventusky.com", "rajadas", "40", "previsões", "previsão", "futuro", "gráfico", "simepar",
  "defesa", "civil", "estragos", "vento", "cidade",
]);
const limpa = (w: string) => w.toLowerCase().replace(/[.,!?;:"]+$/g, "");
const GRUPOS: Palavra[][] = (() => {
  const g: Palavra[][] = [];
  let atual: Palavra[] = [];
  PALAVRAS.forEach((p, idx) => {
    const prox = PALAVRAS[idx + 1];
    atual.push(p);
    const fimFrase = /[.,!?]$/.test(p.w);
    const pausa = prox ? prox.i - p.f > 0.45 : true;
    const cruzaCena = prox ? [T_TEMPORAL, T_TELA].some((c) => p.i < c && prox.i >= c) : true;
    if (atual.length >= 3 || fimFrase || pausa || cruzaCena) {
      g.push(atual);
      atual = [];
    }
  });
  if (atual.length) g.push(atual);
  return g;
})();

const Legenda: React.FC<{ topo: number }> = ({ topo }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const idx = GRUPOS.findIndex((g, i) => {
    const fim = GRUPOS[i + 1] ? Math.min(GRUPOS[i + 1][0].i, g[g.length - 1].f + 0.6) : g[g.length - 1].f + 0.6;
    return t >= g[0].i - 0.05 && t < fim;
  });
  if (idx < 0) return null;
  const g = GRUPOS[idx];
  const entrada = spring({ frame: frame - fr(g[0].i - 0.05), fps, config: { damping: 14, stiffness: 220 } });
  return (
    <div
      style={{
        position: "absolute",
        top: topo,
        left: 70,
        right: 70,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        columnGap: 20,
        rowGap: 4,
        transform: `translateY(${(1 - entrada) * 26}px) scale(${0.92 + entrada * 0.08})`,
        opacity: entrada,
      }}
    >
      {g.map((p, k) => {
        const ativa = t >= p.i - 0.03;
        const destaque = CHAVE.has(limpa(p.w));
        const pp = spring({ frame: frame - fr(p.i), fps, config: { damping: 10, stiffness: 260 } });
        return (
          <span
            key={k}
            style={{
              fontFamily: FONTE,
              fontWeight: 800,
              fontSize: destaque ? 72 : 64,
              textTransform: "uppercase",
              lineHeight: 1.12,
              color: destaque ? AMARELO : "white",
              opacity: ativa ? 1 : 0.55,
              transform: `scale(${ativa ? 1 + (1 - pp) * 0.18 : 1})`,
              display: "inline-block",
              WebkitTextStroke: "2px rgba(0,0,0,.55)",
              textShadow: sombraTexto,
            }}
          >
            {p.w.replace(/[,]$/, "")}
          </span>
        );
      })}
    </div>
  );
};

// ---------- CENA 1 · abertura ----------
const Abertura: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const punchF2 = spring({ frame: frame - fr(3.0), fps, config: { damping: 12, stiffness: 140 } });
  const zoom = interpolate(t, [0, 8], [1.0, 1.12]) + punchF2 * 0.04;
  const stamp = pop(frame, fr(2.95), fps);
  const vel = interpolate(t, [5.6, 7.3], [180, 250], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const velIn = pop(frame, fr(5.0), fps);
  const tremor = t > 5.6 && t < 7.4 ? Math.sin(frame * 2.3) * 4 : 0;
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill style={{ transform: `scale(${zoom})`, transformOrigin: "50% 40%" }}>
        <Video src={staticFile("vento/rosto1.mp4")} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, transparent 45%, rgba(0,0,0,.55) 100%)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, rgba(0,0,0,.55) 0%, transparent 28%, transparent 62%, rgba(0,0,0,.6) 100%)" }} />
      {t >= 2.95 ? (
        <div
          style={{
            position: "absolute",
            top: 250,
            width: "100%",
            display: "flex",
            justifyContent: "center",
            transform: `scale(${0.4 + stamp * 0.6}) rotate(${-4 + (1 - stamp) * -10}deg)`,
            opacity: Math.min(1, stamp * 1.5),
          }}
        >
          <Pilula cor={VERMELHO} texto="white" style={{ fontFamily: FONTE, fontSize: 58, letterSpacing: 2, padding: "14px 36px" }}>
            🌪️ TORNADO F2
          </Pilula>
        </div>
      ) : null}
      {t >= 5.0 ? (
        <div
          style={{
            position: "absolute",
            top: 380,
            width: "100%",
            textAlign: "center",
            fontFamily: FONTE,
            transform: `translateX(${tremor}px) scale(${0.6 + velIn * 0.4})`,
            opacity: velIn,
          }}
        >
          <div style={{ color: "white", fontWeight: 800, fontSize: 120, lineHeight: 1, textShadow: sombraTexto }}>
            {Math.round(vel)}
            <span style={{ fontSize: 56, color: AMARELO }}> km/h</span>
          </div>
          <div style={{ color: "rgba(255,255,255,.9)", fontWeight: 600, fontSize: 34, marginTop: 6, textShadow: sombraTexto }}>
            ventos de 180 a 250 km/h
          </div>
        </div>
      ) : null}
      {t >= 5.0 ? <LinhasVento opacidade={interpolate(t, [5, 5.6, 7.6, 8], [0, 0.8, 0.8, 0], { extrapolateRight: "clamp" })} /> : null}
    </AbsoluteFill>
  );
};

// ---------- CENA 2 · temporal (cortes rápidos) ----------
const TOMADAS_TEMPORAL = [5.2, 10.3, 21.2, 49.0];
const Temporal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = 8.7 / TOMADAS_TEMPORAL.length;
  const t = frame / fps;
  const gratis = pop(frame, fr(9.75 - T_TEMPORAL), fps);
  const itens = [
    { txt: "Direção", em: 11.8 },
    { txt: "Velocidade", em: 12.5 },
    { txt: "Intensidade", em: 13.3 },
  ];
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {TOMADAS_TEMPORAL.map((ini, i) => {
        const de = fr(i * dur);
        const local = frame - de;
        const z = interpolate(local, [0, fr(dur)], [1.04, 1.14]);
        return (
          <Sequence key={i} from={de} durationInFrames={fr(dur) + 1} layout="none">
            <AbsoluteFill style={{ transform: `scale(${z}) translateX(${i % 2 ? -10 : 10}px)` }}>
              <Video
                src={staticFile("vento/temporal.mp4")}
                trimBefore={fr(ini)}
                muted
                style={{ position: "absolute", height: 1920, width: Math.round((1920 * 1034) / 1518), left: (1080 - Math.round((1920 * 1034) / 1518)) / 2, top: 0, filter: "contrast(1.12) saturate(0.8) brightness(0.92)" }}
              />
            </AbsoluteFill>
          </Sequence>
        );
      })}
      {/* flash nos cortes */}
      {TOMADAS_TEMPORAL.map((_, i) => {
        const de = fr(i * dur);
        const o = interpolate(frame, [de, de + 4], [i === 0 ? 0.9 : 0.75, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return frame >= de && frame < de + 5 ? <AbsoluteFill key={i} style={{ backgroundColor: "white", opacity: o }} /> : null;
      })}
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, rgba(0,0,0,.6) 0%, transparent 30%, transparent 60%, rgba(0,0,0,.7) 100%)" }} />
      <div style={{ position: "absolute", top: 250, left: 60, fontFamily: FONTE }}>
        <Pilula cor="rgba(0,0,0,.55)" texto="white" style={{ fontSize: 32, fontWeight: 700, border: "2px solid rgba(255,255,255,.35)" }}>
          <span style={{ width: 16, height: 16, borderRadius: 8, backgroundColor: VERMELHO, opacity: Math.floor(t * 2) % 2 ? 0.3 : 1 }} />
          MARINGÁ · PR
        </Pilula>
      </div>
      {t >= 9.75 - T_TEMPORAL ? (
        <div
          style={{
            position: "absolute",
            top: 380,
            width: "100%",
            display: "flex",
            justifyContent: "center",
            transform: `scale(${0.5 + gratis * 0.5}) rotate(-3deg)`,
            opacity: Math.min(1, gratis * 1.4),
          }}
        >
          <Pilula style={{ fontFamily: FONTE, fontSize: 60, padding: "16px 40px" }}>SITE 100% GRATUITO</Pilula>
        </div>
      ) : null}
      <div style={{ position: "absolute", top: 520, width: "100%", display: "flex", justifyContent: "center", gap: 18, fontFamily: FONTE }}>
        {itens.map((it) => {
          const s = pop(frame, fr(it.em - T_TEMPORAL), fps);
          return t + T_TEMPORAL >= it.em ? (
            <div
              key={it.txt}
              style={{
                transform: `translateY(${(1 - s) * 40}px) scale(${0.7 + s * 0.3})`,
                opacity: s,
                backgroundColor: "white",
                color: FUNDO,
                fontWeight: 700,
                fontSize: 36,
                padding: "10px 24px",
                borderRadius: 16,
                boxShadow: "0 10px 30px rgba(0,0,0,.4)",
              }}
            >
              ✓ {it.txt}
            </div>
          ) : null;
        })}
      </div>
    </AbsoluteFill>
  );
};

// ---------- CENAS 3 a 5 · gravação de tela ----------
const Tela: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame / fps;
  const src = origemTela(local);
  const T = local + T_TELA;
  const { s, cx, cy } = camera(src);
  const tx = VP.w / 2 - cx * s;
  const ty = VP.h / 2 - cy * s;
  const entrada = spring({ frame, fps, config: { damping: 16, stiffness: 120 } });

  const passoIdx = PASSOS.reduce((acc, p, i) => (src >= p.de ? i : acc), 0);
  const passo = PASSOS[passoIdx];
  const passoIn = spring({ frame: frame - fr(Math.max(0, tempoLocal(passo.de))), fps, config: { damping: 14, stiffness: 180 } });

  // badge 40 km/h
  const b40 = src >= 28.0 && src < 29.15 ? pop(frame, fr(tempoLocal(28.0)), fps) : 0;
  // aviso final
  const avisos = [
    { txt: "É uma PREVISÃO", em: 59.4 },
    { txt: "NÃO identifica tornado", em: 61.3 },
    { txt: "NÃO substitui Simepar e Defesa Civil", em: 67.0 },
  ];
  const cardIn = T >= 57.9 ? pop(frame, fr(57.9 - T_TELA), fps) : 0;

  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 35%, #12305a 0%, ${FUNDO} 70%)`, fontFamily: FONTE }}>
      <LinhasVento opacidade={0.35} seed={3} />
      {/* passo atual */}
      <div
        key={passoIdx}
        style={{
          position: "absolute",
          top: 230,
          width: "100%",
          textAlign: "center",
          transform: `translateY(${(1 - passoIn) * -30}px)`,
          opacity: passoIn,
        }}
      >
        <div style={{ display: "inline-block", backgroundColor: passoIdx === 5 ? VERMELHO : AMARELO, color: passoIdx === 5 ? "white" : "#111", fontWeight: 800, fontSize: 26, letterSpacing: 3, padding: "6px 18px", borderRadius: 10 }}>
          {passo.n}
        </div>
        <div style={{ color: "white", fontWeight: 800, fontSize: 52, marginTop: 8, textShadow: sombraTexto }}>{passo.titulo}</div>
      </div>

      {/* janela com a tela */}
      <div
        style={{
          position: "absolute",
          left: VP.x,
          top: VP.y,
          width: VP.w,
          height: VP.h,
          borderRadius: 30,
          overflow: "hidden",
          backgroundColor: "#0b1626",
          boxShadow: "0 30px 80px rgba(0,0,0,.55), 0 0 0 3px rgba(255,255,255,.12)",
          transform: `scale(${0.85 + entrada * 0.15})`,
          opacity: entrada,
        }}
      >
        <div
          style={{
            position: "absolute",
            width: TELA_W,
            height: TELA_H,
            transformOrigin: "0 0",
            transform: `translate(${tx}px, ${ty}px) scale(${s})`,
          }}
        >
          <Video src={staticFile("vento/tela.mp4")} muted style={{ width: TELA_W, height: TELA_H }} />
          <svg width={TELA_W} height={TELA_H} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
            {DESTAQUES.filter((d) => src >= d.de && src < d.ate).map((d, i) => {
              const p = interpolate(src, [d.de, d.de + 0.35], [0, 1], { extrapolateRight: "clamp", easing: ease });
              const saida = interpolate(src, [d.ate - 0.15, d.ate], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
              const pulso = 1 + Math.sin(frame / 4) * 0.04;
              const sw = 5 / s;
              const glow = `drop-shadow(0 0 ${8 / s}px ${AMARELO})`;
              if (d.tipo === "ret") {
                const per = 2 * (d.w + d.h) + 40;
                return (
                  <rect
                    key={i}
                    x={d.x - 6}
                    y={d.y - 6}
                    width={d.w + 12}
                    height={d.h + 12}
                    rx={10}
                    fill={`rgba(255,210,63,${0.12 * p})`}
                    stroke={AMARELO}
                    strokeWidth={sw}
                    strokeDasharray={per}
                    strokeDashoffset={per * (1 - p)}
                    opacity={saida}
                    style={{ filter: glow }}
                  />
                );
              }
              const cxp = d.x2 !== undefined ? interpolate(src, [32.4, 33.6], [d.x, d.x2], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease }) : d.x;
              const r = (d.w / 2) * pulso;
              const per = 2 * Math.PI * r;
              return (
                <circle
                  key={i}
                  cx={cxp}
                  cy={d.y}
                  r={r}
                  fill="none"
                  stroke={AMARELO}
                  strokeWidth={sw}
                  strokeDasharray={per}
                  strokeDashoffset={per * (1 - p)}
                  opacity={saida}
                  style={{ filter: glow }}
                />
              );
            })}
          </svg>
        </div>

        {/* rótulos fixos dentro da janela */}
        {src >= 15.4 && src < 17.8 ? (
          <div style={{ position: "absolute", bottom: 40, width: "100%", display: "flex", justifyContent: "center" }}>
            <Pilula style={{ fontSize: 34, opacity: pop(frame, fr(tempoLocal(15.4)), fps) }}>〰️ As linhas mostram a direção do vento</Pilula>
          </div>
        ) : null}
        {src >= 14.2 && src < 15.3 ? (
          <div style={{ position: "absolute", top: 40, left: 40 }}>
            <Pilula style={{ fontSize: 34, opacity: pop(frame, fr(tempoLocal(14.2)), fps) }}>🎨 Cor = velocidade (km/h)</Pilula>
          </div>
        ) : null}
        {src >= 39.8 && src < 43.5 ? (
          <div style={{ position: "absolute", top: 40, left: 40 }}>
            <Pilula style={{ fontSize: 34, opacity: pop(frame, fr(tempoLocal(39.8)), fps) }}>🎨 Escala de cores em km/h</Pilula>
          </div>
        ) : null}
        {src >= 29.6 && src < 35.0 ? (
          <div style={{ position: "absolute", top: 40, width: "100%", display: "flex", justifyContent: "center" }}>
            <Pilula style={{ fontSize: 34, opacity: pop(frame, fr(tempoLocal(29.6)), fps) }}>👆 Arraste para ver as próximas horas</Pilula>
          </div>
        ) : null}
        {b40 > 0 ? (
          <div style={{ position: "absolute", top: 90, width: "100%", textAlign: "center", transform: `scale(${0.5 + b40 * 0.5})`, opacity: b40 }}>
            <Pilula cor={VERMELHO} texto="white" style={{ fontSize: 70, padding: "14px 40px" }}>
              💨 40 km/h
            </Pilula>
          </div>
        ) : null}

        {/* card de aviso */}
        {cardIn > 0 ? (
          <div
            style={{
              position: "absolute",
              left: 50,
              right: 50,
              bottom: 50,
              backgroundColor: "rgba(10,16,28,.92)",
              border: `3px solid ${VERMELHO}`,
              borderRadius: 28,
              padding: "30px 36px",
              transform: `translateY(${(1 - cardIn) * 80}px)`,
              opacity: cardIn,
            }}
          >
            <div style={{ color: VERMELHO, fontWeight: 800, fontSize: 40, letterSpacing: 1 }}>⚠️ ATENÇÃO</div>
            {avisos.map((a) => {
              const k = T >= a.em ? pop(frame, fr(a.em - T_TELA), fps) : 0;
              return (
                <div
                  key={a.txt}
                  style={{ color: "white", fontWeight: 700, fontSize: 40, marginTop: 14, opacity: k, transform: `translateX(${(1 - k) * -40}px)` }}
                >
                  {a.txt}
                </div>
              );
            })}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
// tempo local da cena de tela a partir do tempo da gravação original
function tempoLocal(src: number) {
  let acc = 0;
  for (const [a, b] of TRECHOS) {
    if (src < b) return acc + Math.max(0, src - a);
    acc += b - a;
  }
  return acc;
}

// ---------- CENA 6 · encerramento ----------
const Encerramento: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const a = pop(frame, 4, fps);
  const b = pop(frame, 14, fps);
  const icones = pop(frame, 24, fps);
  return (
    <AbsoluteFill style={{ backgroundColor: "black", fontFamily: FONTE }}>
      <AbsoluteFill style={{ transform: `scale(${1.08 + t * 0.03})` }}>
        <Img src={staticFile("vento/rosto_final.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "blur(6px) brightness(.55)" }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, rgba(7,17,31,.2) 0%, rgba(7,17,31,.85) 80%)" }} />
      <LinhasVento opacidade={0.4} seed={7} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", textAlign: "center", padding: "0 70px" }}>
        <div style={{ color: "white", fontWeight: 800, fontSize: 104, lineHeight: 1.02, transform: `scale(${0.6 + a * 0.4})`, opacity: a, textShadow: sombraTexto }}>
          SALVE
        </div>
        <div style={{ color: AMARELO, fontWeight: 800, fontSize: 104, lineHeight: 1.02, transform: `scale(${0.6 + a * 0.4})`, opacity: a, textShadow: sombraTexto }}>
          E COMPARTILHE
        </div>
        <div style={{ color: "white", fontWeight: 800, fontSize: 72, lineHeight: 1.1, marginTop: 6, transform: `scale(${0.6 + b * 0.4})`, opacity: b, textShadow: sombraTexto }}>
          ESTE VÍDEO!
        </div>
        <div style={{ display: "flex", gap: 60, marginTop: 60, transform: `translateY(${(1 - icones) * 60}px)`, opacity: icones }}>
          {/* salvar */}
          <svg width={120} height={120} viewBox="0 0 24 24" style={{ transform: `rotate(${Math.sin(frame / 5) * 6}deg)` }}>
            <path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4.5L5 21V4a1 1 0 0 1 1-1z" fill={AMARELO} />
          </svg>
          {/* compartilhar */}
          <svg width={120} height={120} viewBox="0 0 24 24" style={{ transform: `rotate(${Math.sin(frame / 5 + 1.5) * 6}deg)` }}>
            <path d="M22 2 11 13" stroke="white" strokeWidth={2.2} strokeLinecap="round" />
            <path d="M22 2 15 22l-4-9-9-4 20-7z" fill="white" />
          </svg>
        </div>
        <div style={{ color: "rgba(255,255,255,.85)", fontWeight: 600, fontSize: 34, marginTop: 40, opacity: icones }}>
          Mande pra quem mora em Maringá 💨
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------- composição ----------
export const VentoMaringa: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const volMusica = (f: number) => {
    const s = f / FPS;
    if (s >= T_FIM_TELA - 0.3) return interpolate(s, [T_FIM_TELA - 0.3, T_FIM_TELA + 0.4], [0.32, 0.95], { extrapolateRight: "clamp" });
    return 0.32;
  };
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Sequence durationInFrames={fr(T_TEMPORAL)}>
        <Abertura />
      </Sequence>
      <Sequence from={fr(T_TEMPORAL)} durationInFrames={fr(T_TELA - T_TEMPORAL)}>
        <Temporal />
      </Sequence>
      <Sequence from={fr(T_TELA)} durationInFrames={fr(T_FIM_TELA - T_TELA)}>
        <Tela />
      </Sequence>
      <Sequence from={fr(T_FIM_TELA)}>
        <Encerramento />
      </Sequence>
      {/* flash de transição entre cenas */}
      {[T_TEMPORAL, T_TELA, T_FIM_TELA].map((c) => {
        const d = t - c;
        return d >= 0 && d < 0.2 ? <AbsoluteFill key={c} style={{ backgroundColor: "white", opacity: 0.8 * (1 - d / 0.2) }} /> : null;
      })}
      {t < T_FIM_TELA ? <Legenda topo={t < T_TELA ? 1330 : 1350} /> : null}
      <Audio src={staticFile("vento/voz.wav")} />
      <Audio src={staticFile("vento/musica.wav")} volume={volMusica} />
    </AbsoluteFill>
  );
};
