import pytest

from facilita_studio.imagens.gerador import carregar
from facilita_studio.projeto import criar
from facilita_studio.util import ErroFacilita
from facilita_studio.video import roteiro


def test_novo_projeto(tmp_path):
    pasta = criar("Xcaret Arte", tmp_path / "projetos")
    assert pasta.name == "xcaret-arte"
    for sub in ("clips", "audio", "fotos", "saida"):
        assert (pasta / sub).is_dir()
    rot = roteiro.ler(pasta / "roteiro.md")
    assert rot.titulo == "Xcaret Arte" and rot.cta == "Comente ARTE" and len(rot.blocos) == 3
    assert carregar(pasta / "post.yaml")["modelo"] == "oferta"
    with pytest.raises(ErroFacilita, match="já existe"):
        criar("Xcaret Arte", tmp_path / "projetos")
