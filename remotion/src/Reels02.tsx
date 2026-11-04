import { Audio, Video } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  Sequence,
  Series,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { clamp, Degrade, Sobe, sombra } from "./AllFunInclusive";
import { BEGE, FONTE, LARANJA, MARINHO, SEGURA } from "./marca";
import dados from "./r02-dados.json";

// Reels 02 · La Casa de la Playa, narrado. Planos e tempos: scripts/preparar_r02.py

const Plano: React.FC<{ readonly arquivo: string; readonly duracao: number; readonly i: number }> = ({
  arquivo,
  duracao,
  i,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO }}>
      <Video
        src={staticFile(`r02/${arquivo}`)}
        muted
        objectFit="cover"
        premountFor={fps}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          filter: "contrast(1.06) saturate(1.12)",
          scale: interpolate(frame, [0, 6, duracao], i % 2 ? [1.15, 1.08, 1.02] : [1.13, 1.02, 1.08], {
            ...clamp,
            easing: Easing.out(Easing.cubic),
          }),
        }}
      />
    </AbsoluteFill>
  );
};

/** Texto do plano: linha branca e destaque em etiqueta laranja. */
const Texto: React.FC<{ readonly t1: string; readonly t2: string }> = ({ t1, t2 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - 3, fps, config: { damping: 11, stiffness: 230, mass: 0.6 } });
  if (!t1 && !t2) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: SEGURA.esquerda,
        right: SEGURA.direita,
        bottom: SEGURA.base + 70,
        fontFamily: FONTE,
        fontWeight: 700,
        color: "white",
        letterSpacing: "-0.02em",
      }}
    >
      {t1 ? (
        <div style={{ fontSize: t1.length > 16 ? 84 : 104, lineHeight: 1.08, textShadow: sombra }}>
          <Sobe atraso={1}>{t1}</Sobe>
        </div>
      ) : null}
      {t2 ? (
        <div
          style={{
            display: "inline-block",
            marginTop: 12,
            padding: "2px 30px 8px",
            borderRadius: 24,
            backgroundColor: LARANJA,
            fontSize: t2.length > 13 ? 88 : 112,
            lineHeight: 1.12,
            transformOrigin: "left center",
            scale: interpolate(pop, [0, 1], [0, 1]),
            rotate: "-2.5deg",
          }}
        >
          {t2}
        </div>
      ) : null}
    </div>
  );
};

const Gancho: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - 70, fps, config: { damping: 10, stiffness: 200, mass: 0.7 } });
  return (
    <div
      style={{
        position: "absolute",
        left: SEGURA.esquerda,
        right: SEGURA.direita,
        top: 560,
        fontFamily: FONTE,
        fontWeight: 700,
        color: "white",
        letterSpacing: "-0.02em",
        opacity: interpolate(frame, [138, 147], [1, 0], clamp),
      }}
    >
      <div style={{ fontSize: 170, lineHeight: 1, textShadow: sombra }}>
        <Sobe atraso={2}>Para tudo.</Sobe>
      </div>
      <div style={{ marginTop: 20, fontSize: 80, lineHeight: 1.1, textShadow: sombra }}>
        <Sobe atraso={26}>Essa suíte tem</Sobe>
      </div>
      <div
        style={{
          display: "inline-block",
          marginTop: 10,
          padding: "2px 30px 10px",
          borderRadius: 26,
          backgroundColor: LARANJA,
          fontSize: 124,
          lineHeight: 1.12,
          transformOrigin: "left center",
          scale: interpolate(pop, [0, 1], [0, 1]),
          rotate: "-3deg",
        }}
      >
        águas-vivas
      </div>
      <div style={{ marginTop: 12, fontSize: 80, textShadow: sombra }}>
        <Sobe atraso={96}>na parede</Sobe>
      </div>
    </div>
  );
};

const Final: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entra = (atraso: number) => spring({ frame: frame - atraso, fps, config: { damping: 200 } });
  const linha = (atraso: number): React.CSSProperties => ({
    opacity: entra(atraso),
    translate: `0px ${interpolate(entra(atraso), [0, 1], [40, 0])}px`,
  });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ backgroundColor: MARINHO, opacity: interpolate(frame, [0, 8], [0, 0.86], clamp) }} />
      <AbsoluteFill
        style={{
          left: SEGURA.esquerda,
          right: SEGURA.direita,
          width: "auto",
          top: SEGURA.topo,
          bottom: SEGURA.base,
          height: "auto",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: FONTE,
          color: "white",
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: 46, fontWeight: 500, color: BEGE, ...linha(2) }}>La Casa de la Playa · Riviera Maya</div>
        <div style={{ marginTop: 26, fontSize: 108, fontWeight: 700, lineHeight: 1.1, ...linha(6) }}>
          Com quem você viria pra cá?
        </div>
        <Img src={staticFile("marca/logo.png")} style={{ marginTop: 100, width: 540, ...linha(16) }} />
        <Img src={staticFile("marca/selo.png")} style={{ marginTop: 50, width: 240, ...linha(22) }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Reels02: React.FC = () => {
  const { fps } = useVideoConfig();
  const ultimo = dados.linha.length - 1;
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO }}>
      <Series>
        {dados.linha.map((p, i) => (
          <Series.Sequence key={p.arquivo} name={p.t2 || p.t1 || `Plano ${i + 1}`} durationInFrames={p.quadros} premountFor={fps}>
            <Plano arquivo={p.arquivo} duracao={p.quadros} i={i} />
            {i === ultimo ? <Final /> : <Degrade />}
            {i > 1 && i < ultimo ? <Texto t1={p.t1} t2={p.t2} /> : null}
          </Series.Sequence>
        ))}
      </Series>
      <Sequence name="Gancho" durationInFrames={147} premountFor={fps}>
        <Gancho />
      </Sequence>
      <Audio name="Narração" src={staticFile("r02/voz.wav")} premountFor={fps} />
    </AbsoluteFill>
  );
};
