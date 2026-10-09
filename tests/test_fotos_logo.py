import hashlib

import pytest
from PIL import Image

from facilita_studio.imagens.fotos import corrigir_alfa_logo, verificar_fotos
from facilita_studio.marca import erros
from facilita_studio.util import ErroFacilita


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_logo_alfa_corrigido_sem_tocar_original(tmp_path, marca):
    origem = marca.pasta / "logo" / "laranja-principal.png"
    antes = _sha(origem)
    r = corrigir_alfa_logo(origem, tmp_path / "logo-alfa.png")
    assert _sha(origem) == antes
    assert r["pixels_removidos"] > 0
    with Image.open(r["destino"]) as im:
        assert im.mode == "RGBA"
        assert im.getpixel((0, 0))[:3] == (232, 87, 42)  # recortado na área útil


def test_logo_nao_sobrescreve_original(marca):
    origem = marca.pasta / "logo" / "laranja-principal.png"
    with pytest.raises(ErroFacilita):
        corrigir_alfa_logo(origem, origem)


def test_fotos_exigem_origem(tmp_path, marca):
    foto = tmp_path / "f.jpg"
    Image.new("RGB", (10, 10)).save(foto)
    _, p = verificar_fotos([{"arquivo": "f.jpg"}], tmp_path, marca)
    assert erros(p)
    _, p = verificar_fotos([{"arquivo": "f.jpg", "origem": "IA"}], tmp_path, marca)
    assert erros(p) and "IA" in p[0].mensagem
    _, p = verificar_fotos([{"arquivo": "f.jpg", "origem": "Canva Pro"}], tmp_path, marca)
    assert not p
