import { Composition } from "remotion";
import { Ad01 } from "./Ad01";
import { Ad02 } from "./Ad02";
import { Ad04 } from "./Ad04";
import { AllFunInclusive } from "./AllFunInclusive";
import { BlackFacilita } from "./BlackFacilita";
import { metadadosReelFala, ReelFala } from "./ReelFala";
import { Reels02 } from "./Reels02";
import { Reels03 } from "./Reels03";
import { Reels09 } from "./Reels09";
import { metadadosOrlando, OrlandoEstatico } from "./OrlandoEstatico";
import { PromoDisney } from "./PromoDisney";
import { DURACAO_VENTO, VentoMaringa } from "./VentoMaringa";
import { DURACAO_GRAMADO, GramadoOferta } from "./GramadoOferta";
import { metadadosStory, Story } from "./Story";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="AllFunInclusive"
        component={AllFunInclusive}
        durationInFrames={602}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Reels09"
        component={Reels09}
        durationInFrames={1046}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Reels03"
        component={Reels03}
        durationInFrames={1096}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Story"
        component={Story}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={metadadosStory}
        defaultProps={{ id: "seg-1", etiqueta: "", titulo: "", total: 300, linha: [], grupos: [] }}
      />
      <Composition
        id="ReelFala"
        component={ReelFala}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={metadadosReelFala}
        defaultProps={{ id: "r22", gancho: "", etiqueta: "", final1: "", final2: "", final3: "", total: 300, linha: [], grupos: [] }}
      />
      <Composition
        id="Reels02"
        component={Reels02}
        durationInFrames={1599}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Ad01"
        component={Ad01}
        durationInFrames={861}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{ comMusica: true }}
      />
      <Composition
        id="OrlandoEstatico"
        component={OrlandoEstatico}
        durationInFrames={1}
        fps={30}
        width={1080}
        height={1350}
        calculateMetadata={metadadosOrlando}
        defaultProps={{ foto: "IMG_8170.jpg", linha1: "Orlando a dois.", linha2: "Agora com data.", focoY: 30, largura: 1080, altura: 1350 }}
      />
      <Composition
        id="PromoDisney"
        component={PromoDisney}
        durationInFrames={1}
        fps={30}
        width={1080}
        height={1350}
        defaultProps={{ foto: "IMG_8170.jpg", data: "20/10", focoY: 25 }}
      />
      <Composition id="BlackFacilita" component={BlackFacilita} durationInFrames={906} fps={30} width={1080} height={1920} defaultProps={{ comMusica: true }} />
      <Composition id="GramadoOferta" component={GramadoOferta} durationInFrames={DURACAO_GRAMADO} fps={30} width={1080} height={1920} />
      <Composition id="VentoMaringa" component={VentoMaringa} durationInFrames={DURACAO_VENTO} fps={30} width={1080} height={1920} />
      <Composition id="Ad02" component={Ad02} durationInFrames={771} fps={30} width={1080} height={1920} defaultProps={{ comMusica: true }} />
      <Composition id="Ad04" component={Ad04} durationInFrames={771} fps={30} width={1080} height={1920} defaultProps={{ comMusica: true }} />
    </>
  );
};
