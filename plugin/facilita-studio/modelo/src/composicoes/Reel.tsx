import { Audio, Video } from "@remotion/media";
import React from "react";
import { AbsoluteFill, Img, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { COR, FONTE, MARCA } from "../marca";
import { cobrir, contraste, cor, ease, fr, LinhasMovimento, NomeCor, Pilula, pop, sombraTexto } from "../componentes/basicos";
import { agrupar, Legenda, Palavra } from "../componentes/Legenda";

// =====================================================================
// Reel 1080×1920 montado por CENAS. Todos os tempos em segundos.
// Tempos das cenas e dos textos: na linha do tempo final do vídeo.
// Tempos DENTRO de uma cena de tela (tomadas, destaques, passos...): a
// partir do início daquela cena.
// =====================================================================

type Base = { de: number; ate: number; flash?: boolean };
export type CenaFala = Base & {
  tipo: "fala";
  video: string;
  inicio?: number; // segundo do arquivo onde a cena começa
  largura?: number;
  altura?: number;
  zoom?: [number, number]; // escala no início e no fim (zoom suave)
  punches?: number[]; // tempos (linha final) com "soco" de zoom
};
export type CenaCobertura = Base & {
  tipo: "cobertura";
  tomadas: { video: string; inicio?: number; largura?: number; altura?: number }[];
  filtro?: "dramatico" | "natural";
  etiqueta?: string; // ex.: "MARINGÁ · PR"
};
export type Tomada = { t: number; cx: number; cy: number; s: number };
export type Destaque = { de: number; ate: number; tipo: "ret" | "circ"; x: number; y: number; w: number; h: number; paraX?: number; paraY?: number; mover?: [number, number] };
export type CenaTela = Base & {
  tipo: "tela";
  video: string;
  inicio?: number;
  largura: number; // dimensões do arquivo de tela
  altura: number;
  tomadas: Tomada[]; // câmera: centro (cx, cy) em px do arquivo e escala s
  destaques?: Destaque[];
  passos?: { de: number; rotulo: string; titulo: string; alerta?: boolean }[];
  rotulos?: { de: number; ate: number; texto: string; posicao?: "topo" | "base"; fundo?: NomeCor }[];
  aviso?: { de: number; titulo: string; itens: { em: number; texto: string }[] };
};
export type CenaFinal = Base & {
  tipo: "final";
  imagem?: string; // fundo desfocado (ex.: quadro do rosto)
  linhas: { texto: string; cor?: NomeCor; tamanho?: number }[];
  rodape?: string;
  icones?: ("salvar" | "compartilhar" | "seguir" | "whatsapp")[];
  logo?: boolean;
};
export type Cena = CenaFala | CenaCobertura | CenaTela | CenaFinal;

export type TextoTela = {
  de: number;
  ate: number;
  texto: string;
  estilo?: "selo" | "etiqueta" | "titulo" | "contador";
  posicao?: "topo" | "alto" | "meio";
  fundo?: NomeCor;
  contador?: { de: number; ate: number; sufixo?: string; t0: number; t1: number; legenda?: string };
  linhas?: boolean; // linhas de movimento atrás
};

export type ReelProps = {
  duracao: number;
  voz?: string;
  musica?: { arquivo: string; volume: number; volumeFinal?: number };
  palavras?: Palavra[];
  legenda?: { ativa?: boolean; topo?: number; topoTela?: number; maxPalavras?: number; tamanho?: number; destaques?: string[] };
  cenas: Cena[];
  textos?: TextoTela[];
};

export const metadadosReel = ({ props }: { props: ReelProps }) => ({ durationInFrames: Math.max(1, fr(props.duracao)) });

// ---------------------------------------------------------------- fala
const Fala: React.FC<{ c: CenaFala }> = ({ c }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = c.ate - c.de;
  const [z0, z1] = c.zoom ?? [1.0, 1.1];
  const t = frame / fps;
  // cada "soco" acrescenta 4% de zoom com mola e mantém
  const soco = (c.punches ?? []).reduce((acc, p) => acc + spring({ frame: frame - fr(p - c.de), fps, config: { damping: 12, stiffness: 140 } }), 0);
  const escala = interpolate(t, [0, dur], [z0, z1], { extrapolateRight: "clamp" }) + soco * 0.04;
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill style={{ transform: `scale(${escala})`, transformOrigin: "50% 40%" }}>
        <Video src={staticFile(c.video)} trimBefore={fr(c.inicio ?? 0)} muted style={cobrir(c.largura, c.altura)} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, transparent 45%, rgba(0,0,0,.5) 100%)" }} />
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, rgba(0,0,0,.5) 0%, transparent 28%, transparent 62%, rgba(0,0,0,.6) 100%)" }} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- cobertura
const Cobertura: React.FC<{ c: CenaCobertura }> = ({ c }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = (c.ate - c.de) / c.tomadas.length;
  const filtro = c.filtro === "natural" ? "none" : "contrast(1.12) saturate(0.8) brightness(0.92)";
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {c.tomadas.map((tm, i) => {
        const de = fr(i * dur);
        const z = interpolate(frame - de, [0, fr(dur)], [1.04, 1.14]);
        return (
          <Sequence key={i} from={de} durationInFrames={fr(dur) + 1} layout="none">
            <AbsoluteFill style={{ transform: `scale(${z}) translateX(${i % 2 ? -10 : 10}px)` }}>
              <Video src={staticFile(tm.video)} trimBefore={fr(tm.inicio ?? 0)} muted style={{ ...cobrir(tm.largura, tm.altura), filter: filtro }} />
            </AbsoluteFill>
          </Sequence>
        );
      })}
      {c.tomadas.map((_, i) => {
        const de = fr(i * dur);
        if (i === 0 || frame < de || frame >= de + 5) return null;
        return <AbsoluteFill key={i} style={{ backgroundColor: "white", opacity: interpolate(frame, [de, de + 4], [0.75, 0], { extrapolateRight: "clamp" }) }} />;
      })}
      <AbsoluteFill style={{ background: "linear-gradient(to bottom, rgba(0,0,0,.6) 0%, transparent 30%, transparent 60%, rgba(0,0,0,.7) 100%)" }} />
      {c.etiqueta ? (
        <div style={{ position: "absolute", top: 250, left: 60 }}>
          <Pilula fundo="rgba(0,0,0,.55)" style={{ fontSize: 32, fontWeight: 700, color: "white", border: "2px solid rgba(255,255,255,.35)" }}>
            <span style={{ width: 16, height: 16, borderRadius: 8, backgroundColor: COR.alerta, opacity: Math.floor((frame / fps) * 2) % 2 ? 0.3 : 1 }} />
            {c.etiqueta}
          </Pilula>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- tela
const JANELA = { x: 40, y: 360, w: 1000, h: 960 };
const limitar = (c: number, tam: number, total: number) => (tam >= total ? total / 2 : Math.min(Math.max(c, tam / 2), total - tam / 2));
const camera = (tomadas: Tomada[], t: number, W: number, H: number) => {
  let k = 0;
  tomadas.forEach((tm, i) => {
    if (tm.t <= t) k = i;
  });
  const atual = tomadas[k];
  const ant = tomadas[Math.max(0, k - 1)];
  const p = k === 0 ? 1 : interpolate(t, [atual.t, atual.t + 0.6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  let s = ant.s + (atual.s - ant.s) * p;
  s *= 1 + Math.min(t - atual.t, 6) * 0.006; // empurrão lento
  return { s, cx: limitar(ant.cx + (atual.cx - ant.cx) * p, JANELA.w / s, W), cy: limitar(ant.cy + (atual.cy - ant.cy) * p, JANELA.h / s, H) };
};

const Tela: React.FC<{ c: CenaTela }> = ({ c }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const { s, cx, cy } = camera(c.tomadas, t, c.largura, c.altura);
  const entrada = spring({ frame, fps, config: { damping: 16, stiffness: 120 } });
  const passos = c.passos ?? [];
  const pIdx = passos.reduce((acc, p, i) => (t >= p.de ? i : acc), -1);
  const passo = pIdx >= 0 ? passos[pIdx] : null;
  const pIn = passo ? spring({ frame: frame - fr(passo.de), fps, config: { damping: 14, stiffness: 180 } }) : 0;
  const amarelo = COR.legenda_destaque;
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 35%, ${COR.primaria} 0%, #050b14 75%)`, fontFamily: FONTE }}>
      <LinhasMovimento opacidade={0.3} semente={3} />
      {passo ? (
        <div key={pIdx} style={{ position: "absolute", top: 230, width: "100%", textAlign: "center", transform: `translateY(${(1 - pIn) * -30}px)`, opacity: pIn }}>
          <div style={{ display: "inline-block", backgroundColor: passo.alerta ? COR.alerta : amarelo, color: contraste(passo.alerta ? COR.alerta : amarelo), fontWeight: 800, fontSize: 26, letterSpacing: 3, padding: "6px 18px", borderRadius: 10 }}>
            {passo.rotulo}
          </div>
          <div style={{ color: "white", fontWeight: 800, fontSize: 52, marginTop: 8, textShadow: sombraTexto }}>{passo.titulo}</div>
        </div>
      ) : null}
      <div
        style={{
          position: "absolute",
          left: JANELA.x,
          top: JANELA.y,
          width: JANELA.w,
          height: JANELA.h,
          borderRadius: 30,
          overflow: "hidden",
          backgroundColor: "#0b1626",
          boxShadow: "0 30px 80px rgba(0,0,0,.55), 0 0 0 3px rgba(255,255,255,.12)",
          transform: `scale(${0.85 + entrada * 0.15})`,
          opacity: entrada,
        }}
      >
        <div style={{ position: "absolute", width: c.largura, height: c.altura, transformOrigin: "0 0", transform: `translate(${JANELA.w / 2 - cx * s}px, ${JANELA.h / 2 - cy * s}px) scale(${s})` }}>
          <Video src={staticFile(c.video)} trimBefore={fr(c.inicio ?? 0)} muted style={{ width: c.largura, height: c.altura }} />
          <svg width={c.largura} height={c.altura} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
            {(c.destaques ?? [])
              .filter((d) => t >= d.de && t < d.ate)
              .map((d, i) => {
                const p = interpolate(t, [d.de, d.de + 0.35], [0, 1], { extrapolateRight: "clamp", easing: ease });
                const saida = interpolate(t, [d.ate - 0.15, d.ate], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
                const mv = d.mover ?? [d.de, d.de];
                const k = interpolate(t, [mv[0], Math.max(mv[1], mv[0] + 0.01)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
                const x = d.x + ((d.paraX ?? d.x) - d.x) * k;
                const y = d.y + ((d.paraY ?? d.y) - d.y) * k;
                const sw = 5 / s;
                const estilo = { filter: `drop-shadow(0 0 ${8 / s}px ${amarelo})` };
                if (d.tipo === "ret") {
                  const per = 2 * (d.w + d.h) + 40;
                  return <rect key={i} x={x - 6} y={y - 6} width={d.w + 12} height={d.h + 12} rx={10} fill={amarelo} fillOpacity={0.12 * p} stroke={amarelo} strokeWidth={sw} strokeDasharray={per} strokeDashoffset={per * (1 - p)} opacity={saida} style={estilo} />;
                }
                const r = (d.w / 2) * (1 + Math.sin(frame / 4) * 0.04);
                const per = 2 * Math.PI * r;
                return <circle key={i} cx={x} cy={y} r={r} fill="none" stroke={amarelo} strokeWidth={sw} strokeDasharray={per} strokeDashoffset={per * (1 - p)} opacity={saida} style={estilo} />;
              })}
          </svg>
        </div>
        {(c.rotulos ?? [])
          .filter((r) => t >= r.de && t < r.ate)
          .map((r, i) => (
            <div key={i} style={{ position: "absolute", width: "100%", display: "flex", justifyContent: "center", ...(r.posicao === "base" ? { bottom: 40 } : { top: 40 }) }}>
              <Pilula fundo={cor(r.fundo, amarelo)} style={{ fontSize: 34, opacity: pop(frame, fr(r.de), fps), transform: `scale(${0.7 + 0.3 * pop(frame, fr(r.de), fps)})` }}>
                {r.texto}
              </Pilula>
            </div>
          ))}
        {c.aviso && t >= c.aviso.de ? (
          <div
            style={{
              position: "absolute",
              left: 50,
              right: 50,
              bottom: 50,
              backgroundColor: "rgba(10,16,28,.92)",
              border: `3px solid ${COR.alerta}`,
              borderRadius: 28,
              padding: "30px 36px",
              transform: `translateY(${(1 - pop(frame, fr(c.aviso.de), fps)) * 80}px)`,
              opacity: pop(frame, fr(c.aviso.de), fps),
            }}
          >
            <div style={{ color: COR.alerta, fontWeight: 800, fontSize: 40 }}>{c.aviso.titulo}</div>
            {c.aviso.itens.map((a) => {
              const k = t >= a.em ? pop(frame, fr(a.em), fps) : 0;
              return (
                <div key={a.texto} style={{ color: "white", fontWeight: 700, fontSize: 40, marginTop: 14, opacity: k, transform: `translateX(${(1 - k) * -40}px)` }}>
                  {a.texto}
                </div>
              );
            })}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- final
const Icone: React.FC<{ nome: string; frame: number; i: number }> = ({ nome, frame, i }) => {
  const rot = Math.sin(frame / 5 + i * 1.5) * 6;
  const amarelo = COR.legenda_destaque;
  const svg: Record<string, React.ReactNode> = {
    salvar: <path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4.5L5 21V4a1 1 0 0 1 1-1z" fill={amarelo} />,
    compartilhar: <path d="M22 2 15 22l-4-9-9-4 20-7z" fill="white" />,
    seguir: <path d="M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm-8 10a8 8 0 0 1 16 0z M19 6h4M21 4v4" fill="white" stroke="white" strokeWidth={0.6} />,
    whatsapp: <path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.5-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.4.6-.4.4c-.1.1-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.4 2.4 1.5.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.7-.1l1.9.9c.3.1.5.2.5.3.1.2.1.6-.1 1.1z" fill="#25D366" />,
  };
  return (
    <svg width={120} height={120} viewBox="0 0 24 24" style={{ transform: `rotate(${rot}deg)` }}>
      {svg[nome]}
    </svg>
  );
};

const Final: React.FC<{ c: CenaFinal }> = ({ c }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const icones = pop(frame, 6 + c.linhas.length * 8, fps);
  return (
    <AbsoluteFill style={{ backgroundColor: COR.primaria, fontFamily: FONTE }}>
      {c.imagem ? (
        <AbsoluteFill style={{ transform: `scale(${1.08 + t * 0.03})` }}>
          <Img src={staticFile(c.imagem)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "blur(6px) brightness(.55)" }} />
        </AbsoluteFill>
      ) : null}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, rgba(5,11,20,.2) 0%, rgba(5,11,20,.85) 80%)" }} />
      <LinhasMovimento opacidade={0.35} semente={7} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", textAlign: "center", padding: "0 70px" }}>
        {c.linhas.map((l, i) => {
          const a = pop(frame, 4 + i * 8, fps);
          return (
            <div key={i} style={{ color: cor(l.cor, "#FFFFFF"), fontWeight: 800, fontSize: l.tamanho ?? 100, lineHeight: 1.04, transform: `scale(${0.6 + a * 0.4})`, opacity: a, textShadow: sombraTexto }}>
              {l.texto}
            </div>
          );
        })}
        {c.icones?.length ? (
          <div style={{ display: "flex", gap: 60, marginTop: 60, transform: `translateY(${(1 - icones) * 60}px)`, opacity: icones }}>
            {c.icones.map((n, i) => (
              <Icone key={n} nome={n} frame={frame} i={i} />
            ))}
          </div>
        ) : null}
        {c.rodape ? <div style={{ color: "rgba(255,255,255,.88)", fontWeight: 600, fontSize: 36, marginTop: 40, opacity: icones }}>{c.rodape}</div> : null}
        {c.logo && MARCA.logo ? <Img src={staticFile(MARCA.logo)} style={{ height: 90, marginTop: 50, opacity: icones, objectFit: "contain" }} /> : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- textos na tela
const Texto: React.FC<{ x: TextoTela }> = ({ x }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame / fps;
  const a = pop(frame, 0, fps);
  const saida = interpolate(local, [x.ate - x.de - 0.2, x.ate - x.de], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const topo = x.posicao === "meio" ? 760 : x.posicao === "alto" ? 390 : 260;
  const fundo = cor(x.fundo, COR.alerta);
  let corpo: React.ReactNode;
  if (x.estilo === "contador" && x.contador) {
    const k = x.contador;
    const v = interpolate(local + x.de, [k.t0, k.t1], [k.de, k.ate], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
    const tremor = local + x.de > k.t0 && local + x.de < k.t1 ? Math.sin(frame * 2.3) * 4 : 0;
    corpo = (
      <div style={{ textAlign: "center", transform: `translateX(${tremor}px)` }}>
        <div style={{ color: "white", fontWeight: 800, fontSize: 120, lineHeight: 1, textShadow: sombraTexto }}>
          {Math.round(v)}
          <span style={{ fontSize: 56, color: COR.legenda_destaque }}>{k.sufixo ?? ""}</span>
        </div>
        {k.legenda ? <div style={{ color: "rgba(255,255,255,.9)", fontWeight: 600, fontSize: 34, marginTop: 6, textShadow: sombraTexto }}>{k.legenda}</div> : null}
      </div>
    );
  } else if (x.estilo === "titulo") {
    corpo = <div style={{ color: "white", fontWeight: 800, fontSize: 84, lineHeight: 1.05, textAlign: "center", padding: "0 60px", textShadow: sombraTexto }}>{x.texto}</div>;
  } else if (x.estilo === "etiqueta") {
    corpo = <Pilula fundo={fundo} style={{ fontSize: 40 }}>{x.texto}</Pilula>;
  } else {
    corpo = (
      <Pilula fundo={fundo} style={{ fontSize: 58, letterSpacing: 2, padding: "14px 36px", transform: "rotate(-3deg)" }}>
        {x.texto}
      </Pilula>
    );
  }
  return (
    <AbsoluteFill style={{ fontFamily: FONTE }}>
      {x.linhas ? <LinhasMovimento opacidade={0.8 * saida * Math.min(1, a * 2)} /> : null}
      <div style={{ position: "absolute", top: topo, width: "100%", display: "flex", justifyContent: "center", transform: `scale(${0.5 + a * 0.5})`, opacity: Math.min(1, a * 1.5) * saida }}>{corpo}</div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- composição
export const Reel: React.FC<ReelProps> = ({ duracao, voz, musica, palavras = [], legenda = {}, cenas, textos = [] }) => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  const cortes = cenas.map((c) => c.de);
  const grupos = React.useMemo(() => agrupar(palavras, legenda.maxPalavras ?? 3, cortes), [palavras, legenda.maxPalavras, cortes.join(",")]);
  const cenaAtual = cenas.find((c) => t >= c.de && t < c.ate);
  const inicioFinal = cenas.find((c) => c.tipo === "final")?.de ?? duracao;
  const volMusica = (f: number) => {
    if (!musica) return 0;
    const s = f / 30;
    const fim = musica.volumeFinal ?? musica.volume;
    return interpolate(s, [inicioFinal - 0.3, inicioFinal + 0.4], [musica.volume, fim], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  };
  const legendaAtiva = (legenda.ativa ?? true) && cenaAtual?.tipo !== "final";
  const topoLegenda = cenaAtual?.tipo === "tela" ? (legenda.topoTela ?? 1350) : (legenda.topo ?? 1330);
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {cenas.map((c, i) => (
        <Sequence key={i} from={fr(c.de)} durationInFrames={Math.max(1, fr(c.ate) - fr(c.de))}>
          {c.tipo === "fala" ? <Fala c={c} /> : c.tipo === "cobertura" ? <Cobertura c={c} /> : c.tipo === "tela" ? <Tela c={c} /> : <Final c={c} />}
        </Sequence>
      ))}
      {textos.map((x, i) => (
        <Sequence key={`t${i}`} from={fr(x.de)} durationInFrames={Math.max(1, fr(x.ate) - fr(x.de))}>
          <Texto x={x} />
        </Sequence>
      ))}
      {cenas.slice(1).map((c) => {
        const d = t - c.de;
        return c.flash !== false && d >= 0 && d < 0.2 ? <AbsoluteFill key={`f${c.de}`} style={{ backgroundColor: "white", opacity: 0.8 * (1 - d / 0.2) }} /> : null;
      })}
      {legendaAtiva && grupos.length ? <Legenda grupos={grupos} topo={topoLegenda} extras={legenda.destaques} tamanho={legenda.tamanho} /> : null}
      {voz ? <Audio src={staticFile(voz)} /> : null}
      {musica ? <Audio src={staticFile(musica.arquivo)} volume={volMusica} /> : null}
    </AbsoluteFill>
  );
};
