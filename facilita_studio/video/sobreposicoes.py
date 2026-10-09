"""Títulos e CTA desenhados em PNG transparente 1080×1920, sempre dentro da zona segura.

A zona segura exclui o topo (cabeçalho do Reels), a base (legenda e botões) e a
lateral direita (curtir, comentar, compartilhar), conforme `video.zona_segura`.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..marca import Marca


def zona_segura(marca: Marca) -> tuple[int, int, int, int]:
    """(x0, y0, x1, y1) da área livre da interface do Instagram."""
    v, z = marca.video, marca.video["zona_segura"]
    return z["esquerda"], z["topo"], v["largura"] - z["direita"], v["altura"] - z["base"]


def _quebrar(texto: str, fonte: ImageFont.FreeTypeFont, largura: int) -> list[str]:
    linhas: list[str] = []
    for paragrafo in texto.split("\n"):
        atual = ""
        for palavra in paragrafo.split():
            teste = f"{atual} {palavra}".strip()
            if fonte.getlength(teste) <= largura or not atual:
                atual = teste
            else:
                linhas.append(atual)
                atual = palavra
        if atual:
            linhas.append(atual)
    return linhas


def _ajustar(texto: str, ttf: Path, largura: int, tamanho: int, max_linhas: int, minimo: int = 40):
    while True:
        fonte = ImageFont.truetype(str(ttf), tamanho)
        linhas = _quebrar(texto, fonte, largura)
        cabe = len(linhas) <= max_linhas and all(fonte.getlength(l) <= largura for l in linhas)
        if cabe or tamanho <= minimo:
            return fonte, linhas
        tamanho -= 4


def _rgba(marca: Marca, cor: str, alfa: int) -> tuple[int, int, int, int]:
    return (*marca.cor_rgb(cor), alfa)


def titulo_png(texto: str, destino: Path, marca: Marca, posicao: str = "topo") -> Path:
    """Faixa marinho translúcida com barra laranja, texto branco em Poppins Bold."""
    W, H = marca.video["largura"], marca.video["altura"]
    x0, y0, x1, y1 = zona_segura(marca)
    pad_x, pad_y, barra = 36, 28, 12
    fonte, linhas = _ajustar(texto, marca.fonte_ttf("negrito"), x1 - x0 - 2 * pad_x - barra, 72, 3)
    asc, desc = fonte.getmetrics()
    alt_linha = int((asc + desc) * 1.08)
    caixa_h = alt_linha * len(linhas) + 2 * pad_y
    caixa_w = int(max(fonte.getlength(l) for l in linhas)) + 2 * pad_x + barra
    if posicao == "centro":
        topo = (y0 + y1 - caixa_h) // 2
    elif posicao == "baixo":
        topo = y1 - caixa_h - 40
    else:
        topo = y0 + 40
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0, topo, x0 + caixa_w, topo + caixa_h), radius=22, fill=_rgba(marca, "marinho", 225))
    d.rectangle((x0, topo + 18, x0 + barra, topo + caixa_h - 18), fill=_rgba(marca, "laranja", 255))
    y = topo + pad_y
    for linha in linhas:
        d.text((x0 + barra + pad_x, y), linha, font=fonte, fill=(255, 255, 255, 255))
        y += alt_linha
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino)
    return destino


def cta_png(cta: str, destino: Path, marca: Marca, logo: Path | None, subtitulo: str = "") -> Path:
    """Cartão final: logo em cartão branco e botão laranja com o CTA, centrados na zona segura."""
    W, H = marca.video["largura"], marca.video["altura"]
    x0, y0, x1, y1 = zona_segura(marca)
    largura_util = x1 - x0
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # véu marinho para leitura sobre qualquer imagem
    d.rectangle((0, 0, W, H), fill=_rgba(marca, "marinho", 120))

    blocos_h = []
    logo_img = None
    if logo:
        with Image.open(logo) as li:
            logo_img = li.convert("RGBA")
        escala = min((largura_util - 200) / logo_img.width, 200 / logo_img.height)
        logo_img = logo_img.resize((int(logo_img.width * escala), int(logo_img.height * escala)), Image.LANCZOS)
        blocos_h.append(logo_img.height + 100)
    f_cta, l_cta = _ajustar(cta, marca.fonte_ttf("negrito"), largura_util - 140, 84, 2)
    asc, desc = f_cta.getmetrics()
    alt_cta = int((asc + desc) * 1.1)
    botao_h = alt_cta * len(l_cta) + 70
    blocos_h.append(botao_h)
    f_sub = l_sub = None
    if subtitulo:
        f_sub, l_sub = _ajustar(subtitulo, marca.fonte_ttf("regular"), largura_util - 60, 44, 3, 30)
        a2, d2 = f_sub.getmetrics()
        blocos_h.append(int((a2 + d2) * 1.15) * len(l_sub) + 20)
    total = sum(blocos_h) + 50 * (len(blocos_h) - 1)
    y = (y0 + y1 - total) // 2
    cx = (x0 + x1) // 2

    if logo_img is not None:
        card_w, card_h = logo_img.width + 120, logo_img.height + 100
        d.rounded_rectangle((cx - card_w // 2, y, cx + card_w // 2, y + card_h), radius=36, fill=(255, 255, 255, 245))
        img.alpha_composite(logo_img, (cx - logo_img.width // 2, y + 50))
        y += card_h + 50

    botao_w = int(max(f_cta.getlength(l) for l in l_cta)) + 140
    d.rounded_rectangle((cx - botao_w // 2, y, cx + botao_w // 2, y + botao_h), radius=botao_h // 2 if len(l_cta) == 1 else 48,
                        fill=_rgba(marca, "laranja", 255))
    ty = y + 35
    for linha in l_cta:
        d.text((cx, ty), linha, font=f_cta, fill=(255, 255, 255, 255), anchor="ma")
        ty += alt_cta
    y += botao_h + 50

    if f_sub and l_sub:
        a2, d2 = f_sub.getmetrics()
        for linha in l_sub:
            d.text((cx, y), linha, font=f_sub, fill=(255, 255, 255, 255), anchor="ma")
            y += int((a2 + d2) * 1.15)
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino)
    return destino


def dentro_da_zona_segura(png: Path, marca: Marca, ignorar_veu: bool = False) -> bool:
    """Confere que nenhum pixel opaco (além do véu) cai fora da zona segura."""
    x0, y0, x1, y1 = zona_segura(marca)
    with Image.open(png) as im:
        alfa = im.getchannel("A")
    limiar = 130 if ignorar_veu else 0
    bbox = alfa.point(lambda a: 255 if a > limiar else 0).getbbox()
    if bbox is None:
        return True
    return bbox[0] >= x0 and bbox[1] >= y0 and bbox[2] <= x1 and bbox[3] <= y1
