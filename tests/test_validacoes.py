from decimal import Decimal

import pytest

from src.utils.validacoes import validar_dependentes, validar_valor_monetario


def test_aceita_valor_em_formato_brasileiro():
	assert validar_valor_monetario("1.234,56") == Decimal("1234.56")


@pytest.mark.parametrize("valor", ["abc", "-10", float("inf"), True])
def test_rejeita_valor_invalido(valor):
	with pytest.raises(ValueError):
		validar_valor_monetario(valor)


@pytest.mark.parametrize("quantidade", [-1, 1.5, True])
def test_rejeita_dependentes_invalidos(quantidade):
	with pytest.raises(ValueError):
		validar_dependentes(quantidade)
