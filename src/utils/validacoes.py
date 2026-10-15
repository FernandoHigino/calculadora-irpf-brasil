from decimal import Decimal, InvalidOperation


def validar_valor_monetario(valor, nome="valor"):
	"""Converte valor em Decimal, aceitando números e formato brasileiro."""
	if isinstance(valor, bool):
		raise ValueError(f"{nome.capitalize()} deve ser um número não negativo.")
	try:
		if isinstance(valor, str):
			texto = valor.strip().replace("R$", "").replace(" ", "")
			if "," in texto:
				texto = texto.replace(".", "").replace(",", ".")
			numero = Decimal(texto)
		else:
			numero = Decimal(str(valor))
	except (InvalidOperation, ValueError):
		raise ValueError(f"{nome.capitalize()} inválido.") from None

	if not numero.is_finite() or numero < 0:
		raise ValueError(f"{nome.capitalize()} deve ser um número não negativo.")
	return numero


def validar_dependentes(dependentes):
	if isinstance(dependentes, bool) or not isinstance(dependentes, int) or dependentes < 0:
		raise ValueError("A quantidade de dependentes deve ser um inteiro não negativo.")
	return dependentes
