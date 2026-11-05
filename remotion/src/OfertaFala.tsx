import { Audio, Video } from "@remotion/media";
import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { BEGE, FONTE, LARANJA, MARINHO } from "./marca";

// Modelo de Reels de OFERTA com fala real (Facilita Pass).
// Cada oferta é um JSON em src/ofertas/<nome>.json. Tempos em segundos do vídeo.
const FPS = 30;
const fr = (s: number) => Math.round(s * FPS);
const ease = Easing.bezier(0.45, 0, 0.2, 1);
const sombra = "0 4px 18px rgba(0,0,0,.55), 0 2px 4px rgba(0,0,0,.7)";
const VERDE_WPP = "#25D366";
const CORES: Record<string, string> = { marinho: MARINHO, laranja: LARANJA, bege: BEGE, branco: "#FFFFFF", preto: "#0A0A0A", cinza: "#9CA3AF" };
const c = (n?: string, p = MARINHO) => (n ? (CORES[n] ?? n) : p);

type Parte = { texto: string; cor?: string; tamanho?: number; peso?: number };
type Linha = { em?: number; texto?: string; partes?: Parte[]; tamanho?: number; cor?: string; peso?: number; icone?: string; sub?: string };
type CardOferta = { de: number; ate: number; fundo?: "branco" | "marinho" | "preto"; rotulo?: string; linhas: Linha[] };
type Palavra = { w: string; i: number; f: number };

export type OfertaProps = {
  pasta: string; // public/<pasta>/fala.mp4, voz.wav, musica.wav
  fimFala: number;
  gancho?: { texto: string; ate: number }; // selo antes do título
  titulo: { texto: string; sub?: string; etiqueta: string; em: number };
  cortes: number[];
  destaques: string[];
  palavras: Palavra[];
  cards: CardOferta[];
  chamada?: { de: number; botaoEm: number; texto: string; botao: string };
  final: { linha1: string; destaque: string; linha3: string; rodape: string };
  musicaVolume?: number;
  espelhar?: boolean; // desinverte vídeo de câmera frontal (texto do fundo legível)
};

export const metadadosOferta = ({ props }: { props: OfertaProps }) => ({ durationInFrames: fr(props.fimFala + 2.1) });

const mola = (frame: number, ini: number, fps: number) => spring({ frame: frame - ini, fps, config: { damping: 11, stiffness: 170, mass: 0.7 } });
const limpa = (w: string) => w.toLowerCase().replace(/[.,!?]+$/, "");

