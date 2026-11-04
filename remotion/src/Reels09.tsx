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
import dados from "./r09-dados.json";

// Reels 09 · "Check-out ao meio-dia e voo às seis da tarde?" (fala real + legendas).
// Os trechos e as legendas vêm de scripts/preparar_r09.py.
const FINAL = 84;

/** Trecho de vídeo em tela cheia; `zoom` alterna o enquadramento para disfarçar o corte na fala. */
const Trecho: React.FC<{
  readonly arquivo: string;
  readonly zoom?: number;
  readonly duracao: number;
}> = ({ arquivo, zoom = 1, duracao }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO }}>
      <Video
        src={staticFile(`r09/${arquivo}`)}
        muted
        objectFit="cover"
        premountFor={fps}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          filter: "contrast(1.05) saturate(1.1)",
          transformOrigin: "50% 38%",
          scale: zoom * interpolate(frame, [0, duracao], [1, 1.035], clamp),
        }}
      />
    </AbsoluteFill>
  );
};

/** Imagem de apoio que cobre a fala, com entrada rápida. */
const Apoio: React.FC<{ readonly arquivo: string; readonly duracao: number }> = ({
  arquivo,
  duracao,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      <Video
        src={staticFile(`r09/${arquivo}`)}
        muted
        objectFit="cover"
        premountFor={fps}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          filter: "contrast(1.06) saturate(1.14)",
          scale: interpolate(frame, [0, 7, duracao], [1.16, 1.04, 1.1], {
            ...clamp,
            easing: Easing.out(Easing.cubic),
          }),
        }}
      />
    </AbsoluteFill>
  );
};

/** Legenda em blocos curtos; a palavra falada fica laranja. */
const Legendas: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const grupos = dados.grupos;
  let i = -1;
  for (let k = 0; k < grupos.length; k++) {
    if (grupos[k][0].quadro <= frame) i = k;
  }
  if (i < 0) return null;
  const grupo = grupos[i];
  const fim = i + 1 < grupos.length ? grupos[i + 1][0].quadro : dados.total;
  if (frame >= Math.min(fim, grupo[grupo.length - 1].quadro + 45)) return null;
  const entra = spring({
    frame: frame - grupo[0].quadro,
    fps,
    config: { damping: 14, stiffness: 260, mass: 0.5 },
  });
  return (
    <div
      style={{
        position: "absolute",
        left: SEGURA.esquerda,
        right: SEGURA.direita,
        bottom: SEGURA.base + 120,
        textAlign: "center",
        fontFamily: FONTE,
        fontWeight: 700,
        fontSize: 82,
        lineHeight: 1.12,
        letterSpacing: "-0.01em",
        color: "white",
        textShadow: "0 4px 18px rgba(0,0,0,.85), 0 0 4px rgba(0,0,0,.6)",
        scale: interpolate(entra, [0, 1], [0.86, 1]),
      }}
    >
      {grupo.map((p, k) => {
        const ativa = p.quadro <= frame && (k + 1 >= grupo.length || grupo[k + 1].quadro > frame);
        return (
          <span key={k} style={{ color: ativa ? LARANJA : "white" }}>
            {p.texto}
            {k + 1 < grupo.length ? " " : ""}
          </span>
        );
      })}
    </div>
  );
};

