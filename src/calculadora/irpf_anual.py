"""Cálculo anual estimado do IRPF com comparação das deduções."""

from decimal import Decimal, ROUND_HALF_UP

from src.calculadora.faixas import obter_tabela_anual
from src.utils.validacoes import validar_dependentes, validar_valor_monetario


CENTAVO = Decimal("0.01")
ZERO = Decimal("0.00")
MODALIDADES = ("deducoes_legais", "desconto_simplificado", "mais_vantajosa")


def calcular_irpf_anual(
	rendimentos_tributaveis,
	ano_calendario,
	*,
	rendimentos_isentos=0,
	dependentes=0,
	despesas_medicas=0,
	despesas_educacionais=None,
	outras_deducoes=0,
	irrf_retido=0,
	modalidade="mais_vantajosa",
):
	"""Estima o ajuste anual e compara deduções legais com desconto simplificado.

	Cada item de ``despesas_educacionais`` representa um beneficiário elegível;
	o limite legal é aplicado separadamente a cada item.
	"""
	if modalidade not in MODALIDADES:
		raise ValueError(f"Modalidade deve ser uma destas: {', '.join(MODALIDADES)}.")

	tabela = obter_tabela_anual(ano_calendario)
	renda = _dinheiro(rendimentos_tributaveis, "rendimentos tributáveis")
	isentos = _dinheiro(rendimentos_isentos, "rendimentos isentos")
	retido = _dinheiro(irrf_retido, "imposto retido")
	medicas = _dinheiro(despesas_medicas, "despesas médicas")
	outras = _dinheiro(outras_deducoes, "outras deduções")
	quantidade_dependentes = validar_dependentes(dependentes)
	educacao_informada, educacao_dedutivel = _despesas_educacionais(
		despesas_educacionais,
		Decimal(str(tabela["limite_educacao_por_beneficiario"])),
	)

	deducao_dependentes = (
		Decimal(str(tabela["deducao_dependente"])) * quantidade_dependentes
	).quantize(CENTAVO, rounding=ROUND_HALF_UP)
	deducoes_legais = (
		deducao_dependentes + medicas + educacao_dedutivel + outras
	).quantize(CENTAVO, rounding=ROUND_HALF_UP)
	desconto_simplificado = min(
		renda * Decimal(str(tabela["desconto_simplificado_percentual"])),
		Decimal(str(tabela["desconto_simplificado_maximo"])),
	).quantize(CENTAVO, rounding=ROUND_HALF_UP)

	cenario_legal = _calcular_cenario(renda, deducoes_legais, tabela)
	cenario_simplificado = _calcular_cenario(renda, desconto_simplificado, tabela)
	mais_vantajosa = (
		"deducoes_legais"
		if cenario_legal["imposto_devido"] <= cenario_simplificado["imposto_devido"]
		else "desconto_simplificado"
	)
	modalidade_aplicada = mais_vantajosa if modalidade == "mais_vantajosa" else modalidade
	selecionado = (
		cenario_legal if modalidade_aplicada == "deducoes_legais" else cenario_simplificado
	)
	diferenca = abs(
		cenario_legal["imposto_devido"] - cenario_simplificado["imposto_devido"]
	).quantize(CENTAVO, rounding=ROUND_HALF_UP)
	imposto_a_pagar = max(ZERO, selecionado["imposto_devido"] - retido)
	restituicao = max(ZERO, retido - selecionado["imposto_devido"])

	return {
		"ano_calendario": ano_calendario,
		"exercicio": tabela["exercicio"],
		"versao_regras": tabela["versao_regras"],
		"fonte": tabela["fonte"],
		"rendimentos_tributaveis": renda,
		"rendimentos_isentos": isentos,
		"irrf_retido": retido,
		"modalidade_aplicada": modalidade_aplicada,
		"mais_vantajosa": mais_vantajosa,
		"diferenca_entre_modalidades": diferenca,
		"cenarios": {
			"deducoes_legais": {
				**cenario_legal,
				"deducoes_detalhadas": {
					"dependentes": deducao_dependentes,
					"despesas_medicas": medicas,
					"despesas_educacionais_informadas": educacao_informada,
					"despesas_educacionais_dedutiveis": educacao_dedutivel,
					"outras_deducoes": outras,
				},
			},
			"desconto_simplificado": {
				**cenario_simplificado,
				"deducoes_detalhadas": {"desconto_simplificado": desconto_simplificado},
			},
		},
		"deducoes": selecionado["deducoes"],
		"base_calculo": selecionado["base_calculo"],
		"faixa_numero": selecionado["faixa_numero"],
		"aliquota": selecionado["aliquota"],
		"parcela_deduzir": selecionado["parcela_deduzir"],
		"imposto_tabela": selecionado["imposto_tabela"],
		"reducao": selecionado["reducao"],
		"imposto_devido": selecionado["imposto_devido"],
		"imposto_a_pagar": imposto_a_pagar,
		"restituicao_estimada": restituicao,
	}


