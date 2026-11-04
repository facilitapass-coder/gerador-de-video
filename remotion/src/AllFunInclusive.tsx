import { Audio, Video } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  Series,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { BEGE, FONTE, LARANJA, MARINHO, SEGURA } from "./marca";

// Duração de cada parte, em quadros (30 fps). Cortes secos, sem transição.
// Os cortes seguem a narração (public/audio/narracao.wav): cada cena entra 2 quadros antes da fala.
const REVELA = 29;
const VIRADA = 76;
const FECHO = 41;
const FINAL = 101;

export const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

/** Um plano em tela cheia, com zoom lento e a mesma cor em todos os clips. */
const Plano: React.FC<{
  readonly src: string;
  readonly inicio: number; // segundo do clip em que o plano começa
  readonly duracao: number; // quadros
  readonly afastar?: boolean;
}> = ({ src, inicio, duracao, afastar }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO }}>
      <Video
        src={staticFile(`clips/${src}`)}
        trimBefore={Math.round(inicio * fps)}
        muted
        objectFit="cover"
        premountFor={fps}
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          filter: "contrast(1.07) saturate(1.16)",
          scale: interpolate(
            frame,
            [0, 7, duracao],
            afastar ? [1.2, 1.1, 1.02] : [1.16, 1.03, 1.1],
            { ...clamp, easing: Easing.out(Easing.cubic) },
          ),
        }}
      />
    </AbsoluteFill>
  );
};

/** Escurece a base e o topo para o texto ler sobre qualquer imagem. */
export const Degrade: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        "linear-gradient(to bottom, rgba(6,20,44,.55) 0%, rgba(6,20,44,0) 22%, rgba(6,20,44,0) 50%, rgba(6,20,44,.78) 100%)",
    }}
  />
);

