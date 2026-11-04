import React from "react";
import { Composition } from "remotion";
import { Arte, ArteProps, metadadosArte } from "./composicoes/Arte";
import { metadadosReel, Reel, ReelProps } from "./composicoes/Reel";

// Duas composições genéricas. Cada peça é um arquivo de props (JSON) em projetos/<peça>/.
//   npx remotion render Reel projetos/x/saida/x.mp4 --props=projetos/x/reel.json
//   npx remotion still  Arte projetos/x/saida/x.png --props=projetos/x/arte.json
// As props padrão são mínimas de propósito: o Remotion mistura as padrão com as da peça,
// então qualquer campo extra aqui apareceria em todas as peças.
const reelPadrao: ReelProps = {
  duracao: 4,
  cenas: [{ tipo: "final", de: 0, ate: 4, linhas: [{ texto: "FACILITA" }, { texto: "STUDIO", cor: "legenda" }] }],
};
const artePadrao: ArteProps = { largura: 1080, altura: 1350, titulo: "Seu título aqui" };

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Reel" component={Reel} fps={30} width={1080} height={1920} durationInFrames={120} defaultProps={reelPadrao} calculateMetadata={metadadosReel} />
    <Composition id="Arte" component={Arte} fps={30} width={1080} height={1350} durationInFrames={1} defaultProps={artePadrao} calculateMetadata={metadadosArte} />
  </>
);
