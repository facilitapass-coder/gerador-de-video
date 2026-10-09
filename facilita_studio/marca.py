"""Marca como configuração: cores, fonte, logo e regras de texto aplicadas a toda peça."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .util import ErroFacilita, sem_acentos

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_MARCA_PADRAO = RAIZ_PROJETO / "marca"

# Fontes de sistema usadas só como substitutas quando a Poppins não está instalada.
FONTES_SUBSTITUTAS = {
    "regular": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/Library/Fonts/Arial.ttf", "C:/Windows/Fonts/arial.ttf"],
    "negrito": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/Library/Fonts/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"],
}

_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\U00002B50\U00002B55\U0000231A-\U0000231B]"
)


@dataclass
class Problema:
    nivel: str  # "erro" bloqueia a peça; "aviso" só informa
    mensagem: str
    onde: str = ""

    def __str__(self) -> str:
        prefixo = "ERRO" if self.nivel == "erro" else "aviso"
        return f"[{prefixo}] {self.onde + ': ' if self.onde else ''}{self.mensagem}"


@dataclass
class Marca:
    pasta: Path
    dados: dict
    avisos: list[str] = field(default_factory=list)

    # ---------- carregamento ----------
    @classmethod
    def carregar(cls, pasta: Path | str | None = None) -> "Marca":
        pasta = Path(pasta or os.environ.get("FACILITA_MARCA", PASTA_MARCA_PADRAO))
        arquivo = pasta / "marca.yaml"
        if not arquivo.exists():
            raise ErroFacilita(f"Configuração da marca não encontrada em {arquivo}.")
        return cls(pasta=pasta, dados=yaml.safe_load(arquivo.read_text(encoding="utf-8")))

    # ---------- atalhos ----------
    @property
    def cores(self) -> dict:
        return self.dados["cores"]

    @property
    def video(self) -> dict:
        return self.dados["video"]

    @property
    def imagens(self) -> dict:
        return self.dados["imagens"]

    def cor_rgb(self, nome: str) -> tuple[int, int, int]:
        h = self.cores[nome].lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]

    def caminho_fonte(self, peso: str = "negrito") -> Path | None:
        rel = self.dados["fonte"]["arquivos"].get(peso)
        p = self.pasta / rel if rel else None
        return p if p and p.exists() else None

    def fonte_ttf(self, peso: str = "negrito") -> Path:
        """Poppins quando instalada; senão uma fonte de sistema, registrando aviso."""
        p = self.caminho_fonte(peso)
        if p:
            return p
        base = "negrito" if peso in ("negrito", "seminegrito") else "regular"
        for candidata in FONTES_SUBSTITUTAS[base]:
            if Path(candidata).exists():
                msg = f"Poppins ({peso}) não encontrada em {self.pasta / 'fontes'}; usando {Path(candidata).name}."
                if msg not in self.avisos:
                    self.avisos.append(msg)
                return Path(candidata)
        raise ErroFacilita("Nenhuma fonte disponível. Coloque os arquivos da Poppins em marca/fontes/.")

    def fonte_completa(self) -> bool:
        return all(self.caminho_fonte(p) for p in self.dados["fonte"]["arquivos"])

    def caminho_logo(self) -> Path | None:
        """Prefere a versão com canal alfa corrigido, se já existir."""
        original = self.pasta / self.dados["logo"]["arquivo"]
        corrigido = self.pasta / "derivados" / (original.stem + "-alfa.png")
        if corrigido.exists():
            return corrigido
        return original if original.exists() else None

    def exigir_logo(self) -> Path:
        p = self.caminho_logo()
        if not p:
            raise ErroFacilita(
                f"Logo '{self.dados['logo']['nome']}' não encontrado em {self.pasta / self.dados['logo']['arquivo']}. "
                "Copie o PNG do Drive (ID - Facilita Pass Lazer) para essa pasta."
            )
        return p

    def verificar_ativos(self, permitir_fonte_substituta: bool = False) -> list[Problema]:
        problemas = []
        if not self.fonte_completa():
            faltando = [p for p in self.dados["fonte"]["arquivos"] if not self.caminho_fonte(p)]
            problemas.append(
                Problema(
                    "aviso" if permitir_fonte_substituta else "erro",
                    f"Arquivos da Poppins ausentes ({', '.join(faltando)}) em {self.pasta / 'fontes'}.",
                    "marca",
                )
            )
        if not self.caminho_logo():
            problemas.append(Problema("erro", f"Logo ausente: {self.pasta / self.dados['logo']['arquivo']}", "marca"))
        return problemas

    # ---------- regras de texto ----------
    def verificar_texto(self, texto: str, onde: str = "") -> list[Problema]:
        """Terminologia, frases proibidas e excesso de emoji."""
        if not texto:
            return []
        problemas: list[Problema] = []
        normal = sem_acentos(texto).lower()
        for regra in self.dados.get("terminologia", []):
            errado = sem_acentos(regra["errado"]).lower()
            if re.search(rf"\b{re.escape(errado)}\b", normal):
                problemas.append(Problema("erro", f"Use \"{regra['certo']}\", não \"{regra['errado']}\".", onde))
        for frase in self.dados.get("frases_proibidas", []):
            if sem_acentos(frase).lower() in normal:
                problemas.append(Problema("erro", f"Frase proibida pela marca: \"{frase}\".", onde))
        n_emojis = len(_EMOJI.findall(texto))
        limite = self.dados.get("tom", {}).get("max_emojis", 2)
        if n_emojis > limite:
            problemas.append(Problema("erro", f"{n_emojis} emojis (máximo {limite}): o tom da marca é sóbrio.", onde))
        return problemas

    # ---------- licenciamento ----------
    def verificar_origem(self, origem: str | None, arquivo: str, tipo: str = "foto") -> list[Problema]:
        lista = self.dados["fontes_musica_licenciadas"] if tipo == "musica" else self.dados["fontes_licenciadas"]
        if not origem or not str(origem).strip():
            return [Problema("erro", f"{tipo} sem origem informada; só entram arquivos de fonte licenciada.", arquivo)]
        aceitas = {sem_acentos(o).lower() for o in lista}
        if sem_acentos(str(origem)).lower().strip() not in aceitas:
            return [
                Problema(
                    "erro",
                    f"origem \"{origem}\" não está na lista de fontes licenciadas ({'; '.join(lista)}).",
                    arquivo,
                )
            ]
        return []


def erros(problemas: list[Problema]) -> list[Problema]:
    return [p for p in problemas if p.nivel == "erro"]


def exigir_sem_erros(problemas: list[Problema], contexto: str) -> None:
    e = erros(problemas)
    if e:
        raise ErroFacilita(f"{contexto} recusado(a):\n" + "\n".join(f"  {p}" for p in e))
