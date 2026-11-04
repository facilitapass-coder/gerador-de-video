import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { COR, FONTE, MARCA, SEGURA } from "../marca";
import { contraste, cor, NomeCor, sombraTexto } from "../componentes/basicos";

// Peça estática (post 1080×1350, story 1080×1920, quadrado 1080×1080, WhatsApp...).
// Renderize com: npx remotion still Arte saida.png --props=props.json
export type ArteProps = {
  largura: number;
  altura: number;
  foto?: string; // arquivo em public/ (foto real)
  focoY?: number; // 0 a 100: posição vertical da foto
  etiqueta?: string; // pílula no topo
  etiquetaDireita?: string; // pílula com contorno no topo, à direita
  titulo: string;
  titulo2?: string; // segunda linha, cor clara
  destaqueGrande?: { valor: string; sufixo?: string; legenda?: string }; // ex.: 7% OFF
  card?: { linha1?: string; prefixo?: string; valor: string; linha2?: string; linha3?: string };
  chamada?: string; // faixa branca com seta
  rodape?: string; // letras miúdas (use \n para quebrar)
  logo?: boolean;
  corDestaque?: NomeCor;
};

export const metadadosArte = ({ props }: { props: ArteProps }) => ({ width: props.largura, height: props.altura });

export const Arte: React.FC<ArteProps> = (p) => {
  const vertical = p.altura > 1600;
  const topo = vertical ? SEGURA.topo - 40 : 64;
  const base = vertical ? SEGURA.base - 60 : 60;
  const destaque = cor(p.corDestaque, COR.destaque);
  const escuro = "rgba(6,14,28,";
  return (
    <AbsoluteFill style={{ backgroundColor: COR.primaria, fontFamily: FONTE }}>
      {p.foto ? (
        <Img src={staticFile(p.foto)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: `50% ${p.focoY ?? 50}%`, filter: "contrast(1.05) saturate(1.1)" }} />
      ) : null}
      <AbsoluteFill
        style={{
          background: `linear-gradient(to bottom, ${escuro}.8) 0%, ${escuro}.3) 30%, ${escuro}0) 46%, ${escuro}.25) 58%, ${escuro}.9) 100%)`,
        }}
      />
      <div style={{ position: "absolute", top: topo, left: 60, right: 60 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 20 }}>
          {p.etiqueta ? (
            <div style={{ backgroundColor: destaque, color: contraste(destaque), fontWeight: 700, fontSize: 30, letterSpacing: 1.5, padding: "10px 24px", borderRadius: 40 }}>{p.etiqueta}</div>
          ) : (
            <span />
          )}
          {p.etiquetaDireita ? <div style={{ border: "3px solid white", color: "white", fontWeight: 600, fontSize: 28, padding: "9px 22px", borderRadius: 40 }}>{p.etiquetaDireita}</div> : null}
        </div>
        <div style={{ color: "white", fontWeight: 700, fontSize: vertical ? 84 : 74, lineHeight: 1.05, marginTop: 26, textShadow: sombraTexto }}>
          {p.titulo}
          {p.titulo2 ? (
            <>
              <br />
              <span style={{ color: COR.clara, fontWeight: 600 }}>{p.titulo2}</span>
            </>
          ) : null}
        </div>
      </div>

      <div style={{ position: "absolute", left: 60, right: 60, bottom: base }}>
        {p.destaqueGrande ? (
          <>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 24 }}>
              <div style={{ color: destaque, fontWeight: 800, fontSize: 250, lineHeight: 0.85, textShadow: "0 8px 30px rgba(0,0,0,.45)" }}>{p.destaqueGrande.valor}</div>
              {p.destaqueGrande.sufixo ? <div style={{ color: "white", fontWeight: 700, fontSize: 92, lineHeight: 0.95, paddingBottom: 12, textShadow: sombraTexto }}>{p.destaqueGrande.sufixo}</div> : null}
            </div>
            {p.destaqueGrande.legenda ? <div style={{ color: "white", fontWeight: 500, fontSize: 40, marginTop: 18, textShadow: sombraTexto }}>{p.destaqueGrande.legenda}</div> : null}
          </>
        ) : null}
        {p.card ? (
          <div style={{ backgroundColor: "white", borderRadius: 28, padding: "28px 36px 26px", boxShadow: "0 18px 50px rgba(0,0,0,.35)", marginTop: 24 }}>
            {p.card.linha1 ? <div style={{ color: COR.primaria, fontWeight: 600, fontSize: 32 }}>{p.card.linha1}</div> : null}
            <div style={{ display: "flex", alignItems: "baseline", gap: 14, marginTop: 4, flexWrap: "wrap" }}>
              {p.card.prefixo ? <span style={{ color: COR.primaria, fontWeight: 500, fontSize: 36 }}>{p.card.prefixo}</span> : null}
              <span style={{ color: destaque, fontWeight: 800, fontSize: 96, lineHeight: 1.05 }}>{p.card.valor}</span>
            </div>
            {p.card.linha2 ? (
              <div style={{ color: COR.primaria, fontWeight: 600, fontSize: 34 }}>
                {p.card.linha2}
                {p.card.linha3 ? <span style={{ fontWeight: 400, fontSize: 28 }}> · {p.card.linha3}</span> : null}
              </div>
            ) : null}
          </div>
        ) : null}
        {p.chamada ? (
          <div style={{ marginTop: 26, backgroundColor: "white", color: COR.primaria, borderRadius: 24, padding: "22px 30px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ fontWeight: 700, fontSize: 38 }}>{p.chamada}</div>
            <div style={{ fontSize: 44 }}>👉</div>
          </div>
        ) : null}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 22, gap: 20 }}>
          <div style={{ color: "rgba(255,255,255,.85)", fontSize: 22, lineHeight: 1.35, maxWidth: 640, whiteSpace: "pre-line" }}>{p.rodape ?? ""}</div>
          {p.logo !== false && MARCA.logo ? <Img src={staticFile(MARCA.logo)} style={{ height: 70, maxWidth: 320, objectFit: "contain" }} /> : null}
        </div>
      </div>
    </AbsoluteFill>
  );
};
