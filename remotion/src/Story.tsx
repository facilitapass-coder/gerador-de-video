import { Audio } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  interpolate,
  Sequence,
  Series,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { clamp, Sobe, sombra } from "./AllFunInclusive";
import { DadosFala, Legendas, Trecho } from "./fala";
import { FONTE, LARANJA, MARINHO, SEGURA } from "./marca";

// Story de sequência: trechos preparados por scripts/montar_stories.py.
// As propriedades vêm de public/<id>/dados.json (passado em --props).
export type StoryProps = DadosFala & {
  id: string;
  etiqueta: string;
  titulo: string;
  linha: { nome: string; quadros: number; inicio: number; mudo: boolean }[];
};

export const metadadosStory: CalculateMetadataFunction<StoryProps> = ({ props }) => ({
  durationInFrames: Math.max(30, props.total),
});

/** Etiqueta do lugar, no topo, abaixo do cabeçalho do Instagram. */
const Etiqueta: React.FC<{ readonly texto: string }> = ({ texto }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entra = spring({ frame: frame - 6, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        position: "absolute",
        left: SEGURA.esquerda,
        top: SEGURA.topo + 30,
        display: "flex",
        alignItems: "center",
        gap: 16,
        padding: "12px 28px 14px 22px",
        borderRadius: 50,
        backgroundColor: "rgba(13,45,94,.88)",
        fontFamily: FONTE,
        fontSize: 38,
        fontWeight: 600,
        color: "white",
        opacity: entra,
        translate: `${interpolate(entra, [0, 1], [-30, 0])}px 0px`,
      }}
    >
      <div style={{ width: 18, height: 18, borderRadius: 9, backgroundColor: LARANJA }} />
      {texto}
    </div>
  );
};

/** Título grande nos primeiros segundos (ou o tempo todo, quando o Story não tem fala). */
const Titulo: React.FC<{ readonly texto: string; readonly fixo: boolean }> = ({ texto, fixo }) => {
  const frame = useCurrentFrame();
  const palavras = texto.split(" ");
  return (
    <div
      style={{
        position: "absolute",
        left: SEGURA.esquerda,
        right: SEGURA.direita,
        top: 560,
        fontFamily: FONTE,
        fontWeight: 700,
        fontSize: texto.length > 34 ? 96 : 112,
        lineHeight: 1.08,
        letterSpacing: "-0.02em",
        color: "white",
        textShadow: sombra,
        opacity: fixo ? 1 : interpolate(frame, [78, 90], [1, 0], clamp),
      }}
    >
      {palavras.map((p, i) => (
        <Sobe key={i} atraso={3 + i * 3}>
          {p}
          {i + 1 < palavras.length ? " " : ""}
        </Sobe>
      ))}
    </div>
  );
};

export const Story: React.FC<StoryProps> = (props) => {
  const { fps } = useVideoConfig();
  const semFala = props.grupos.length === 0;
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO }}>
      <Series>
        {props.linha.map((t, i) => (
          <Series.Sequence key={t.nome} name={`Trecho ${t.nome}`} durationInFrames={t.quadros} premountFor={fps}>
            <Trecho src={`${props.id}/fala_${t.nome}.mp4`} zoom={t.mudo || i % 2 === 0 ? 1 : 1.1} duracao={t.quadros} />
          </Series.Sequence>
        ))}
      </Series>
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to bottom, rgba(6,20,44,.5) 0%, rgba(6,20,44,0) 24%, rgba(6,20,44,0) 55%, rgba(6,20,44,.62) 100%)",
        }}
      />
      {props.etiqueta ? <Etiqueta texto={props.etiqueta} /> : null}
      {props.titulo ? <Titulo texto={props.titulo} fixo={semFala} /> : null}
      <Sequence name="Legendas" premountFor={fps}>
        <Legendas dados={props} />
      </Sequence>
      <Audio name="Voz" src={staticFile(`${props.id}/voz.wav`)} premountFor={fps} />
    </AbsoluteFill>
  );
};