/** Palavra que sobe de trás de uma máscara. */
export const Sobe: React.FC<{
  readonly atraso: number;
  readonly children: React.ReactNode;
  readonly style?: React.CSSProperties;
}> = ({ atraso, children, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({
    frame: frame - atraso,
    fps,
    config: { damping: 16, stiffness: 190, mass: 0.7 },
  });
  return (
    <span
      style={{
        display: "inline-block",
        overflow: "hidden",
        verticalAlign: "top",
        paddingBottom: "0.12em",
        ...style,
      }}
    >
      <span
        style={{
          display: "inline-block",
          translate: `0px ${interpolate(p, [0, 1], [115, 0])}%`,
        }}
      >
        {children}
      </span>
    </span>
  );
};

export const sombra = "0 4px 26px rgba(0,0,0,.55)";

/** "Isso não é a Tailândia": o destino aparece grande e é riscado. */
const Negacao: React.FC<{
  readonly antes: string;
  readonly lugar: string;
  readonly clip: string;
  readonly inicio: number;
  readonly duracao: number;
  readonly risco: number; // quadro em que a palavra é riscada
}> = ({ antes, lugar, clip, inicio, duracao, risco }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Plano src={clip} inicio={inicio} duracao={duracao} />
      <Degrade />
      <div
        style={{
          position: "absolute",
          left: SEGURA.esquerda,
          right: SEGURA.direita,
          top: 600,
          fontFamily: FONTE,
          color: "white",
          textShadow: sombra,
        }}
      >
        <div style={{ fontSize: 72, fontWeight: 600, lineHeight: 1.15 }}>
          <Sobe atraso={1}>{antes}</Sobe>
        </div>
        <div
          style={{
            position: "relative",
            display: "inline-block",
            fontSize: lugar.length > 8 ? 148 : 190,
            fontWeight: 700,
            lineHeight: 1.1,
            letterSpacing: "-0.02em",
          }}
        >
          <Sobe atraso={4}>{lugar}</Sobe>
          <div
            style={{
              position: "absolute",
              left: -14,
              top: "47%",
              height: 22,
              borderRadius: 11,
              backgroundColor: LARANJA,
              rotate: "-3deg",
              transformOrigin: "left center",
              width: `${interpolate(frame, [risco, risco + 7], [0, 106], {
                ...clamp,
                easing: Easing.out(Easing.cubic),
              })}%`,
            }}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** "É o México": a virada do gancho. */
const Revela: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({
    frame: frame - 5,
    fps,
    config: { damping: 10, stiffness: 190, mass: 0.7 },
  });
  return (
    <AbsoluteFill>
      <Plano src="xailing3.mp4" inicio={3} duracao={REVELA} afastar />
      <Degrade />
      <div
        style={{
          position: "absolute",
          left: SEGURA.esquerda,
          right: SEGURA.direita,
          top: 600,
          fontFamily: FONTE,
          color: "white",
        }}
      >
        <div
          style={{
            fontSize: 84,
            fontWeight: 600,
            lineHeight: 1.15,
            textShadow: sombra,
          }}
        >
          <Sobe atraso={1}>É o</Sobe>
        </div>
        <div
          style={{
            display: "inline-block",
            padding: "0 34px 8px",
            borderRadius: 34,
            backgroundColor: LARANJA,
            fontSize: 200,
            fontWeight: 700,
            lineHeight: 1.14,
            transformOrigin: "left center",
            scale: interpolate(pop, [0, 1], [0, 1]),
            rotate: `${interpolate(pop, [0, 1], [-9, -3])}deg`,
          }}
        >
          México
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** "E tá tudo incluso no seu hotel." */
const Virada: React.FC = () => {
  return (
    <AbsoluteFill>
      <Plano src="xcaret2.mp4" inicio={2} duracao={VIRADA} />
      <AbsoluteFill style={{ backgroundColor: "rgba(6,20,44,.38)" }} />
      <div
        style={{
          position: "absolute",
          left: SEGURA.esquerda,
          right: SEGURA.direita,
          top: 600,
          fontFamily: FONTE,
          color: "white",
          textShadow: sombra,
          fontWeight: 700,
          fontSize: 128,
          lineHeight: 1.08,
          letterSpacing: "-0.02em",
        }}
      >
        <div style={{ fontSize: 72, fontWeight: 600 }}>
          <Sobe atraso={1}>E o melhor:</Sobe>
        </div>
        <div>
          <Sobe atraso={21}>tá&nbsp;</Sobe>
          <Sobe atraso={24}>tudo</Sobe>
        </div>
        <div style={{ color: LARANJA, textShadow: "0 4px 22px rgba(0,0,0,.7)" }}>
          <Sobe atraso={33}>incluso</Sobe>
        </div>
        <div style={{ fontSize: 84 }}>
          <Sobe atraso={50}>no&nbsp;</Sobe>
          <Sobe atraso={53}>seu&nbsp;</Sobe>
          <Sobe atraso={56}>hotel.</Sobe>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Um plano da montagem: a experiência e o carimbo "incluso". */
const Incluso: React.FC<{
  readonly texto: string;
  readonly clip: string;
  readonly inicio: number;
  readonly duracao: number;
}> = ({ texto, clip, inicio, duracao }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const carimbo = spring({
    frame: frame - 9,
    fps,
    config: { damping: 9, stiffness: 260, mass: 0.6 },
  });
  return (
    <AbsoluteFill>
      <Plano src={clip} inicio={inicio} duracao={duracao} afastar />
      <Degrade />
      <div
        style={{
          position: "absolute",
          left: SEGURA.esquerda,
          right: SEGURA.direita,
          bottom: SEGURA.base + 60,
          fontFamily: FONTE,
          color: "white",
        }}
      >
        <div
          style={{
            fontSize: texto.length > 16 ? 86 : 112,
            fontWeight: 700,
            lineHeight: 1.06,
            letterSpacing: "-0.02em",
            textShadow: sombra,
          }}
        >
          <Sobe atraso={1}>{texto}</Sobe>
        </div>
        <div
          style={{
            display: "inline-block",
            marginTop: 14,
            padding: "4px 30px 8px",
            borderRadius: 22,
            backgroundColor: LARANJA,
            fontSize: 78,
            fontWeight: 700,
            transformOrigin: "left center",
            opacity: interpolate(frame, [9, 11], [0, 1], clamp),
            scale: interpolate(carimbo, [0, 1], [1.9, 1]),
            rotate: "-4deg",
          }}
        >
          incluso
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Uma palavra gigante sobre o plano: "tudo" e depois "incluso". */
const Palavra: React.FC<{
  readonly palavra: string;
  readonly destaque?: boolean;
  readonly clip: string;
  readonly inicio: number;
  readonly duracao: number;
}> = ({ palavra, destaque, clip, inicio, duracao }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({
    frame: frame - 1,
    fps,
    config: { damping: 10, stiffness: 240, mass: 0.6 },
  });
  return (
    <AbsoluteFill>
      <Plano src={clip} inicio={inicio} duracao={duracao} />
      <AbsoluteFill style={{ backgroundColor: "rgba(6,20,44,.3)" }} />
      <div
        style={{
          position: "absolute",
          left: SEGURA.esquerda,
          right: SEGURA.direita,
          top: 760,
          textAlign: "center",
          fontFamily: FONTE,
          fontWeight: 700,
          fontSize: destaque ? 196 : 250,
          lineHeight: 1,
          letterSpacing: "-0.03em",
          color: destaque ? LARANJA : "white",
          textShadow: "0 6px 30px rgba(0,0,0,.65)",
          scale: interpolate(pop, [0, 1], [1.7, 1]),
          opacity: interpolate(frame, [0, 3], [0, 1], clamp),
        }}
      >
        {palavra}
      </div>
    </AbsoluteFill>
  );
};

/** "Um hotel. Todos os parques." */
const Fecho: React.FC = () => {
  return (
    <AbsoluteFill>
      <Plano src="xplorfuego4.mp4" inicio={1} duracao={FECHO} />
      <Degrade />
      <div
        style={{
          position: "absolute",
          left: SEGURA.esquerda,
          right: SEGURA.direita,
          bottom: SEGURA.base + 60,
          fontFamily: FONTE,
          color: "white",
          textShadow: sombra,
          fontWeight: 700,
          fontSize: 132,
          lineHeight: 1.06,
          letterSpacing: "-0.02em",
        }}
      >
        <div>
          <Sobe atraso={2}>Um hotel.</Sobe>
        </div>
        <div style={{ fontSize: 108 }}>
          <Sobe atraso={17}>Todos os</Sobe>
        </div>
        <div style={{ fontSize: 132, color: LARANJA, textShadow: "0 4px 22px rgba(0,0,0,.7)" }}>
          <Sobe atraso={29}>parques.</Sobe>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Final: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entra = (atraso: number) =>
    spring({ frame: frame - atraso, fps, config: { damping: 200 } });
  const logo = spring({
    frame: frame - 2,
    fps,
    config: { damping: 13, stiffness: 150 },
  });
  const linha = (atraso: number): React.CSSProperties => ({
    opacity: entra(atraso),
    translate: `0px ${interpolate(entra(atraso), [0, 1], [40, 0])}px`,
  });
  return (
    <AbsoluteFill>
      <Plano src="xelha7.mp4" inicio={2} duracao={FINAL} />
      <AbsoluteFill
        style={{
          backgroundColor: MARINHO,
          opacity: interpolate(frame, [0, 8], [0, 0.84], clamp),
        }}
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
          src={staticFile("marca/logo.png")}
          style={{
            width: 640,
            scale: interpolate(logo, [0, 1], [0.6, 1]),
            opacity: interpolate(frame, [2, 8], [0, 1], clamp),
          }}
        />
        <div
          style={{
            marginTop: 90,
            fontSize: 56,
            fontWeight: 500,
            color: BEGE,
            ...linha(6),
          }}
        >
          Quer viver
        </div>
        <div
          style={{
            fontSize: 124,
            fontWeight: 700,
            lineHeight: 1.1,
            ...linha(9),
          }}
        >
          tudo isso?
        </div>
        <div
          style={{
            marginTop: 14,
            fontSize: 40,
            fontWeight: 500,
            color: BEGE,
            ...linha(12),
          }}
        >
          All-Fun Inclusive® · Hotéis Xcaret
        </div>
        <div
          style={{
            marginTop: 80,
            padding: "30px 60px",
            borderRadius: 80,
            backgroundColor: LARANJA,
            fontSize: 62,
            fontWeight: 700,
            opacity: entra(14),
            scale:
              interpolate(entra(14), [0, 1], [0.7, 1]) *
              (1 + 0.035 * Math.sin(Math.max(0, frame - 26) / 5)),
          }}
        >
          Comente INCLUSIVE
        </div>
        <Img
          src={staticFile("marca/selo.png")}
          style={{ marginTop: 90, width: 270, ...linha(24) }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const AllFunInclusive: React.FC = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO }}>
      <Series>
        <Series.Sequence name="Não é a Tailândia" durationInFrames={70} premountFor={fps}>
          <Negacao antes="Isso aqui não é a" lugar="Tailândia" clip="xenses4.mp4" inicio={15.2} duracao={70} risco={50} />
        </Series.Sequence>
        <Series.Sequence name="Nem as Maldivas" durationInFrames={43} premountFor={fps}>
          <Negacao antes="Nem as" lugar="Maldivas" clip="xcaret7.mp4" inicio={1} duracao={43} risco={30} />
        </Series.Sequence>
        <Series.Sequence name="Nem Bali" durationInFrames={37} premountFor={fps}>
          <Negacao antes="Nem" lugar="Bali" clip="xcaret.mp4" inicio={1} duracao={37} risco={22} />
        </Series.Sequence>
        <Series.Sequence name="É o México" durationInFrames={REVELA} premountFor={fps}>
          <Revela />
        </Series.Sequence>
        <Series.Sequence name="Tudo incluso no seu hotel" durationInFrames={VIRADA} premountFor={fps}>
          <Virada />
        </Series.Sequence>
        <Series.Sequence name="Tirolesa" durationInFrames={24} premountFor={fps}>
          <Incluso texto="Tirolesa" clip="xplor2.mp4" inicio={0.4} duracao={24} />
        </Series.Sequence>
        <Series.Sequence name="Rio subterrâneo" durationInFrames={34} premountFor={fps}>
          <Incluso texto="Rio subterrâneo" clip="xplor2.mp4" inicio={7.4} duracao={34} />
        </Series.Sequence>
        <Series.Sequence name="Snorkel" durationInFrames={26} premountFor={fps}>
          <Incluso texto="Snorkel" clip="xelha8.mp4" inicio={6.5} duracao={26} />
        </Series.Sequence>
        <Series.Sequence name="Cenote" durationInFrames={29} premountFor={fps}>
          <Incluso texto="Cenote" clip="xenotes4.mp4" inicio={6} duracao={29} />
        </Series.Sequence>
        <Series.Sequence name="Festa mexicana" durationInFrames={43} premountFor={fps}>
          <Incluso texto="Festa mexicana" clip="xoximilco3.mp4" inicio={0.8} duracao={43} />
        </Series.Sequence>
        <Series.Sequence name="Tudo" durationInFrames={23} premountFor={fps}>
          <Palavra palavra="tudo" clip="xplorfuego2.mp4" inicio={2} duracao={23} />
        </Series.Sequence>
        <Series.Sequence name="Incluso" durationInFrames={26} premountFor={fps}>
          <Palavra palavra="incluso" destaque clip="xailing2.mp4" inicio={23} duracao={26} />
        </Series.Sequence>
        <Series.Sequence name="Um hotel, todos os parques" durationInFrames={FECHO} premountFor={fps}>
          <Fecho />
        </Series.Sequence>
        <Series.Sequence name="Cartão final" durationInFrames={FINAL} premountFor={fps}>
          <Final />
        </Series.Sequence>
      </Series>
      <Audio name="Narração" src={staticFile("audio/narracao.wav")} premountFor={fps} />
    </AbsoluteFill>
  );
};
