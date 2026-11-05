import { Audio, Video } from "@remotion/media";
import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { BEGE, FONTE, LARANJA, MARINHO } from "./marca";
import palavras from "./gramado-palavras.json";

// Reels oferta Gramado · fala real (IMG_2386) com cards animados da oferta.
// Fala 0–22,33 s + card final até 24,3 s.
const FPS = 30;
const FIM_FALA = 22.33;
export const DURACAO_GRAMADO = Math.round(24.3 * FPS);
const fr = (s: number) => Math.round(s * FPS);
const ease = Easing.bezier(0.45, 0, 0.2, 1);
const sombra = "0 4px 18px rgba(0,0,0,.55), 0 2px 4px rgba(0,0,0,.7)";
const VERDE_WPP = "#25D366";

// cortes secos (jump cut) nas palavras fortes: alterna o enquadramento
const CORTES = [1.63, 2.95, 6.17, 8.96, 11.0, 13.39, 16.68, 19.1];

type Palavra = { w: string; i: number; f: number };
const PALAVRAS = palavras as Palavra[];
const DESTAQUES = new Set(["gramado", "15", "r$", "288", "duas", "pessoas", "maio", "2027", "aéreo", "maringá", "quatro", "noites", "café", "manhã", "transfer", "porto", "alegre", "ida", "volta", "chama", "detalhes"]);
const limpa = (w: string) => w.toLowerCase().replace(/[.,!?]+$/, "");

const molaPop = (frame: number, ini: number, fps: number) => spring({ frame: frame - ini, fps, config: { damping: 11, stiffness: 170, mass: 0.7 } });

const Janela: React.FC<{ de: number; ate: number; children: (k: number, saida: number) => React.ReactNode }> = ({ de, ate, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t < de || t >= ate) return null;
  const k = molaPop(frame, fr(de), fps);
  const saida = interpolate(t, [ate - 0.18, ate], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return <>{children(k, saida)}</>;
};

// ---------- legenda palavra a palavra ----------
const GRUPOS: Palavra[][] = (() => {
  const g: Palavra[][] = [];
  let a: Palavra[] = [];
  PALAVRAS.forEach((p, i) => {
    a.push(p);
    const prox = PALAVRAS[i + 1];
    if (a.length >= 3 || /[.,!?]$/.test(p.w) || !prox || prox.i - p.f > 0.4) {
      g.push(a);
      a = [];
    }
  });
  return g;
})();

const Legenda: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const idx = GRUPOS.findIndex((g, i) => t >= g[0].i - 0.05 && t < (GRUPOS[i + 1] ? GRUPOS[i + 1][0].i : g[g.length - 1].f + 0.4));
  if (idx < 0 || t >= FIM_FALA) return null;
  const g = GRUPOS[idx];
  const e = spring({ frame: frame - fr(g[0].i - 0.05), fps, config: { damping: 14, stiffness: 220 } });
  return (
    <div style={{ position: "absolute", top: 1425, left: 70, right: 70, display: "flex", flexWrap: "wrap", justifyContent: "center", columnGap: 18, transform: `translateY(${(1 - e) * 22}px)`, opacity: e }}>
      {g.map((p, k) => {
        const ativa = t >= p.i - 0.03;
        const dest = DESTAQUES.has(limpa(p.w));
        const pp = spring({ frame: frame - fr(p.i), fps, config: { damping: 10, stiffness: 260 } });
        return (
          <span
            key={k}
            style={{
              fontFamily: FONTE,
              fontWeight: 700,
              fontSize: dest ? 66 : 60,
              textTransform: "uppercase",
              color: dest ? LARANJA : "white",
              opacity: ativa ? 1 : 0.5,
              transform: `scale(${ativa ? 1 + (1 - pp) * 0.16 : 1})`,
              display: "inline-block",
              WebkitTextStroke: dest ? "2px rgba(255,255,255,.0)" : "2px rgba(0,0,0,.45)",
              textShadow: sombra,
              lineHeight: 1.1,
            }}
          >
            {p.w.replace(/,$/, "")}
          </span>
        );
      })}
    </div>
  );
};

// ---------- cards da oferta (altura do peito) ----------
const Card: React.FC<{ k: number; saida: number; children: React.ReactNode; fundo?: string }> = ({ k, saida, children, fundo = "white" }) => (
  <div
    style={{
      position: "absolute",
      left: 70,
      right: 70,
      top: 1100,
      display: "flex",
      justifyContent: "center",
      transform: `translateY(${(1 - k) * 90}px) scale(${0.85 + 0.15 * k})`,
      opacity: Math.min(1, k * 1.4) * saida,
    }}
  >
    <div style={{ backgroundColor: fundo, borderRadius: 34, padding: "26px 40px", boxShadow: "0 22px 60px rgba(0,0,0,.35)", fontFamily: FONTE, width: "100%" }}>{children}</div>
  </div>
);

