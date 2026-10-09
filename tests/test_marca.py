from facilita_studio.marca import erros


def test_terminologia_e_frases_proibidas(marca):
    problemas = marca.verificar_texto("Fale com nosso embaixador, condições exclusivas que agência comum não consegue!")
    textos = " ".join(p.mensagem for p in erros(problemas))
    assert "Xpert Xcaret" in textos
    assert "Frase proibida" in textos


def test_nivel_vira_faixa_mesmo_sem_acento(marca):
    assert erros(marca.verificar_texto("Nivel 2 do programa"))
    assert not marca.verificar_texto("Faixa 2 do programa")


def test_excesso_de_emoji(marca):
    assert erros(marca.verificar_texto("Partiu 🌴🌊☀️✈️"))
    assert not marca.verificar_texto("Partiu México ✈️")


def test_origem_obrigatoria(marca):
    assert erros(marca.verificar_origem(None, "x.jpg"))
    assert erros(marca.verificar_origem("Google Imagens", "x.jpg"))
    assert not marca.verificar_origem("drive oficial xcaret", "x.jpg")
    assert erros(marca.verificar_origem("Drive oficial Xcaret", "m.mp3", "musica"))


def test_ativos_exigem_poppins(marca):
    assert erros(marca.verificar_ativos())
    assert not erros(marca.verificar_ativos(permitir_fonte_substituta=True))