// ---------------------------------------------------------------- legenda
const Legenda: React.FC<{ palavras: Palavra[]; destaques: Set<string>; fim: number }> = ({ palavras, destaques, fim }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const grupos = React.useMemo(() => {
    const g: Palavra[][] = [];
    let a: Palavra[] = [];
    palavras.forEach((p, i) => {
      a.push(p);
      const prox = palavras[i + 1];
      if (a.length >= 3 || /[.,!?]$/.test(p.w) || !prox || prox.i - p.f > 0.4) {
        g.push(a);
        a = [];
      }
    });
    return g;
  }, [palavras]);
  const idx = grupos.findIndex((g, i) => t >= g[0].i - 0.05 && t < (grupos[i + 1] ? grupos[i + 1][0].i : g[g.length - 1].f + 0.4));
  if (idx < 0 || t >= fim) return null;
  const g = grupos[idx];
  const e = spring({ frame: frame - fr(g[0].i - 0.05), fps, config: { damping: 14, stiffness: 220 } });
  return (
    <div style={{ position: "absolute", top: 1425, left: 70, right: 70, display: "flex", flexWrap: "wrap", justifyContent: "center", columnGap: 18, transform: `translateY(${(1 - e) * 22}px)`, opacity: e }}>
      {g.map((p, k) => {
        const ativa = t >= p.i - 0.03;
        const dest = destaques.has(limpa(p.w));
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
              WebkitTextStroke: dest ? undefined : "2px rgba(0,0,0,.45)",
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

// ---------------------------------------------------------------- card
const Card: React.FC<{ card: CardOferta }> = ({ card }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t < card.de || t >= card.ate) return null;
  const k = mola(frame, fr(card.de), fps);
  const saida = interpolate(t, [card.ate - 0.18, card.ate], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fundo = card.fundo === "marinho" ? MARINHO : card.fundo === "preto" ? "#0A0A0A" : "white";
  const textoPadrao = card.fundo && card.fundo !== "branco" ? "branco" : "marinho";
  const brilho = interpolate((t * 0.7) % 1, [0, 1], [-30, 130]);
  return (
    <div style={{ position: "absolute", left: 70, right: 70, top: 1100, transform: `translateY(${(1 - k) * 90}px) scale(${0.85 + 0.15 * k})`, opacity: Math.min(1, k * 1.4) * saida, fontFamily: FONTE }}>
      <div
        style={{
          backgroundColor: fundo,
          borderRadius: 34,
          padding: "24px 38px",
          boxShadow: "0 22px 60px rgba(0,0,0,.35)",
          border: card.fundo === "preto" ? `3px solid ${LARANJA}` : undefined,
          backgroundImage: card.fundo === "preto" ? `linear-gradient(100deg, transparent ${brilho - 12}%, rgba(255,255,255,.12) ${brilho}%, transparent ${brilho + 12}%)` : undefined,
        }}
      >
        {card.rotulo ? <div style={{ color: LARANJA, fontWeight: 700, fontSize: 26, letterSpacing: 2, marginBottom: 4 }}>{card.rotulo}</div> : null}
        {card.linhas.map((l, i) => {
          const em = l.em ?? card.de;
          const p = mola(frame, fr(em), fps);
          const vis = frame >= fr(em) ? p : 0;
          const corpo = l.partes ? (
            <div style={{ display: "flex", alignItems: "baseline", gap: 16, flexWrap: "wrap" }}>
              {l.partes.map((pt, j) => (
                <span key={j} style={{ color: c(pt.cor, c(textoPadrao)), fontWeight: pt.peso ?? 700, fontSize: pt.tamanho ?? 44, lineHeight: 1.05 }}>
                  {pt.texto}
                </span>
              ))}
            </div>
          ) : (
            <div style={{ color: c(l.cor, c(textoPadrao)), fontWeight: l.peso ?? 600, fontSize: l.tamanho ?? 36, lineHeight: 1.12 }}>
              {l.texto}
              {l.sub ? <div style={{ fontWeight: 500, fontSize: 26, color: LARANJA }}>{l.sub}</div> : null}
            </div>
          );
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 16, marginTop: i === 0 ? 0 : 6, opacity: vis, transform: `translateX(${(1 - vis) * -40}px) scale(${l.partes ? 0.7 + 0.3 * vis : 1})`, transformOrigin: "left center" }}>
              {l.icone ? (
                <div style={{ width: 52, height: 52, borderRadius: 26, backgroundColor: card.fundo === "preto" ? "#262626" : BEGE, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28, flexShrink: 0 }}>{l.icone}</div>
              ) : null}
              {corpo}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------- título
const Titulo: React.FC<{ p: OfertaProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  if (t >= p.fimFala) return null;
  const ganchoAtivo = p.gancho && t < p.gancho.ate;
  if (ganchoAtivo && p.gancho) {
    const s = mola(frame, 0, fps);
    return (
      <div style={{ position: "absolute", top: 300, width: "100%", display: "flex", justifyContent: "center", fontFamily: FONTE }}>
        <div style={{ backgroundColor: LARANJA, color: "white", fontWeight: 700, fontSize: 62, padding: "14px 40px", borderRadius: 999, transform: `scale(${2 - s}) rotate(-3deg)`, opacity: Math.min(1, s * 2), boxShadow: "0 14px 40px rgba(0,0,0,.35)" }}>
          {p.gancho.texto}
        </div>
      </div>
    );
  }
  if (t < p.titulo.em) return null;
  const slam = spring({ frame: frame - fr(p.titulo.em), fps, config: { damping: 9, stiffness: 200, mass: 0.6 } });
  const enc = interpolate(t, [p.titulo.em + 1.4, p.titulo.em + 2.0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const brilho = interpolate((t * 0.6) % 1, [0, 1], [-30, 130]);
  const longo = p.titulo.texto.length > 10;
  return (
    <div style={{ position: "absolute", top: interpolate(enc, [0, 1], [290, 250]), width: "100%", display: "flex", flexDirection: "column", alignItems: "center", fontFamily: FONTE, padding: "0 50px", textAlign: "center" }}>
      <div
        style={{
          backgroundColor: enc > 0.5 ? LARANJA : "transparent",
          borderRadius: 999,
          padding: enc > 0.5 ? "10px 34px" : 0,
          color: "white",
          fontWeight: 700,
          fontSize: interpolate(enc, [0, 1], [longo ? 108 : 150, 44]),
          letterSpacing: interpolate(enc, [0, 1], [4, 3]),
          lineHeight: 1.02,
          textShadow: enc > 0.5 ? "none" : "0 10px 40px rgba(0,0,0,.5)",
          transform: `scale(${enc > 0 ? 1 : 2.2 - 1.2 * slam})`,
          opacity: Math.min(1, slam * 2),
          backgroundImage: enc > 0.5 ? `linear-gradient(100deg, transparent ${brilho - 15}%, rgba(255,255,255,.35) ${brilho}%, transparent ${brilho + 15}%)` : undefined,
          boxShadow: enc > 0.5 ? "0 10px 30px rgba(0,0,0,.3)" : undefined,
        }}
      >
        {enc > 0.5 ? p.titulo.etiqueta : p.titulo.texto}
      </div>
      {enc < 0.5 && p.titulo.sub ? <div style={{ color: BEGE, fontWeight: 600, fontSize: 42, marginTop: 8, textShadow: sombra, opacity: (1 - enc * 2) * slam }}>{p.titulo.sub}</div> : null}
    </div>
  );
};

// ---------------------------------------------------------------- chamada
const Chamada: React.FC<{ p: OfertaProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const ch = p.chamada;
  if (!ch || t < ch.de || t >= p.fimFala) return null;
  const k = mola(frame, fr(ch.de), fps);
  const b = mola(frame, fr(ch.botaoEm), fps);
  const pulso = frame >= fr(ch.botaoEm + 0.5) ? 1 + Math.sin((frame - fr(ch.botaoEm + 0.5)) / 4) * 0.03 : 1;
  return (
    <div style={{ position: "absolute", left: 70, right: 70, top: 1110, textAlign: "center", fontFamily: FONTE, opacity: Math.min(1, k * 1.4) }}>
      <div style={{ color: "white", fontWeight: 700, fontSize: 50, textShadow: sombra, transform: `translateY(${(1 - k) * 40}px)` }}>{ch.texto}</div>
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
          opacity: frame >= fr(ch.botaoEm) ? b : 0,
        }}
      >
        <svg width={52} height={52} viewBox="0 0 24 24">
          <path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.5-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.4.6-.4.4c-.1.1-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.4 2.4 1.5.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.7-.1l1.9.9c.3.1.5.2.5.3.1.2.1.6-.1 1.1z" fill="white" />
        </svg>
        {ch.botao}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------- final
const Final: React.FC<{ p: OfertaProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < fr(p.fimFala)) return null;
  const local = frame - fr(p.fimFala);
  const a = mola(local, 3, fps);
  const b = mola(local, 10, fps);
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO, fontFamily: FONTE, justifyContent: "center", alignItems: "center", textAlign: "center", padding: "0 80px" }}>
      <div style={{ color: BEGE, fontWeight: 600, fontSize: 44, opacity: a, transform: `translateY(${(1 - a) * 30}px)` }}>{p.final.linha1}</div>
      <div style={{ color: "white", fontWeight: 700, fontSize: 64, marginTop: 10, opacity: a }}>
        a partir de <span style={{ color: LARANJA }}>{p.final.destaque}</span>
      </div>
      <div style={{ color: "white", fontWeight: 500, fontSize: 40, marginTop: 4, opacity: a }}>{p.final.linha3}</div>
      <Img src={staticFile("marca/logo.png")} style={{ height: 120, marginTop: 70, opacity: b, transform: `scale(${0.8 + 0.2 * b})` }} />
      <div style={{ color: "rgba(255,255,255,.7)", fontSize: 24, marginTop: 50, opacity: b }}>{p.final.rodape}</div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- composição
export const OfertaFala: React.FC<OfertaProps> = (p) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const nCorte = p.cortes.filter((x) => t >= x).length;
  const escala = interpolate(t, [0, p.fimFala], [1.0, 1.06]) * (nCorte % 2 === 1 ? 1.13 : 1.0);
  const flash = p.cortes.some((x) => t >= x && t < x + 0.1) ? interpolate((t * 10) % 1, [0, 1], [0.25, 0]) : 0;
  const destaques = React.useMemo(() => new Set(p.destaques.map((d) => d.toLowerCase())), [p.destaques]);
  const vol = p.musicaVolume ?? 0.13;
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill style={{ transform: `scale(${escala})`, transformOrigin: "50% 32%" }}>
        <Video src={staticFile(`${p.pasta}/fala.mp4`)} muted style={{ width: 1080, height: 1920, transform: p.espelhar ? "scaleX(-1)" : undefined }} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, rgba(13,45,94,.45) 0%, transparent 22%, transparent 50%, rgba(13,45,94,.55) 72%, rgba(13,45,94,.8) 100%)" }} />
      {flash > 0 ? <AbsoluteFill style={{ backgroundColor: "white", opacity: flash }} /> : null}
      <Titulo p={p} />
      {p.cards.map((card, i) => (
        <Card key={i} card={card} />
      ))}
      <Chamada p={p} />
      <Legenda palavras={p.palavras} destaques={destaques} fim={p.fimFala} />
      <Final p={p} />
      <Audio src={staticFile(`${p.pasta}/voz.wav`)} />
      <Audio src={staticFile(`${p.pasta}/musica.wav`)} volume={(f) => (f / FPS >= p.fimFala ? interpolate(f / FPS, [p.fimFala, p.fimFala + 0.5], [vol, 0.4], { extrapolateRight: "clamp" }) : vol)} />
    </AbsoluteFill>
  );
};
