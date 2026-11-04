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
import { clamp, Sobe, sombra } from "./AllFunInclusive";
import { BEGE, FONTE, LARANJA, MARINHO, SEGURA } from "./marca";
import dados from "./ad02-dados.json";

// Anúncio 01 · Hotel Xcaret México em família. Planos: scripts/preparar_ad02.py
// comMusica=false gera a versão muda (música escolhida no Gerenciador de Anúncios).
export type Ad02Props = { comMusica: boolean };

const Plano: React.FC<{ readonly arquivo: string; readonly duracao: number; readonly i: number }> = ({ arquivo, duracao, i }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO }}>
      <Video
        src={staticFile(`ad02/${arquivo}`)}
        muted
        objectFit="cover"
        premountFor={fps}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          filter: "contrast(1.07) saturate(1.15)",
          scale: interpolate(frame, [0, 6, duracao], i % 2 ? [1.16, 1.07, 1.02] : [1.14, 1.02, 1.08], {
            ...clamp,
            easing: Easing.out(Easing.cubic),
          }),
        }}
      />
    </AbsoluteFill>
  );
};

const Escuro: React.FC<{ readonly forte?: boolean }> = ({ forte }) => (
  <AbsoluteFill
    style={{
      background: forte
        ? "linear-gradient(to bottom, rgba(6,20,44,.55), rgba(6,20,44,.35) 40%, rgba(6,20,44,.75))"
        : "linear-gradient(to bottom, rgba(6,20,44,.5) 0%, rgba(6,20,44,0) 25%, rgba(6,20,44,0) 55%, rgba(6,20,44,.7) 100%)",
    }}
  />
);

const Etiqueta: React.FC<{ readonly texto: string }> = ({ texto }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - 2, fps, config: { damping: 11, stiffness: 240, mass: 0.55 } });
  return (
    <div style={{ position: "absolute", left: SEGURA.esquerda, right: SEGURA.direita, bottom: SEGURA.base + 80, fontFamily: FONTE }}>
      <div
        style={{
          display: "inline-block",
          padding: "6px 30px 12px",
          borderRadius: 24,
          backgroundColor: LARANJA,
          color: "white",
          fontWeight: 700,
          fontSize: texto.length > 22 ? 70 : 88,
          lineHeight: 1.1,
          transformOrigin: "left center",
          scale: interpolate(pop, [0, 1], [0.4, 1]),
          opacity: interpolate(frame, [0, 3], [0, 1], clamp),
          rotate: "-2deg",
        }}
      >
        {texto}
      </div>
    </div>
  );
};

const Gancho: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - 36, fps, config: { damping: 10, stiffness: 200, mass: 0.7 } });
  return (
    <div style={{ position: "absolute", left: SEGURA.esquerda, right: SEGURA.direita, top: 500, fontFamily: FONTE, fontWeight: 700, color: "white" }}>
      <div style={{ fontSize: 92, lineHeight: 1.08, letterSpacing: "-0.02em", textShadow: sombra }}>
        <Sobe atraso={2}>Seu</Sobe> <Sobe atraso={5}>filho</Sobe> <Sobe atraso={8}>vai</Sobe> <Sobe atraso={11}>pedir</Sobe> <Sobe atraso={14}>pra</Sobe>
      </div>
      <div style={{ display: "inline-block", marginTop: 20, padding: "4px 30px 12px", borderRadius: 26, backgroundColor: LARANJA, fontSize: 104, lineHeight: 1.1,
        transformOrigin: "left center", scale: interpolate(pop, [0, 1], [0, 1]), rotate: "-3deg" }}>
        morar nesse hotel
      </div>
    </div>
  );
};

const Hotel: React.FC = () => (
  <div style={{ position: "absolute", left: SEGURA.esquerda, right: SEGURA.direita, top: 560, fontFamily: FONTE, color: "white", textShadow: sombra }}>
    <div style={{ fontSize: 150, fontWeight: 700, lineHeight: 1 }}>
      <Sobe atraso={2}>4 noites</Sobe>
    </div>
    <div style={{ marginTop: 16, fontSize: 70, fontWeight: 600, lineHeight: 1.1 }}>
      <Sobe atraso={8}>no Hotel Xcaret México</Sobe>
    </div>
    <div style={{ marginTop: 14, fontSize: 48, fontWeight: 500, color: BEGE }}>
      <Sobe atraso={14}>All-Fun Inclusive® · Riviera Maya</Sobe>
    </div>
  </div>
);

