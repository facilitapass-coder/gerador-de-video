import { Audio, Video } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  random,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { clamp, sombra } from "./AllFunInclusive";
import { BEGE, FONTE, LARANJA, MARINHO, SEGURA } from "./marca";
import palavras from "./bf-palavras.json";

// Reels Black Facilita Pass · fala real (IMG_9875) com motion graphics estilo After Effects.
// comMusica=false gera a versão só com a voz.
export type BlackProps = { comMusica: boolean };

const FPS = 30;
const f = (s: number) => Math.round(s * FPS);
const PRETO = "#0A0A0F";

// Fim de cada frase: punch-in de câmera + flash
const CORTES = [3.42, 4.5, 10.7, 17.2, 22.1, 26.3];
const DESTAQUES = new Set([
  "black", "friday", "novidade!", "facilita", "pass", "novembro", "ofertas", "novas", "todos", "dias.",
  "nacionais,", "internacionais,", "cruzeiros", "papel.", "instagram", "grupo", "vip,", "promoções",
  "condições", "especiais.", "próxima", "viagem", "viagem?", "aqui.",
]);

const useSpring = (inicio: number, cfg = { damping: 12, stiffness: 180 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - f(inicio), fps, config: cfg });
};

// ---------- câmera: punch-in a cada frase + tremida no gancho ----------
const Camera: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const i = CORTES.filter((c) => t >= c).length;
  const desde = i === 0 ? 0 : CORTES[i - 1];
  const alvo = i % 2 === 0 ? 1.04 : 1.16;
  const pulso = interpolate(frame - f(desde), [0, 5], [alvo + 0.08, alvo], { ...clamp, easing: Easing.out(Easing.cubic) });
  const tremor = t > 1.2 && t < 2.1 ? (random(`x${frame}`) - 0.5) * 14 : 0;
  const tremorY = t > 1.2 && t < 2.1 ? (random(`y${frame}`) - 0.5) * 14 : 0;
  return (
    <AbsoluteFill style={{ backgroundColor: PRETO }}>
      <Video
        src={staticFile("bf/fala.mp4")}
        muted
        objectFit="cover"
        style={{
          width: "100%",
          height: "100%",
          scale: pulso,
          translate: `${tremor}px ${tremorY - (alvo > 1.1 ? 40 : 0)}px`,
          filter: "contrast(1.1) saturate(1.08) brightness(0.97)",
        }}
      />
    </AbsoluteFill>
  );
};

// ---------- acabamento: vinheta, grão e flashes ----------
const Acabamento: React.FC = () => {
  const frame = useCurrentFrame();
  const flash = Math.max(
    ...CORTES.map((c) => interpolate(frame - f(c), [0, 1, 5], [0, 0.55, 0], clamp)),
  );
  return (
    <>
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 50% 40%, rgba(0,0,0,0) 45%, rgba(0,0,0,.55) 100%), linear-gradient(to bottom, rgba(0,0,0,.45) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 50%, rgba(0,0,0,.6) 100%)",
        }}
      />
      <AbsoluteFill style={{ opacity: 0.09, mixBlendMode: "overlay" }}>
        <svg width="100%" height="100%">
          <filter id="grao">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={frame % 12} />
          </filter>
          <rect width="100%" height="100%" filter="url(#grao)" />
        </svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ backgroundColor: "white", opacity: flash, mixBlendMode: "screen" }} />
    </>
  );
};

// ---------- texto com glitch RGB ----------
const Glitch: React.FC<{ readonly texto: string; readonly tamanho: number; readonly inicio: number; readonly cor?: string }> = ({
  texto,
  tamanho,
  inicio,
  cor = "white",
}) => {
  const frame = useCurrentFrame();
  const local = frame - f(inicio);
  const forte = local < 8 || (local % 37 < 3);
  const dx = forte ? (random(`g${frame}`) - 0.5) * 26 : 0;
  const corte = forte ? random(`c${frame}`) * 60 + 20 : 0;
  const camada = (c: string, ox: number): React.CSSProperties => ({
    position: "absolute",
    inset: 0,
    color: c,
    transform: `translateX(${ox}px)`,
    mixBlendMode: "screen",
  });
  const estilo: React.CSSProperties = { fontWeight: 700, fontSize: tamanho, lineHeight: 0.95, letterSpacing: -2, whiteSpace: "nowrap" };
  return (
    <div style={{ position: "relative", ...estilo }}>
      <span style={{ visibility: "hidden" }}>{texto}</span>
      <span style={camada("#ff2a4f", dx)}>{texto}</span>
      <span style={camada("#22e6ff", -dx)}>{texto}</span>
      <span
        style={{
          position: "absolute",
          inset: 0,
          color: cor,
          clipPath: forte ? `inset(${corte}% 0 ${100 - corte - 12}% 0)` : undefined,
          transform: forte ? `translateX(${dx * 1.5}px)` : undefined,
          textShadow: sombra,
        }}
      >
        {texto}
      </span>
      {forte ? <span style={{ position: "absolute", inset: 0, color: cor, clipPath: `inset(0 0 ${corte + 12}% 0)` }}>{texto}</span> : null}
      {forte ? <span style={{ position: "absolute", inset: 0, color: cor, clipPath: `inset(${corte + 12}% 0 0 0)` }}>{texto}</span> : null}
    </div>
  );
};

