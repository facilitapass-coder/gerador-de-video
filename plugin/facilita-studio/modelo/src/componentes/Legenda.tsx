import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COR, FONTE, MARCA } from "../marca";
import { fr, sombraTexto } from "./basicos";

export type Palavra = { w: string; i: number; f: number };

const limpa = (w: string) => w.toLowerCase().replace(/[.,!?;:"]+$/g, "");

// Agrupa as palavras em blocos curtos: até N palavras, quebra em pontuação, pausa ou troca de cena
export const agrupar = (palavras: Palavra[], maxPalavras: number, cortes: number[]) => {
  const g: Palavra[][] = [];
  let atual: Palavra[] = [];
  palavras.forEach((p, idx) => {
    const prox = palavras[idx + 1];
    atual.push(p);
    const fimFrase = /[.,!?]$/.test(p.w);
    const pausa = prox ? prox.i - p.f > 0.45 : true;
    const cruza = prox ? cortes.some((c) => p.i < c && prox.i >= c) : true;
    if (atual.length >= maxPalavras || fimFrase || pausa || cruza) {
      g.push(atual);
      atual = [];
    }
  });
  if (atual.length) g.push(atual);
  return g;
};

export const Legenda: React.FC<{ grupos: Palavra[][]; topo: number; extras?: string[]; tamanho?: number }> = ({ grupos, topo, extras = [], tamanho = 64 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const chave = new Set([...MARCA.palavras_destaque, ...extras].map(limpa));
  const idx = grupos.findIndex((g, i) => {
    const fimNatural = g[g.length - 1].f + 0.6;
    const fim = grupos[i + 1] ? Math.min(grupos[i + 1][0].i, fimNatural) : fimNatural;
    return t >= g[0].i - 0.05 && t < fim;
  });
  if (idx < 0) return null;
  const g = grupos[idx];
  const entrada = spring({ frame: frame - fr(g[0].i - 0.05), fps, config: { damping: 14, stiffness: 220 } });
  return (
    <div
      style={{
        position: "absolute",
        top: topo,
        left: 70,
        right: 70,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        columnGap: 20,
        rowGap: 4,
        transform: `translateY(${(1 - entrada) * 26}px) scale(${0.92 + entrada * 0.08})`,
        opacity: entrada,
      }}
    >
      {g.map((p, k) => {
        const ativa = t >= p.i - 0.03;
        const destaque = chave.has(limpa(p.w));
        const pp = spring({ frame: frame - fr(p.i), fps, config: { damping: 10, stiffness: 260 } });
        return (
          <span
            key={k}
            style={{
              fontFamily: FONTE,
              fontWeight: 800,
              fontSize: destaque ? tamanho * 1.12 : tamanho,
              textTransform: "uppercase",
              lineHeight: 1.12,
              color: destaque ? COR.legenda_destaque : "white",
              opacity: ativa ? 1 : 0.55,
              transform: `scale(${ativa ? 1 + (1 - pp) * 0.18 : 1})`,
              display: "inline-block",
              WebkitTextStroke: "2px rgba(0,0,0,.55)",
              textShadow: sombraTexto,
            }}
          >
            {p.w.replace(/,$/, "")}
          </span>
        );
      })}
    </div>
  );
};