const Oferta: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entra = (a: number) => spring({ frame: frame - a, fps, config: { damping: 200 } });
  const linha = (a: number): React.CSSProperties => ({ opacity: entra(a), translate: `0px ${interpolate(entra(a), [0, 1], [36, 0])}px` });
  const preco = spring({ frame: frame - 20, fps, config: { damping: 11, stiffness: 180, mass: 0.7 } });
  const cta = frame - 150;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ backgroundColor: MARINHO, opacity: interpolate(frame, [0, 10], [0, 0.82], clamp) }} />
      <AbsoluteFill
        style={{
          left: SEGURA.esquerda,
          right: SEGURA.direita,
          width: "auto",
          top: SEGURA.topo,
          bottom: SEGURA.base - 60,
          height: "auto",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: FONTE,
          color: "white",
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: 46, fontWeight: 600, color: BEGE, ...linha(2) }}>4 noites · Hotel Xcaret México</div>
        <div style={{ marginTop: 10, fontSize: 44, fontWeight: 500, ...linha(6) }}>2 adultos + 2 crianças até 17 anos</div>
        <div
          style={{
            marginTop: 14,
            display: "inline-block",
            padding: "4px 22px 8px",
            borderRadius: 16,
            backgroundColor: "rgba(255,255,255,.14)",
            fontSize: 40,
            fontWeight: 600,
            ...linha(10),
          }}
        >
          crianças inclusas gratuitamente
        </div>
        <div style={{ marginTop: 44, fontSize: 44, fontWeight: 500, ...linha(16) }}>a partir de</div>
        <div
          style={{
            fontSize: 150,
            fontWeight: 700,
            lineHeight: 1.05,
            letterSpacing: "-0.03em",
            color: "white",
            scale: interpolate(preco, [0, 1], [0.6, 1]),
            opacity: interpolate(frame, [20, 26], [0, 1], clamp),
          }}
        >
          R$ 21.073
        </div>
        <div
          style={{
            marginTop: 26,
            display: "inline-block",
            padding: "10px 34px 14px",
            borderRadius: 22,
            backgroundColor: LARANJA,
            fontSize: 58,
            fontWeight: 700,
            ...linha(42),
          }}
        >
          10x sem juros no cartão
        </div>
        <div style={{ marginTop: 18, fontSize: 52, fontWeight: 600, ...linha(56) }}>ou até 24x no NuPay</div>
        <div
          style={{
            marginTop: 60,
            padding: "26px 56px",
            borderRadius: 80,
            backgroundColor: "white",
            color: MARINHO,
            fontSize: 56,
            fontWeight: 700,
            opacity: interpolate(cta, [0, 8], [0, 1], clamp),
            scale: interpolate(cta, [0, 8], [0.7, 1], clamp) * (1 + 0.03 * Math.sin(Math.max(0, cta - 10) / 5)),
          }}
        >
          Chame a gente e garanta a sua
        </div>
        <div style={{ marginTop: 50, display: "flex", alignItems: "center", gap: 40, opacity: interpolate(cta, [6, 16], [0, 1], clamp) }}>
          <Img src={staticFile("marca/logo.png")} style={{ width: 380 }} />
          <Img src={staticFile("marca/selo.png")} style={{ width: 190 }} />
        </div>
      </AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: SEGURA.esquerda,
          right: SEGURA.direita,
          bottom: 130,
          fontFamily: FONTE,
          fontSize: 24,
          lineHeight: 1.3,
          color: "rgba(255,255,255,.75)",
          textAlign: "center",
          opacity: interpolate(frame, [40, 50], [0, 1], clamp),
        }}
      >
        Valor total do pacote para 2 adultos e 2 crianças até 17 anos, 4 noites. Sujeito a disponibilidade e alteração sem aviso prévio.
      </div>
    </AbsoluteFill>
  );
};

export const Ad02: React.FC<Ad02Props> = ({ comMusica }) => {
  const { fps } = useVideoConfig();
  const ultimo = dados.linha.length - 1;
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO }}>
      <Series>
        {dados.linha.map((p, i) => (
          <Series.Sequence key={p.arquivo} name={p.texto || `Plano ${i + 1}`} durationInFrames={p.quadros} premountFor={fps}>
            <Plano arquivo={p.arquivo} duracao={p.quadros} i={i} />
            {i === 0 ? (<><Escuro forte /><Gancho /></>) : null}
            {i === 4 ? (<><Escuro forte /><Hotel /></>) : null}
            {i > 0 && i !== 4 && i < ultimo ? (<><Escuro /><Etiqueta texto={p.texto} /></>) : null}
            {i === ultimo ? <Oferta /> : null}
          </Series.Sequence>
        ))}
      </Series>
      {comMusica ? <Audio name="Trilha" src={staticFile("ad02/musica.wav")} premountFor={fps} /> : null}
      <Sequence durationInFrames={1} premountFor={fps}><></></Sequence>
    </AbsoluteFill>
  );
};
