import { loadFont as fonteArquivo } from "@remotion/fonts";
import { loadFont as bebas } from "@remotion/google-fonts/BebasNeue";
import { loadFont as inter } from "@remotion/google-fonts/Inter";
import { loadFont as lato } from "@remotion/google-fonts/Lato";
import { loadFont as montserrat } from "@remotion/google-fonts/Montserrat";
import { loadFont as openSans } from "@remotion/google-fonts/OpenSans";
import { loadFont as oswald } from "@remotion/google-fonts/Oswald";
import { loadFont as playfair } from "@remotion/google-fonts/PlayfairDisplay";
import { loadFont as poppins } from "@remotion/google-fonts/Poppins";
import { loadFont as raleway } from "@remotion/google-fonts/Raleway";
import { loadFont as roboto } from "@remotion/google-fonts/Roboto";
import { staticFile } from "remotion";
import dados from "../marca.json";

// Kit de marca do cliente: tudo o que é cor, fonte, logo e regra sai de marca.json.
export type Marca = {
  nome: string;
  nicho: string;
  instagram: string;
  whatsapp: string;
  site: string;
  cores: { primaria: string; destaque: string; clara: string; alerta: string; legenda_destaque: string };
  fonte: { familia: string; arquivos: Record<string, string> };
  logo: string | null;
  tom: string;
  palavras_destaque: string[];
  dicionario: string[];
  frases_proibidas: string[];
  regras: string[];
  cta_padrao: string;
};
export const MARCA = dados as Marca;
export const COR = MARCA.cores;

// Zona livre da interface do Instagram em 1080×1920 (topo, base, laterais)
export const SEGURA = { topo: 250, base: 420, esquerda: 60, direita: 160 };

const GOOGLE: Record<string, (estilo: "normal", o: { weights: string[]; subsets: string[] }) => { fontFamily: string }> = {
  Poppins: poppins as never,
  Montserrat: montserrat as never,
  Inter: inter as never,
  Roboto: roboto as never,
  "Open Sans": openSans as never,
  Lato: lato as never,
  Raleway: raleway as never,
  "Bebas Neue": bebas as never,
  Oswald: oswald as never,
  "Playfair Display": playfair as never,
};

const carregarFonte = (): string => {
  const { familia, arquivos } = MARCA.fonte;
  const pesos = Object.entries(arquivos ?? {});
  if (pesos.length > 0) {
    // Fonte própria: arquivos em public/fontes, chave = peso ("400", "700"...)
    pesos.forEach(([weight, arquivo]) => {
      fonteArquivo({ family: familia, url: staticFile(arquivo), weight }).catch(() => undefined);
    });
    return familia;
  }
  const google = GOOGLE[familia] ?? GOOGLE.Poppins;
  const PESOS: Record<string, string[]> = { "Bebas Neue": ["400"], Lato: ["400", "700", "900"], Oswald: ["400", "500", "600", "700"] };
  const pesosGoogle = PESOS[familia] ?? ["400", "500", "600", "700", "800"];
  return google("normal", { weights: pesosGoogle, subsets: ["latin", "latin-ext"] }).fontFamily;
};

export const FONTE = carregarFonte();
export const FONTES_GOOGLE = Object.keys(GOOGLE);