def _calcular_cenario(renda, deducoes, tabela):
	base = max(ZERO, renda - deducoes).quantize(CENTAVO, rounding=ROUND_HALF_UP)
	for indice, faixa in enumerate(tabela["faixas"], start=1):
		limite = faixa["limite_superior"]
		if limite is None or base <= Decimal(str(limite)):
			aliquota = Decimal(str(faixa["aliquota"]))
			parcela = Decimal(str(faixa["deducao"]))
			imposto_tabela = max(ZERO, base * aliquota - parcela).quantize(
				CENTAVO, rounding=ROUND_HALF_UP
			)
			reducao = _calcular_reducao_anual(renda, imposto_tabela, tabela)
			imposto_devido = max(ZERO, imposto_tabela - reducao).quantize(
				CENTAVO, rounding=ROUND_HALF_UP
			)
			return {
				"deducoes": deducoes.quantize(CENTAVO, rounding=ROUND_HALF_UP),
				"base_calculo": base,
				"faixa_numero": indice,
				"limite_superior_faixa": None if limite is None else Decimal(str(limite)),
				"aliquota": aliquota,
				"parcela_deduzir": parcela,
				"imposto_tabela": imposto_tabela,
				"reducao": reducao,
				"imposto_devido": imposto_devido,
			}
	raise ValueError("A tabela anual não contém uma faixa aplicável.")


def _calcular_reducao_anual(renda, imposto_tabela, tabela):
	regra = tabela.get("reducao_anual")
	if regra is None:
		return ZERO

	limite_isencao = Decimal(str(regra["limite_isencao"]))
	limite_final = Decimal(str(regra["limite_final"]))
	if renda >= limite_final:
		return ZERO
	if renda <= limite_isencao:
		valor = Decimal(str(regra["valor_maximo"]))
	else:
		valor = Decimal(str(regra["termo_constante"])) - (
			Decimal(str(regra["coeficiente"])) * renda
		)

	return min(max(ZERO, valor), imposto_tabela).quantize(
		CENTAVO, rounding=ROUND_HALF_UP
	)


def _despesas_educacionais(valores, limite_por_beneficiario):
	if valores is None:
		return ZERO, ZERO
	if isinstance(valores, (str, int, float, Decimal)):
		valores = [valores]
	try:
		valores = list(valores)
	except TypeError:
		raise ValueError("Despesas educacionais devem ser valores por beneficiário.") from None

	informado = ZERO
	dedutivel = ZERO
	for indice, valor in enumerate(valores, start=1):
		valor_validado = _dinheiro(valor, f"despesas educacionais do beneficiário {indice}")
		informado += valor_validado
		dedutivel += min(valor_validado, limite_por_beneficiario)
	return (
		informado.quantize(CENTAVO, rounding=ROUND_HALF_UP),
		dedutivel.quantize(CENTAVO, rounding=ROUND_HALF_UP),
	)


def _dinheiro(valor, nome):
	return validar_valor_monetario(valor, nome).quantize(CENTAVO, rounding=ROUND_HALF_UP)