const Preco: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <Janela de={1.55} ate={6.17}>
      {(k, saida) => {
        const p288 = molaPop(frame, fr(2.95), fps);
        const p2 = molaPop(frame, fr(4.64), fps);
        return (
          <Card k={k} saida={saida}>
            <div style={{ color: MARINHO, fontWeight: 500, fontSize: 32 }}>a partir de</div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 18 }}>
              <span style={{ color: MARINHO, fontWeight: 700, fontSize: 92, lineHeight: 1 }}>15x</span>
              <span style={{ color: LARANJA, fontWeight: 700, fontSize: 118, lineHeight: 1, display: "inline-block", transform: `scale(${0.6 + 0.4 * p288})`, opacity: p288, transformOrigin: "left bottom" }}>R$ 288</span>
            </div>
            <div style={{ color: MARINHO, fontWeight: 600, fontSize: 40, marginTop: 6, opacity: p2, transform: `translateX(${(1 - p2) * -30}px)` }}>para 2 pessoas 💑</div>
          </Card>
        );
      }}
    </Janela>
  );
};

const Data: React.FC = () => (
  <Janela de={6.17} ate={8.96}>
    {(k, saida) => (
      <Card k={k} saida={saida} fundo={MARINHO}>
        <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
          <div style={{ backgroundColor: "white", borderRadius: 20, width: 180, overflow: "hidden", textAlign: "center", flexShrink: 0 }}>
            <div style={{ backgroundColor: LARANJA, color: "white", fontWeight: 700, fontSize: 30, padding: "6px 0" }}>MAIO</div>
            <div style={{ color: MARINHO, fontWeight: 700, fontSize: 56, lineHeight: 1.3 }}>2027</div>
          </div>
          <div>
            <div style={{ color: BEGE, fontWeight: 500, fontSize: 34 }}>Temos disponibilidade</div>
            <div style={{ color: "white", fontWeight: 700, fontSize: 58, lineHeight: 1.1 }}>para maio de 2027</div>
          </div>
        </div>
      </Card>
    )}
  </Janela>
);

const ITENS = [
  { em: 8.96, icone: "✈️", texto: "Aéreo saindo de Maringá" },
  { em: 11.0, icone: "🏨", texto: "4 noites com café da manhã" },
  { em: 13.39, icone: "🚐", texto: "Transfer Porto Alegre ↔ Gramado" },
];
const Inclui: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <Janela de={8.96} ate={16.68}>
      {(k, saida) => (
        <Card k={k} saida={saida}>
          <div style={{ color: LARANJA, fontWeight: 700, fontSize: 26, letterSpacing: 2, marginBottom: 4 }}>O PACOTE INCLUI</div>
          {ITENS.map((it) => {
            const p = molaPop(frame, fr(it.em), fps);
            return (
              <div key={it.texto} style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 6, opacity: frame >= fr(it.em) ? p : 0, transform: `translateX(${(1 - p) * -50}px)` }}>
                <div style={{ width: 52, height: 52, borderRadius: 26, backgroundColor: BEGE, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28, flexShrink: 0 }}>{it.icone}</div>
                <div style={{ color: MARINHO, fontWeight: 600, fontSize: 36, lineHeight: 1.12 }}>
                  {it.texto}
                  {it.icone === "🚐" ? <div style={{ fontWeight: 500, fontSize: 26, color: LARANJA }}>ida e volta</div> : null}
                </div>
              </div>
            );
          })}
        </Card>
      )}
    </Janela>
  );
};

const Chamada: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <Janela de={16.68} ate={FIM_FALA}>
      {(k, saida) => {
        const b = molaPop(frame, fr(19.1), fps);
        const pulso = frame >= fr(19.6) ? 1 + Math.sin((frame - fr(19.6)) / 4) * 0.03 : 1;
        return (
          <div style={{ position: "absolute", left: 70, right: 70, top: 1110, textAlign: "center", fontFamily: FONTE, opacity: Math.min(1, k * 1.4) * saida }}>
            <div style={{ color: "white", fontWeight: 700, fontSize: 50, textShadow: sombra, transform: `translateY(${(1 - k) * 40}px)` }}>Quer garantir essa data? 👇</div>
            <div
              style={{
                marginTop: 26,
                display: "inline-flex",
                alignItems: "center",
                gap: 18,
                backgroundColor: VERDE_WPP,
                color: "white",
                fontWeight: 700,
                fontSize: 46,
                padding: "22px 44px",
                borderRadius: 999,
                boxShadow: "0 18px 50px rgba(0,0,0,.35)",
                transform: `scale(${(0.5 + 0.5 * b) * pulso})`,
                opacity: frame >= fr(19.1) ? b : 0,
              }}
            >
              <svg width={52} height={52} viewBox="0 0 24 24">
                <path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.5-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.4.6-.4.4c-.1.1-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.4 2.4 1.5.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.7-.1l1.9.9c.3.1.5.2.5.3.1.2.1.6-.1 1.1z" fill="white" />
              </svg>
              Chama no WhatsApp
            </div>
          </div>
        );
      }}
    </Janela>
  );
};