/** Gancho escrito sobre o primeiro trecho: os dois horários e a pergunta. */
const Gancho: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const etiqueta = (atraso: number) =>
    spring({ frame: frame - atraso, fps, config: { damping: 11, stiffness: 200, mass: 0.7 } });
  const linha: React.CSSProperties = {
    display: "inline-block",
    padding: "4px 30px 8px",
    borderRadius: 26,
    fontSize: 92,
    fontWeight: 700,
    lineHeight: 1.15,
    transformOrigin: "left center",
  };
  return (
    <div
      style={{
        position: "absolute",
        left: SEGURA.esquerda,
        right: SEGURA.direita,
        top: SEGURA.topo + 20,
        fontFamily: FONTE,
        color: "white",
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        gap: 14,
        opacity: interpolate(frame, [112, 122], [1, 0], clamp),
      }}
    >
      <div style={{ ...linha, backgroundColor: MARINHO, scale: etiqueta(4), rotate: "-2deg" }}>
        Check-out: 12h
      </div>
      <div style={{ ...linha, backgroundColor: LARANJA, scale: etiqueta(48), rotate: "1.5deg" }}>
        Voo: 18h
      </div>
      <div style={{ fontSize: 76, fontWeight: 700, textShadow: sombra, marginTop: 6 }}>
        <Sobe atraso={92}>E agora?</Sobe>
      </div>
    </div>
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
  return (
    <AbsoluteFill>
      <Apoio arquivo="apoio_fundo.mp4" duracao={FINAL} />
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
        <Img src={staticFile("marca/logo.png")} style={{ width: 600, ...linha(2) }} />
        <div style={{ marginTop: 90, fontSize: 56, fontWeight: 500, color: BEGE, ...linha(6) }}>
          Vai pro México?
        </div>
        <div style={{ fontSize: 104, fontWeight: 700, lineHeight: 1.1, ...linha(9) }}>
          Salva pra sua viagem
        </div>
        <div style={{ marginTop: 36, fontSize: 50, fontWeight: 500, color: BEGE, ...linha(16) }}>
          e manda pra quem vai com você
        </div>
        <Img src={staticFile("marca/selo.png")} style={{ marginTop: 80, width: 250, ...linha(22) }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Reels09: React.FC = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO }}>
      <Series>
        <Series.Sequence name="Check-out 12h, voo 18h" durationInFrames={123} premountFor={fps}>
          <Trecho arquivo="fala_a.mp4" duracao={123} />
          <Gancho />
        </Series.Sequence>
        <Series.Sequence name="Sala de hospitalidade" durationInFrames={193} premountFor={fps}>
          <Trecho arquivo="fala_b.mp4" zoom={1.14} duracao={193} />
        </Series.Sequence>
        <Series.Sequence name="Continua com tudo incluso" durationInFrames={202} premountFor={fps}>
          <Trecho arquivo="fala_c.mp4" duracao={202} />
          <Sequence name="Apoio: piscina" from={50} durationInFrames={76} premountFor={fps}>
            <Apoio arquivo="apoio_piscina.mp4" duracao={76} />
          </Sequence>
          <Sequence name="Apoio: buffet" from={126} durationInFrames={76} premountFor={fps}>
            <Apoio arquivo="apoio_buffet.mp4" duracao={76} />
          </Sequence>
        </Series.Sequence>
        <Series.Sequence name="O papel do check-out" durationInFrames={214} premountFor={fps}>
          <Trecho arquivo="fala_d.mp4" duracao={214} />
        </Series.Sequence>
        <Series.Sequence name="Chegou cedo" durationInFrames={100} premountFor={fps}>
          <Trecho arquivo="fala_e1.mp4" zoom={1.1} duracao={100} />
        </Series.Sequence>
        <Series.Sequence name="Quarto às três" durationInFrames={35} premountFor={fps}>
          <Trecho arquivo="fala_e2.mp4" duracao={35} />
        </Series.Sequence>
        <Series.Sequence name="Desde o primeiro momento" durationInFrames={95} premountFor={fps}>
          <Trecho arquivo="fala_e3.mp4" zoom={1.1} duracao={95} />
          <Sequence name="Apoio: caminho da piscina" from={12} premountFor={fps}>
            <Apoio arquivo="apoio_caminho.mp4" duracao={83} />
          </Sequence>
        </Series.Sequence>
        <Series.Sequence name="Cartão final" durationInFrames={FINAL} premountFor={fps}>
          <Final />
        </Series.Sequence>
      </Series>
      <Sequence name="Legendas" durationInFrames={962} premountFor={fps}>
        <Degrade />
        <Legendas />
      </Sequence>
      <Audio name="Fala" src={staticFile("r09/voz.wav")} premountFor={fps} />
    </AbsoluteFill>
  );
};
