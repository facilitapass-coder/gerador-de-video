import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { sombra } from "./AllFunInclusive";
import { BEGE, FONTE, LARANJA, MARINHO, SEGURA } from "./marca";

// Anúncio estático Orlando · Aéreo + Hotel, 13 noites, fev a mai/2027 (topo de funil).
// Renderizado com `npx remotion still` em 1080×1350 (feed) e 1080×1920 (stories/reels).
export type OrlandoProps = {
  foto: string;
  linha1: string;
  linha2: string;
  focoY: number; // posição vertical da foto (0 a 100)
  largura: number;
  altura: number;
};

export const metadadosOrlando = ({ props }: { props: OrlandoProps }) => ({
  width: props.largura,
  height: props.altura,
});

export const OrlandoEstatico: React.FC<OrlandoProps> = ({ foto, linha1, linha2, focoY, altura }) => {
  const vertical = altura > 1600;
  const topo = vertical ? SEGURA.topo - 40 : 70;
  const base = vertical ? SEGURA.base - 60 : 60;
  return (
    <AbsoluteFill style={{ backgroundColor: MARINHO, fontFamily: FONTE }}>
      <Img
        src={staticFile(`orlando/${foto}`)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          objectPosition: `50% ${focoY}%`,
          filter: "contrast(1.05) saturate(1.12)",
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to bottom, rgba(6,20,44,.78) 0%, rgba(6,20,44,.25) 30%, rgba(6,20,44,0) 45%, rgba(6,20,44,.2) 58%, rgba(6,20,44,.88) 100%)",
        }}
      />

      <div style={{ position: "absolute", top: topo, left: 60, right: 60 }}>
        <div
          style={{
            display: "inline-block",
            backgroundColor: LARANJA,
            color: "white",
            fontWeight: 600,
            fontSize: 30,
            letterSpacing: 1.5,
            padding: "10px 22px",
            borderRadius: 40,
          }}
        >
          ORLANDO · FEV A MAI 2027
        </div>
        <div
          style={{
            color: "white",
            fontWeight: 700,
            fontSize: vertical ? 84 : 76,
            lineHeight: 1.05,
            marginTop: 26,
            textShadow: sombra,
          }}
        >
          {linha1}
          <br />
          <span style={{ color: BEGE, fontWeight: 600 }}>{linha2}</span>
        </div>
      </div>

      <div style={{ position: "absolute", left: 60, right: 60, bottom: base }}>
        <div
          style={{
            backgroundColor: "white",
            borderRadius: 28,
            padding: "28px 36px 26px",
            boxShadow: "0 18px 50px rgba(0,0,0,.35)",
          }}
        >
          <div style={{ color: MARINHO, fontWeight: 600, fontSize: 32 }}>
            Aéreo + Hotel · 13 noites
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 14, marginTop: 4 }}>
            <span style={{ color: MARINHO, fontWeight: 500, fontSize: 36 }}>a partir de 10x de</span>
            <span style={{ color: LARANJA, fontWeight: 700, fontSize: 96, lineHeight: 1.05 }}>
              R$ 633,80
            </span>
          </div>
          <div style={{ color: MARINHO, fontWeight: 600, fontSize: 34 }}>
            por pessoa, sem juros
            <span style={{ fontWeight: 400, fontSize: 28 }}> · ou até 24x no NuPay</span>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 22 }}>
          <div style={{ color: "rgba(255,255,255,.85)", fontSize: 21, lineHeight: 1.35, maxWidth: 640 }}>
            A partir de R$ 12.676 para 2 pessoas.
            <br />
            Ingressos dos parques não inclusos.
          </div>
          <Img src={staticFile("marca/logo.png")} style={{ height: 70 }} />
        </div>
      </div>
    </AbsoluteFill>
  );
};
