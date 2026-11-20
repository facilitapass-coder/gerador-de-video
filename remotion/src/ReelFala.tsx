import { Audio } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
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
import { DadosFala, Legendas, Trecho, Trilha } from "./fala";
import { BEGE, FONTE, LARANJA, MARINHO, SEGURA } from "./marca";

// Reels de fala real: gancho escrito, trechos com legenda e cartão final com pergunta.
// Propriedades em public/<id>/dados.json (scripts/preparar_fala.py com "reel" no config).
export type ReelFalaProps = DadosFala & {
  id: string;
  gancho: string;
  etiqueta: string;
  final1: string;
  final2: string;
  final3: string;
  linha: { nome: string; quadros: number; inicio: number; mudo: boolean }[];
  /** Segundo da faixa public/<id>/trilha.mp3 onde a música começa; sem ele, sem música. */
  musicaInicio?: number;
};

const FINAL = 96;

export const metadadosReelFala: CalculateMetadataFunction<ReelFalaProps> = ({ props }) => ({
  durationInFrames: Math.max(60, props.total + FINAL),
});

const Gancho: React.FC<{ readonly texto: string }> = ({ texto }) => {
  const frame = useCurrentFrame();
  const palavras = texto.split(" ");
  return (
    <div
      style={{
        position: "absolute",
        left: SEGURA.esquerda,
        right: SEGURA.direita,
        top: SEGURA.topo + 40,
        fontFamily: FONTE,
        fontWeight: 700,
        fontSize: texto.length > 30 ? 96 : 118,
        lineHeight: 1.1,
        letterSpacing: "-0.02em",
        color: "white",
        opacity: interpolate(frame, [100, 112], [1, 0], clamp),
      }}
    >
      {palavras.map((p, i) => (
        <Sobe
          key={i}
          atraso={2 + i * 3}
          style={{
            backgroundColor: i >= palavras.length - 2 ? LARANJA : MARINHO,
            padding: "0 14px",
            marginRight: 8,
            marginBottom: 8,
            borderRadius: 14,
          }}
        >
          {p}
        </Sobe>
      ))}
    </div>
  );
};

const Final: React.FC<ReelFalaProps> = (props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entra = (atraso: number) => spring({ frame: frame - atraso, fps, config: { damping: 200 } });
  const linha = (atraso: number): React.CSSProperties => ({
    opacity: entra(atraso),
    translate: `0px ${interpolate(entra(atraso), [0, 1], [40, 0])}px`,
  });
  const ultimo = props.linha[props.linha.length - 1];
  return (
    <AbsoluteFill>
      <Trecho src={`${props.id}/fala_${ultimo.nome}.mp4`} duracao={FINAL} />
      <AbsoluteFill style={{ backgroundColor: MARINHO, opacity: interpolate(frame, [0, 8], [0, 0.88], clamp) }} />
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
        <div style={{ fontSize: 44, fontWeight: 500, color: BEGE, ...linha(3) }}>{props.final1}</div>
        <div style={{ marginTop: 26, fontSize: 104, fontWeight: 700, lineHeight: 1.1, textShadow: sombra, ...linha(7) }}>
          {props.final2}
        </div>
        <div style={{ marginTop: 30, fontSize: 48, fontWeight: 500, color: BEGE, ...linha(13) }}>{props.final3}</div>
        <Img src={staticFile("marca/logo.png")} style={{ marginTop: 100, width: 520, ...linha(20) }} />
        <Img src={staticFile("marca/selo.png")} style={{ marginTop: 50, width: 230, ...linha(26) }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const ReelFala: React.FC<ReelFalaProps> = (props) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO }}>
      <Series>
        {props.linha.map((t, i) => (
          <Series.Sequence key={t.nome} name={`Trecho ${t.nome}`} durationInFrames={t.quadros} premountFor={fps}>
            <Trecho src={`${props.id}/fala_${t.nome}.mp4`} zoom={t.mudo || i % 2 === 0 ? 1 : 1.1} duracao={t.quadros} semFlash={i === 0} />
          </Series.Sequence>
        ))}
        <Series.Sequence name="Cartão final" durationInFrames={FINAL} premountFor={fps}>
          <Final {...props} />
        </Series.Sequence>
      </Series>
      <Sequence name="Legendas e gancho" durationInFrames={Math.max(1, props.total)} premountFor={fps}>
        <AbsoluteFill
          style={{
            background:
              "linear-gradient(to bottom, rgba(6,20,44,.45) 0%, rgba(6,20,44,0) 24%, rgba(6,20,44,0) 55%, rgba(6,20,44,.62) 100%)",
          }}
        />
        <Legendas dados={props} />
        <Gancho texto={props.gancho} />
      </Sequence>
      <Audio name="Fala" src={staticFile(`${props.id}/voz.wav`)} premountFor={fps} />
      {props.musicaInicio === undefined ? null : (
        <Trilha src={`${props.id}/trilha.mp3`} inicio={props.musicaInicio} fimFala={props.total} total={props.total + FINAL} />
      )}
    </AbsoluteFill>
  );
};