const Janela: React.FC<{ readonly de: number; readonly ate: number; readonly children: React.ReactNode }> = ({ de, ate, children }) => {
  const frame = useCurrentFrame();
  if (frame < f(de) || frame > f(ate)) return null;
  const sai = interpolate(frame, [f(ate) - 5, f(ate)], [1, 0], clamp);
  return <AbsoluteFill style={{ opacity: sai }}>{children}</AbsoluteFill>;
};

// ---------- 0 a 3,4 s · gancho ----------
const Gancho: React.FC = () => {
  const frame = useCurrentFrame();
  const entra = useSpring(1.18, { damping: 10, stiffness: 220 });
  const pergunta = useSpring(0, { damping: 14, stiffness: 200 });
  const blur = interpolate(frame - f(1.18), [0, 6], [18, 0], clamp);
  return (
    <AbsoluteFill style={{ alignItems: "center", top: SEGURA.topo - 60, fontFamily: FONTE }}>
      <div
        style={{
          color: "white",
          fontWeight: 600,
          fontSize: 54,
          textShadow: sombra,
          opacity: pergunta,
          transform: `translateY(${(1 - pergunta) * -40}px)`,
        }}
      >
        Esperando a…
      </div>
      <div
        style={{
          marginTop: 8,
          transform: `scale(${interpolate(entra, [0, 1], [3.2, 1])}) rotate(${interpolate(entra, [0, 1], [-8, -3])}deg)`,
          opacity: frame >= f(1.18) ? 1 : 0,
          filter: `blur(${blur}px)`,
          textAlign: "center",
        }}
      >
        <Glitch texto="BLACK" tamanho={210} inicio={1.18} />
        <div style={{ backgroundColor: LARANJA, padding: "0 26px", marginTop: 6, display: "inline-block" }}>
          <Glitch texto="FRIDAY?" tamanho={150} inicio={1.4} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------- 3,4 a 4,5 s · sticker "tem novidade" ----------
const Novidade: React.FC = () => {
  const s = useSpring(3.42, { damping: 8, stiffness: 260 });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", fontFamily: FONTE }}>
      <div
        style={{
          backgroundColor: "white",
          color: PRETO,
          fontWeight: 700,
          fontSize: 92,
          padding: "18px 44px",
          borderRadius: 24,
          transform: `scale(${s}) rotate(${interpolate(s, [0, 1], [20, -4])}deg)`,
          boxShadow: `14px 14px 0 ${LARANJA}`,
        }}
      >
        TEM NOVIDADE! 🔥
      </div>
    </AbsoluteFill>
  );
};

// ---------- 4,5 a 10,7 s · Black Facilita Pass já começou + novembro ----------
const JaComecou: React.FC = () => {
  const frame = useCurrentFrame();
  const selo = useSpring(4.55, { damping: 11, stiffness: 200 });
  const carimbo = useSpring(5.95, { damping: 7, stiffness: 300 });
  const mes = useSpring(7.6, { damping: 12, stiffness: 180 });
  const dia = Math.min(30, Math.max(1, Math.round(interpolate(frame, [f(8.3), f(10.4)], [1, 30], clamp))));
  const varre = interpolate(frame, [f(4.7), f(5.6)], [-120, 220], clamp);
  return (
    <AbsoluteFill style={{ fontFamily: FONTE }}>
      <div style={{ position: "absolute", top: SEGURA.topo - 40, left: SEGURA.esquerda, right: SEGURA.direita - 60, transform: `translateX(${(1 - selo) * -700}px)` }}>
        <div
          style={{
            position: "relative",
            overflow: "hidden",
            display: "inline-block",
            backgroundColor: PRETO,
            border: `5px solid ${LARANJA}`,
            padding: "18px 30px 14px",
            transform: "skewX(-8deg)",
          }}
        >
          <div style={{ color: LARANJA, fontWeight: 700, fontSize: 104, lineHeight: 0.95, letterSpacing: -2 }}>BLACK</div>
          <div style={{ color: "white", fontWeight: 600, fontSize: 64, lineHeight: 1 }}>Facilita Pass</div>
          <div
            style={{
              position: "absolute",
              top: 0,
              bottom: 0,
              width: 90,
              left: `${varre}%`,
              background: "linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,.55), rgba(255,255,255,0))",
              transform: "skewX(-20deg)",
            }}
          />
        </div>
        <div
          style={{
            marginTop: 18,
            display: "inline-block",
            marginLeft: 30,
            backgroundColor: LARANJA,
            color: "white",
            fontWeight: 700,
            fontSize: 58,
            padding: "6px 24px",
            transform: `scale(${interpolate(carimbo, [0, 1], [2.4, 1])}) rotate(-6deg)`,
            opacity: carimbo > 0.01 ? 1 : 0,
          }}
        >
          JÁ COMEÇOU!
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: SEGURA.esquerda,
          right: SEGURA.direita,
          bottom: SEGURA.base + 330,
          display: "flex",
          alignItems: "center",
          gap: 26,
          opacity: mes,
          transform: `translateY(${(1 - mes) * 120}px)`,
        }}
      >
        <div style={{ width: 190, borderRadius: 26, overflow: "hidden", boxShadow: "0 16px 40px rgba(0,0,0,.5)", flexShrink: 0 }}>
          <div style={{ backgroundColor: LARANJA, color: "white", fontWeight: 700, fontSize: 30, textAlign: "center", padding: "8px 0" }}>NOV</div>
          <div style={{ backgroundColor: "white", color: PRETO, fontWeight: 700, fontSize: 104, textAlign: "center", lineHeight: 1.2 }}>
            {String(dia).padStart(2, "0")}
          </div>
        </div>
        <div style={{ color: "white", textShadow: sombra }}>
          <div style={{ fontWeight: 700, fontSize: 62, lineHeight: 1 }}>Novembro inteiro</div>
          <div style={{ fontWeight: 500, fontSize: 40, color: BEGE, marginTop: 6 }}>ofertas novas todos os dias</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ---------- 10,7 a 17,2 s · nacionais, internacionais, cruzeiros ----------
const Cartao: React.FC<{ readonly icone: string; readonly texto: string; readonly inicio: number; readonly i: number }> = ({ icone, texto, inicio, i }) => {
  const s = useSpring(inicio, { damping: 11, stiffness: 210 });
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 22,
        backgroundColor: i === 1 ? LARANJA : "rgba(10,10,15,.88)",
        border: `3px solid ${i === 1 ? "white" : LARANJA}`,
        color: "white",
        borderRadius: 22,
        padding: "16px 30px",
        marginTop: 18,
        fontWeight: 700,
        fontSize: 60,
        transform: `translateX(${(1 - s) * (i % 2 ? 900 : -900)}px) rotate(${(1 - s) * (i % 2 ? 12 : -12)}deg)`,
        opacity: s > 0.01 ? 1 : 0,
        boxShadow: "0 14px 36px rgba(0,0,0,.45)",
        alignSelf: i % 2 ? "flex-end" : "flex-start",
      }}
    >
      <span style={{ fontSize: 64 }}>{icone}</span>
      {texto}
    </div>
  );
};

