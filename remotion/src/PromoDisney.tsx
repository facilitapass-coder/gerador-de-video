import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { sombra } from "./AllFunInclusive";
import { BEGE, FONTE, LARANJA, MARINHO } from "./marca";

// Imagem para grupo de WhatsApp · promoção do dia nos ingressos Disney.
export type PromoDisneyProps = { foto: string; data: string; focoY: number };

export const PromoDisney: React.FC<PromoDisneyProps> = ({ foto, data, focoY }) => (
  <AbsoluteFill style={{ backgroundColor: MARINHO, fontFamily: FONTE }}>
    <Img
      src={staticFile(`orlando/${foto}`)}
      style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: `50% ${focoY}%`, filter: "saturate(1.12)" }}
    />
    <AbsoluteFill
      style={{
        background:
          "linear-gradient(to bottom, rgba(6,20,44,.82) 0%, rgba(6,20,44,.35) 32%, rgba(6,20,44,.05) 48%, rgba(6,20,44,.55) 66%, rgba(6,20,44,.95) 100%)",
      }}
    />

    <div style={{ position: "absolute", top: 60, left: 60, right: 60, display: "flex", justifyContent: "space-between" }}>
      <div style={{ backgroundColor: LARANJA, color: "white", fontWeight: 700, fontSize: 34, letterSpacing: 2, padding: "12px 26px", borderRadius: 40 }}>
        SOMENTE HOJE · {data}
      </div>
      <div style={{ border: "3px solid white", color: "white", fontWeight: 600, fontSize: 28, padding: "10px 22px", borderRadius: 40 }}>
        Estoque limitado
      </div>
    </div>

    <div style={{ position: "absolute", top: 170, left: 60, right: 60, color: "white", textShadow: sombra }}>
      <div style={{ fontWeight: 600, fontSize: 52, lineHeight: 1.1 }}>Promoção relâmpago</div>
      <div style={{ fontWeight: 600, fontSize: 52, lineHeight: 1.1, color: BEGE }}>pra sua viagem a Orlando</div>
    </div>

    <div style={{ position: "absolute", left: 60, right: 60, bottom: 60 }}>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 24 }}>
        <div style={{ color: LARANJA, fontWeight: 700, fontSize: 250, lineHeight: 0.85, textShadow: "0 8px 30px rgba(0,0,0,.45)" }}>7%</div>
        <div style={{ color: "white", fontWeight: 700, fontSize: 92, lineHeight: 0.95, paddingBottom: 12, textShadow: sombra }}>OFF</div>
      </div>
      <div style={{ color: "white", fontWeight: 500, fontSize: 40, marginTop: 18, textShadow: sombra }}>
        nos ingressos dos parques Disney
      </div>
      <div
        style={{
          marginTop: 30,
          backgroundColor: "white",
          color: MARINHO,
          borderRadius: 24,
          padding: "22px 30px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ fontWeight: 700, fontSize: 38 }}>Chama a gente e garanta o seu</div>
        <div style={{ fontSize: 44 }}>👉</div>
      </div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 22 }}>
        <div style={{ color: "rgba(255,255,255,.85)", fontSize: 22, lineHeight: 1.35, maxWidth: 560 }}>
          Válido somente em {data},
          <br />
          ou enquanto durar o estoque.
        </div>
        <Img src={staticFile("marca/logo.png")} style={{ height: 62 }} />
      </div>
    </div>
  </AbsoluteFill>
);
