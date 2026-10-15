from decimal import Decimal, ROUND_HALF_UP


def formatar_reais(valor):
	centavos = Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
	texto = f"{centavos:,.2f}"
	return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")
