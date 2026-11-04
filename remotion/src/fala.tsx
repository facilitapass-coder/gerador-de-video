import { Video } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { clamp } from "./AllFunInclusive";
import { FONTE, LARANJA, MARINHO, SEGURA } from "./marca";

// Peças comuns dos Reels de fala real (trechos preparados por scripts/preparar_fala.py).

export type DadosFala = {
  total: number;
  grupos: { quadro: number; texto: string }[][];
};

/** Trecho de fala em tela cheia; `zoom` alterna o enquadramento para disfarçar o corte. */
export const Trecho: React.FC<{
  readonly src: string;
  readonly zoom?: number;
  readonly duracao: number;
}> = ({ src, zoom = 1, duracao }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO }}>
      <Video
        src={staticFile(src)}
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
export const Apoio: React.FC<{ readonly src: string; readonly duracao: number }> = ({
  src,
  duracao,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      <Video
        src={staticFile(src)}
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
export const Legendas: React.FC<{ readonly dados: DadosFala }> = ({ dados }) => {
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
