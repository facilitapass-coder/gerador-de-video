import React from "react";
import { AbsoluteFill, Easing, spring, useCurrentFrame } from "remotion";
import { COR, FONTE } from "../marca";

export const FPS = 30;
export const fr = (s: number) => Math.round(s * FPS);
export const ease = Easing.bezier(0.45, 0, 0.2, 1);
export const sombraTexto = "0 4px 18px rgba(0,0,0,.65), 0 2px 4px rgba(0,0,0,.8)";

export type NomeCor = "destaque" | "alerta" | "primaria" | "clara" | "branco" | "legenda";
export const cor = (n?: NomeCor | string, padrao = COR.destaque): string => {
  switch (n) {
    case undefined:
      return padrao;
    case "destaque":
      return COR.destaque;
    case "alerta":
      return COR.alerta;
    case "primaria":
      return COR.primaria;
    case "clara":
      return COR.clara;
    case "branco":
      return "#FFFFFF";
    case "legenda":
      return COR.legenda_destaque;
    default:
      return n; // cor hexadecimal direta
  }
};

// Texto escuro ou claro conforme o fundo
export const contraste = (hex: string) => {
  const h = hex.replace("#", "");
  if (h.length < 6) return "#FFFFFF";
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  return 0.299 * r + 0.587 * g + 0.114 * b > 160 ? "#111111" : "#FFFFFF";
};

export const pop = (frame: number, inicio: number, fps: number) =>
  spring({ frame: frame - inicio, fps, config: { damping: 11, stiffness: 160, mass: 0.7 } });

export const Pilula: React.FC<{ children: React.ReactNode; fundo?: string; style?: React.CSSProperties }> = ({ children, fundo = COR.legenda_destaque, style }) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 12,
      backgroundColor: fundo,
      color: contraste(fundo),
      fontFamily: FONTE,
      fontWeight: 800,
      borderRadius: 999,
      padding: "12px 28px",
      boxShadow: "0 10px 30px rgba(0,0,0,.35)",
      ...style,
    }}
  >
    {children}
  </div>
);

// Linhas de movimento (vento, velocidade) atravessando a tela
export const LinhasMovimento: React.FC<{ opacidade: number; semente?: number }> = ({ opacidade, semente = 1 }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ opacity: opacidade, pointerEvents: "none" }}>
      <svg width={1080} height={1920}>
        {Array.from({ length: 22 }).map((_, i) => {
          const y = (i * 97 + semente * 31) % 1920;
          const vel = 9 + ((i * 7) % 8);
          const len = 160 + ((i * 53) % 220);
          const x = ((frame * vel + i * 211) % (1080 + len * 2)) - len;
          return (
            <line key={i} x1={x} y1={y} x2={x + len} y2={y - len * 0.18} stroke="white" strokeOpacity={0.12 + ((i * 13) % 10) / 60} strokeWidth={2 + (i % 3)} strokeLinecap="round" />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

// Vídeo preenchendo uma área (equivalente a object-fit: cover, calculado à mão)
export const cobrir = (largura: number | undefined, altura: number | undefined, areaW = 1080, areaH = 1920): React.CSSProperties => {
  const w = largura ?? areaW;
  const h = altura ?? areaH;
  const escala = Math.max(areaW / w, areaH / h);
  const vw = Math.round(w * escala);
  const vh = Math.round(h * escala);
  return { position: "absolute", width: vw, height: vh, left: (areaW - vw) / 2, top: (areaH - vh) / 2 };
};
