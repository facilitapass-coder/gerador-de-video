import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// Identidade Facilita Pass (marca/marca.yaml)
export const MARINHO = "#0D2D5E";
export const LARANJA = "#E8572A";
export const BEGE = "#F4ECE0";
export const FONTE = "Poppins";

// Zona livre da interface do Instagram em 1080×1920 (marca.yaml > video.zona_segura)
export const SEGURA = { topo: 250, base: 420, esquerda: 60, direita: 160 };

await Promise.all(
  (
    [
      ["Regular", "400"],
      ["Medium", "500"],
      ["SemiBold", "600"],
      ["Bold", "700"],
    ] as const
  ).map(([nome, weight]) =>
    loadFont({
      family: FONTE,
      url: staticFile(`fontes/Poppins-${nome}.ttf`),
      weight,
    }),
  ),
);