const Destinos: React.FC = () => {
  const frame = useCurrentFrame();
  const papel = useSpring(15.65, { damping: 10, stiffness: 220 });
  const cartoes = interpolate(frame, [f(15.3), f(15.6)], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ fontFamily: FONTE }}>
      <div style={{ position: "absolute", bottom: SEGURA.base + 300, left: SEGURA.esquerda, right: SEGURA.direita - 80, display: "flex", flexDirection: "column", opacity: cartoes }}>
        <Cartao icone="✈️" texto="Nacionais" inicio={11.6} i={0} />
        <Cartao icone="🌎" texto="Internacionais" inicio={12.45} i={1} />
        <Cartao icone="🚢" texto="Cruzeiros" inicio={13.65} i={2} />
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: SEGURA.base + 360,
          textAlign: "center",
          transform: `scale(${papel})`,
          opacity: papel > 0.01 ? 1 : 0,
        }}
      >
        <span style={{ backgroundColor: "white", color: PRETO, fontWeight: 700, fontSize: 64, padding: "10px 30px", borderRadius: 16, boxShadow: `10px 10px 0 ${LARANJA}` }}>
          Tira a viagem do papel ✍️
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ---------- 17,2 a 26,3 s · Instagram + grupo VIP ----------
const GrupoVip: React.FC = () => {
  const frame = useCurrentFrame();
  const insta = useSpring(19.3, { damping: 12, stiffness: 200 });
  const vip = useSpring(21.4, { damping: 8, stiffness: 240 });
  const brilho = interpolate((frame - f(21.8)) % f(1.6), [0, f(0.7)], [-40, 140], clamp);
  const itens: [string, number][] = [
    ["Novidades", 23.6],
    ["Promoções", 24.3],
    ["Condições especiais", 24.95],
  ];
  return (
    <AbsoluteFill style={{ fontFamily: FONTE }}>
      <div
        style={{
          position: "absolute",
          top: SEGURA.topo - 30,
          left: SEGURA.esquerda,
          display: "flex",
          alignItems: "center",
          gap: 18,
          transform: `translateY(${(1 - insta) * -200}px)`,
          opacity: insta,
        }}
      >
        <div
          style={{
            width: 92,
            height: 92,
            borderRadius: 26,
            background: "linear-gradient(45deg,#feda75,#fa7e1e,#d62976,#962fbf,#4f5bd5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div style={{ width: 50, height: 50, border: "6px solid white", borderRadius: 16, position: "relative" }}>
            <div style={{ position: "absolute", inset: 9, border: "6px solid white", borderRadius: "50%" }} />
          </div>
        </div>
        <div style={{ color: "white", fontWeight: 700, fontSize: 52, textShadow: sombra }}>Acompanhe o perfil</div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: SEGURA.base + 300,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <div
          style={{
            position: "relative",
            overflow: "hidden",
            background: `linear-gradient(135deg, ${LARANJA}, #ff8a3d)`,
            color: "white",
            borderRadius: 28,
            padding: "18px 46px",
            transform: `scale(${vip}) rotate(${interpolate(vip, [0, 1], [-15, -2])}deg)`,
            opacity: vip > 0.01 ? 1 : 0,
            boxShadow: "0 20px 50px rgba(232,87,42,.55)",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 34, fontWeight: 600, letterSpacing: 4 }}>👑 ENTRE NO</div>
          <div style={{ fontSize: 112, fontWeight: 700, lineHeight: 0.95 }}>GRUPO VIP</div>
          <div
            style={{
              position: "absolute",
              top: 0,
              bottom: 0,
              width: 120,
              left: `${brilho}%`,
              background: "linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,.6), rgba(255,255,255,0))",
              transform: "skewX(-20deg)",
            }}
          />
        </div>
        <div style={{ display: "flex", gap: 14, marginTop: 22, flexWrap: "wrap", justifyContent: "center", maxWidth: 900 }}>
          {itens.map(([txt, ini]) => (
            <Item key={txt} texto={txt} inicio={ini} />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Item: React.FC<{ readonly texto: string; readonly inicio: number }> = ({ texto, inicio }) => {
  const s = useSpring(inicio, { damping: 12, stiffness: 240 });
  return (
    <div
      style={{
        backgroundColor: "rgba(10,10,15,.85)",
        color: "white",
        fontWeight: 600,
        fontSize: 36,
        padding: "8px 20px",
        borderRadius: 40,
        border: `2px solid ${LARANJA}`,
        transform: `scale(${s})`,
      }}
    >
      ✓ {texto}
    </div>
  );
};

// ---------- 26,3 s até o fim · fechamento ----------
const Fechamento: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const sobe = useSpring(26.3, { damping: 14, stiffness: 160 });
  const cheio = interpolate(frame, [durationInFrames - f(0.9), durationInFrames - f(0.5)], [0, 1], clamp);
  const logo = useSpring((durationInFrames - f(0.85)) / FPS, { damping: 12, stiffness: 200 });
  return (
    <AbsoluteFill style={{ fontFamily: FONTE }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 0,
          height: 980,
          background: `linear-gradient(to bottom, rgba(10,10,15,0), rgba(10,10,15,.92) 35%, ${PRETO})`,
          transform: `translateY(${(1 - sobe) * 600}px)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: SEGURA.esquerda,
          right: SEGURA.direita - 60,
          bottom: SEGURA.base + 300,
          transform: `translateY(${(1 - sobe) * 300}px)`,
          opacity: sobe,
        }}
      >
        <Glitch texto="BLACK" tamanho={150} inicio={26.3} cor={LARANJA} />
        <div style={{ color: "white", fontWeight: 600, fontSize: 64, marginTop: 4 }}>Facilita Pass</div>
        <div style={{ color: BEGE, fontWeight: 500, fontSize: 38, marginTop: 14 }}>Novembro inteiro · ofertas todos os dias</div>
      </div>
      <AbsoluteFill style={{ backgroundColor: PRETO, opacity: cheio, alignItems: "center", justifyContent: "center" }}>
        <Img src={staticFile("marca/logo.png")} style={{ width: 640, transform: `scale(${logo})` }} />
        <div style={{ color: LARANJA, fontWeight: 700, fontSize: 56, marginTop: 40, letterSpacing: 6, opacity: logo }}>BLACK FACILITA</div>
        <div style={{ color: "white", fontWeight: 500, fontSize: 38, marginTop: 12, opacity: logo }}>Entre no grupo VIP</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------- legenda palavra por palavra ----------
type Palavra = [number, number, string];
const GRUPOS: Palavra[][] = (() => {
  const g: Palavra[][] = [];
  let atual: Palavra[] = [];
  for (const p of palavras as Palavra[]) {
    atual.push(p);
    const fim = /[.,?!]$/.test(p[2]);
    if (atual.length >= 3 || fim) {
      g.push(atual);
      atual = [];
    }
  }
  if (atual.length) g.push(atual);
  return g;
})();

const Legenda: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const grupo = GRUPOS.find((g, i) => t >= g[0][0] && t < (GRUPOS[i + 1]?.[0][0] ?? g[g.length - 1][1] + 0.3));
  if (!grupo || t > 29.75) return null;
  const ini = f(grupo[0][0]);
  const pop = interpolate(frame - ini, [0, 3], [0.85, 1], { ...clamp, easing: Easing.out(Easing.back(2)) });
  return (
    <AbsoluteFill style={{ fontFamily: FONTE, justifyContent: "flex-end", alignItems: "center", paddingBottom: SEGURA.base + 20 }}>
      <div style={{ display: "flex", columnGap: 22, rowGap: 4, flexWrap: "wrap", justifyContent: "center", maxWidth: 1080 - SEGURA.esquerda - SEGURA.direita + 60, transform: `scale(${pop})` }}>
        {grupo.map(([a, , txt], i) => {
          const ativa = t >= a;
          const chave = DESTAQUES.has(txt.toLowerCase());
          const limpo = txt.replace(/[,]$/, "");
          return (
            <span
              key={i}
              style={{
                fontWeight: 700,
                fontSize: 66,
                textTransform: "uppercase",
                color: ativa ? (chave ? LARANJA : "white") : "rgba(255,255,255,.45)",
                WebkitTextStroke: "3px rgba(0,0,0,.85)",
                paintOrder: "stroke fill",
                textShadow: "0 6px 18px rgba(0,0,0,.6)",
                transform: ativa && chave ? "rotate(-2deg)" : undefined,
                display: "inline-block",
              }}
            >
              {limpo}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const BlackFacilita: React.FC<BlackProps> = ({ comMusica }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: PRETO }}>
      <Camera />
      <Acabamento />
      <Janela de={0} ate={3.42}>
        <Gancho />
      </Janela>
      <Janela de={3.42} ate={4.5}>
        <Novidade />
      </Janela>
      <Janela de={4.5} ate={10.7}>
        <JaComecou />
      </Janela>
      <Janela de={10.7} ate={17.2}>
        <Destinos />
      </Janela>
      <Janela de={17.2} ate={26.3}>
        <GrupoVip />
      </Janela>
      <Janela de={26.3} ate={31}>
        <Fechamento />
      </Janela>
      <Legenda />
      <Audio src={staticFile("bf/voz.wav")} />
      {comMusica ? <Audio src={staticFile("bf/musica.mp3")} volume={0.3} /> : null}
    </AbsoluteFill>
  );
};
