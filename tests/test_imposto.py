from decimal import Decimal

import pytest

from src.calculadora.imposto import calcular_imposto, comparar_deducoes_mensais


def test_calcula_imposto_na_faixa_isenta():
	resultado = calcular_imposto("2.000,00", 2025)
	assert resultado["base_calculo"] == Decimal("2000.00")
	assert resultado["imposto"] == Decimal("0.00")


def test_calcula_imposto_em_faixa_superior():
	resultado = calcular_imposto("5.000,00", 2025)
	assert resultado["aliquota"] == Decimal("0.275")
	assert resultado["imposto"] == Decimal("466.27")


def test_usa_ano_escolhido_sem_fallback():
	with pytest.raises(ValueError, match="Não há tabela para 2024-12"):
		calcular_imposto("5.000,00", 2024)


def test_desconto_simplificado_reduz_base():
	resultado = calcular_imposto("4.000,00", 2025, desconto_simplificado=True)
	assert resultado["deducoes"] == Decimal("607.20")
	assert resultado["base_calculo"] == Decimal("3392.80")


def test_tabela_mudou_em_maio_de_2025():
	janeiro = calcular_imposto("2.300,00", 2025, mes=1)
	maio = calcular_imposto("2.300,00", 2025, mes=5)
	assert janeiro["imposto"] == Decimal("3.06")
	assert maio["imposto"] == Decimal("0.00")


def test_reducao_de_2026_ate_5000_zera_imposto():
	resultado = calcular_imposto("4.000,00", 2026, desconto_simplificado=True)
	assert resultado["imposto"] == Decimal("0.00")
	assert resultado["reducao"] == Decimal("114.76")


def test_reducao_de_2026_na_faixa_decrescente():
	resultado = calcular_imposto(
		"6.000,00",
		2026,
		outras_deducoes="649,60",
	)
	assert resultado["reducao"] == Decimal("179.75")
	assert resultado["imposto"] == Decimal("382.88")


def test_compara_deducoes_mensais_e_seleciona_menor_imposto():
	resultado = comparar_deducoes_mensais("5.000,00", 2025, mes=12)

	assert resultado["mais_vantajosa"] == "desconto_simplificado"
	assert resultado["cenarios"]["deducoes_legais"]["imposto"] == Decimal("466.27")
	assert resultado["cenarios"]["desconto_simplificado"]["imposto"] == Decimal("312.89")
	assert resultado["diferenca_entre_modalidades"] == Decimal("153.38")
	assert resultado["resultado"] == resultado["cenarios"]["desconto_simplificado"]