// ---------- título GRAMADO no topo ----------
const Titulo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t >= FIM_FALA) return null;
  const slam = spring({ frame, fps, config: { damping: 9, stiffness: 200, mass: 0.6 } });
  // depois de 1,5 s o título encolhe e vira etiqueta
  const enc = interpolate(t, [1.5, 2.1], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const brilho = interpolate((t * 0.6) % 1, [0, 1], [-30, 130]);
  return (
    <div style={{ position: "absolute", top: interpolate(enc, [0, 1], [300, 250]), width: "100%", display: "flex", flexDirection: "column", alignItems: "center", fontFamily: FONTE }}>
      <div
        style={{
          backgroundColor: enc > 0.5 ? LARANJA : "transparent",
          borderRadius: 999,
          padding: enc > 0.5 ? "10px 34px" : 0,
          color: "white",
          fontWeight: 700,
          fontSize: interpolate(enc, [0, 1], [150, 44]),
          letterSpacing: interpolate(enc, [0, 1], [6, 4]),
          lineHeight: 1,
          textShadow: enc > 0.5 ? "none" : `0 10px 40px rgba(0,0,0,.5), 0 0 0 ${LARANJA}`,
          transform: `scale(${enc > 0 ? 1 : 2.2 - 1.2 * slam})`,
          opacity: Math.min(1, slam * 2),
          backgroundImage: enc > 0.5 ? `linear-gradient(100deg, transparent ${brilho - 15}%, rgba(255,255,255,.35) ${brilho}%, transparent ${brilho + 15}%)` : undefined,
          boxShadow: enc > 0.5 ? "0 10px 30px rgba(0,0,0,.3)" : undefined,
        }}
      >
        {enc > 0.5 ? "📍 GRAMADO · RS" : "GRAMADO"}
      </div>
      {enc < 0.5 ? <div style={{ color: BEGE, fontWeight: 600, fontSize: 42, marginTop: 6, textShadow: sombra, opacity: (1 - enc * 2) * slam }}>Serra Gaúcha</div> : null}
    </div>
  );
};

// ---------- card final ----------
const Final: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t < FIM_FALA) return null;
  const local = frame - fr(FIM_FALA);
  const a = molaPop(local, 3, fps);
  const b = molaPop(local, 10, fps);
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO, fontFamily: FONTE, justifyContent: "center", alignItems: "center", textAlign: "center", padding: "0 80px" }}>
      <div style={{ color: BEGE, fontWeight: 600, fontSize: 44, opacity: a, transform: `translateY(${(1 - a) * 30}px)` }}>Gramado · maio de 2027</div>
      <div style={{ color: "white", fontWeight: 700, fontSize: 64, marginTop: 10, opacity: a }}>
        a partir de <span style={{ color: LARANJA }}>15x R$ 288</span>
      </div>
      <div style={{ color: "white", fontWeight: 500, fontSize: 40, marginTop: 4, opacity: a }}>para 2 pessoas</div>
      <Img src={staticFile("marca/logo.png")} style={{ height: 120, marginTop: 70, opacity: b, transform: `scale(${0.8 + 0.2 * b})` }} />
      <div style={{ color: "rgba(255,255,255,.7)", fontSize: 24, marginTop: 50, opacity: b }}>Valores sujeitos a alteração e disponibilidade.</div>
    </AbsoluteFill>
  );
};

export const GramadoOferta: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const nCorte = CORTES.filter((c) => t >= c).length;
  const zoomBase = interpolate(t, [0, FIM_FALA], [1.0, 1.06]);
  const escala = zoomBase * (nCorte % 2 === 1 ? 1.13 : 1.0);
  const flash = CORTES.some((c) => t >= c && t < c + 0.1) ? interpolate((t * 10) % 1, [0, 1], [0.25, 0]) : 0;
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill style={{ transform: `scale(${escala})`, transformOrigin: "50% 32%" }}>
        <Video src={staticFile("gramado/fala.mp4")} muted style={{ width: 1080, height: 1920 }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, rgba(13,45,94,.45) 0%, transparent 22%, transparent 50%, rgba(13,45,94,.55) 72%, rgba(13,45,94,.8) 100%)" }} />
      {flash > 0 ? <AbsoluteFill style={{ backgroundColor: "white", opacity: flash }} /> : null}
      <Titulo />
      <Preco />
      <Data />
      <Inclui />
      <Chamada />
      <Legenda />
      <Final />
      <Audio src={staticFile("gramado/voz.wav")} />
      <Audio src={staticFile("gramado/musica.wav")} volume={(f) => (f / FPS >= FIM_FALA ? interpolate(f / FPS, [FIM_FALA, FIM_FALA + 0.5], [0.13, 0.4], { extrapolateRight: "clamp" }) : 0.13)} />
    </AbsoluteFill>
  );
};
