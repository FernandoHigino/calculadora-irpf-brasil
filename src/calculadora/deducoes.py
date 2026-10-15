from decimal import Decimal, ROUND_HALF_UP


CENTAVO = Decimal("0.01")


def calcular_deducoes(
	renda_bruta,
	dependentes,
	tabela,
	outras_deducoes=0,
	desconto_simplificado=False,
):
	"""Calcula deduções legais informadas ou usa o simplificado em substituição."""
	if desconto_simplificado:
		deducao = Decimal(str(tabela["desconto_simplificado_maximo"]))
	else:
		deducao = (
			Decimal(str(tabela["deducao_dependente"])) * dependentes
			+ Decimal(str(outras_deducoes))
		)
	return deducao.quantize(CENTAVO, rounding=ROUND_HALF_UP)
