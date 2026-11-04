import { Audio } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  Sequence,
  Series,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { clamp, Degrade } from "./AllFunInclusive";
import { Apoio, Legendas, Trecho } from "./fala";
import { BEGE, FONTE, MARINHO, SEGURA } from "./marca";
import dados from "./r03-dados.json";

// Reels 03 · "Agora, oficialmente, Xpert Xcaret." (fala real + legendas).
// Trechos e legendas: scripts/preparar_fala.py scripts/r03.json
const FINAL = 90;

/** O selo Xperts entra no topo quando a frase é dita. */
const SeloGancho: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({
    frame: frame - 38,
    fps,
    config: { damping: 10, stiffness: 190, mass: 0.7 },
  });
  return (
    <Img
      src={staticFile("marca/selo.png")}
      style={{
        position: "absolute",
        left: SEGURA.esquerda,
        top: SEGURA.topo + 10,
        width: 460,
        transformOrigin: "left top",
        scale: interpolate(pop, [0, 1], [0, 1]),
        rotate: `${interpolate(pop, [0, 1], [-10, -3])}deg`,
        opacity: interpolate(frame, [36, 40, 318, 330], [0, 1, 1, 0], clamp),
        filter: "drop-shadow(0 8px 24px rgba(0,0,0,.45))",
      }}
    />
  );
};

const Final: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entra = (atraso: number) =>
    spring({ frame: frame - atraso, fps, config: { damping: 200 } });
  const linha = (atraso: number): React.CSSProperties => ({
    opacity: entra(atraso),
    translate: `0px ${interpolate(entra(atraso), [0, 1], [40, 0])}px`,
  });
  const selo = spring({ frame: frame - 4, fps, config: { damping: 12, stiffness: 150 } });
  return (
    <AbsoluteFill>
      <Apoio src="r03/apoio_fundo.mp4" duracao={FINAL} />
      <AbsoluteFill
        style={{ backgroundColor: MARINHO, opacity: interpolate(frame, [0, 8], [0, 0.86], clamp) }}
      />
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
        <Img
          src={staticFile("marca/selo.png")}
          style={{
            width: 520,
            scale: interpolate(selo, [0, 1], [0.5, 1]),
            opacity: interpolate(frame, [4, 10], [0, 1], clamp),
          }}
        />
        <div style={{ marginTop: 70, fontSize: 92, fontWeight: 700, lineHeight: 1.1, ...linha(12) }}>
          Sua viagem ao México
        </div>
        <div style={{ marginTop: 14, fontSize: 52, fontWeight: 500, color: BEGE, ...linha(17) }}>
          com quem conhece cada detalhe
        </div>
        <Img src={staticFile("marca/logo.png")} style={{ marginTop: 90, width: 520, ...linha(24) }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Reels03: React.FC = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO }}>
      <Series>
        <Series.Sequence name="Agora, oficialmente, Xpert Xcaret" durationInFrames={92} premountFor={fps}>
          <Trecho src="r03/fala_a.mp4" duracao={92} />
        </Series.Sequence>
        <Series.Sequence name="O que o diploma representa" durationInFrames={243} premountFor={fps}>
          <Trecho src="r03/fala_b.mp4" zoom={1.12} duracao={243} />
          <Sequence name="Apoio: diploma de perto" from={124} durationInFrames={54} premountFor={fps}>
            <Apoio src="r03/apoio_diploma.mp4" duracao={54} />
          </Sequence>
        </Series.Sequence>
        <Series.Sequence name="Convidado pelo Xcaret" durationInFrames={236} premountFor={fps}>
          <Trecho src="r03/fala_c.mp4" duracao={236} />
          <Sequence name="Apoio: foto com o diploma" from={48} durationInFrames={140} premountFor={fps}>
            <Apoio src="r03/apoio_entrega.mp4" duracao={140} />
          </Sequence>
        </Series.Sequence>
        <Series.Sequence name="Formação completa" durationInFrames={182} premountFor={fps}>
          <Trecho src="r03/fala_d.mp4" zoom={1.12} duracao={182} />
          <Sequence name="Apoio: La Casa de la Playa" from={40} durationInFrames={44} premountFor={fps}>
            <Apoio src="r03/apoio_casa.mp4" duracao={44} />
          </Sequence>
          <Sequence name="Apoio: Xcaret Arte" from={84} durationInFrames={44} premountFor={fps}>
            <Apoio src="r03/apoio_arte.mp4" duracao={44} />
          </Sequence>
          <Sequence name="Apoio: Xcaret México" from={128} durationInFrames={54} premountFor={fps}>
            <Apoio src="r03/apoio_mexico.mp4" duracao={54} />
          </Sequence>
        </Series.Sequence>
        <Series.Sequence name="É para vocês" durationInFrames={190} premountFor={fps}>
          <Trecho src="r03/fala_e.mp4" duracao={190} />
        </Series.Sequence>
        <Series.Sequence name="Obrigado" durationInFrames={63} premountFor={fps}>
          <Trecho src="r03/fala_f.mp4" zoom={1.1} duracao={63} />
        </Series.Sequence>
        <Series.Sequence name="Cartão final" durationInFrames={FINAL} premountFor={fps}>
          <Final />
        </Series.Sequence>
      </Series>
      <Sequence name="Legendas" durationInFrames={1006} premountFor={fps}>
        <Degrade />
        <Legendas dados={dados} />
        <SeloGancho />
      </Sequence>
      <Audio name="Fala" src={staticFile("r03/voz.wav")} premountFor={fps} />
    </AbsoluteFill>
  );
};
