"""Renderização HTML/CSS em Chromium (Playwright) a 2×, reduzida para o tamanho final."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from PIL import Image

from ..marca import Marca
from ..util import ErroFacilita

PASTA_MODELOS = Path(__file__).parent / "modelos"
PESOS = {"regular": 400, "medio": 500, "seminegrito": 600, "negrito": 700}


def ambiente() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(PASTA_MODELOS)),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def fontes_css(marca: Marca) -> str:
    regras = []
    for peso, valor in PESOS.items():
        p = marca.caminho_fonte(peso)
        if p:
            regras.append(
                f"@font-face {{ font-family: 'Poppins'; font-weight: {valor}; src: url('{p.resolve().as_uri()}') format('truetype'); }}"
            )
    return "\n".join(regras)


class _ComDefault(dict):
    """Campos opcionais ausentes viram texto vazio no modelo."""

    def __getattr__(self, chave):
        return self.get(chave, "")


def html(modelo: str, contexto: dict) -> str:
    ctx = dict(contexto)
    ctx["c"] = _ComDefault(ctx.get("c") or {})
    ctx["o"] = _ComDefault(ctx["o"]) if ctx.get("o") else None
    for chave in ("fotos", "destaques", "numero", "aviso", "variante", "selo_uri", "selo_largura"):
        ctx.setdefault(chave, None)
    return ambiente().get_template(f"{modelo}.html").render(**ctx)


@contextmanager
def navegador():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:  # pragma: no cover
        raise ErroFacilita("Playwright não instalado: pip install playwright") from e
    with sync_playwright() as p:
        caminho = os.environ.get("CHROMIUM_PATH")
        # Execução local: sem tráfego de fundo do Chromium (atualizações, telemetria).
        args = ["--disable-background-networking", "--disable-component-update", "--disable-domain-reliability",
                "--disable-sync", "--no-first-run", "--no-default-browser-check", "--metrics-recording-only"]
        try:
            b = p.chromium.launch(executable_path=caminho, args=args) if caminho else p.chromium.launch(args=args)
        except Exception as e:  # noqa: BLE001
            raise ErroFacilita(
                "Não foi possível abrir o Chromium. Rode 'playwright install chromium' "
                "ou aponte CHROMIUM_PATH para um Chrome/Chromium instalado.\n" + str(e).splitlines()[0]
            ) from e
        try:
            yield b
        finally:
            b.close()


def renderizar(browser, conteudo_html: str, destino: Path, largura: int, altura: int, escala: int = 2,
               manter_2x: bool = False) -> dict:
    """Grava o HTML ao lado do PNG (para conferência) e captura a 2×."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    arquivo_html = destino.with_suffix(".html")
    arquivo_html.write_text(conteudo_html, encoding="utf-8")
    pagina = browser.new_page(viewport={"width": largura, "height": altura}, device_scale_factor=escala)
    externos: list[str] = []

    def _so_local(rota):
        url = rota.request.url
        if url.startswith(("file:", "data:", "about:")):
            rota.continue_()
        else:  # a peça só usa arquivos locais; nada sai para a internet
            externos.append(url)
            rota.abort()

    pagina.route("**/*", _so_local)
    try:
        pagina.goto(arquivo_html.resolve().as_uri(), wait_until="load")
        pagina.evaluate("document.fonts.ready.then(() => true)")
        imagens_ok = pagina.evaluate(
            "Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)"
        )
        poppins = pagina.evaluate("document.fonts.check(\"700 40px Poppins\") && "
                                  "Array.from(document.fonts).some(f => f.family.replace(/['\\\"]/g,'') === 'Poppins' && f.status === 'loaded')")
        bruto = destino.with_name(destino.stem + "@2x.png")
        pagina.screenshot(path=str(bruto), clip={"x": 0, "y": 0, "width": largura, "height": altura})
    finally:
        pagina.close()
    if manter_2x:
        bruto.replace(destino)
    else:
        with Image.open(bruto) as im:
            im.convert("RGB").resize((largura, altura), Image.LANCZOS).save(destino, optimize=True)
        bruto.unlink()
    return {"png": str(destino), "html": str(arquivo_html), "poppins_carregada": bool(poppins), "imagens_ok": bool(imagens_ok),
            "bloqueados": externos}
