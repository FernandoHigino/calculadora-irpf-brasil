from decimal import Decimal

from src.calculadora.deducoes import calcular_deducoes
from src.calculadora.faixas import obter_tabela


def test_deduz_valor_por_dependente():
	deducao = calcular_deducoes(Decimal("5000"), 2, obter_tabela(2025))
	assert deducao == Decimal("379.18")


def test_soma_outras_deducoes_legais():
	deducao = calcular_deducoes(
		Decimal("5000"), 1, obter_tabela(2025), outras_deducoes=Decimal("500")
	)
	assert deducao == Decimal("689.59")


def test_desconto_simplificado_respeita_teto():
	deducao = calcular_deducoes(
		Decimal("5000"), 0, obter_tabela(2025), desconto_simplificado=True
	)
	assert deducao == Decimal("607.20")
