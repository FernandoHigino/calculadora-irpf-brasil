from decimal import Decimal, ROUND_HALF_UP

from src.calculadora.deducoes import calcular_deducoes
from src.calculadora.faixas import obter_tabela_por_competencia
from src.utils.validacoes import validar_dependentes, validar_valor_monetario


CENTAVO = Decimal("0.01")


def calcular_imposto(
	renda_bruta,
	ano,
	dependentes=0,
	desconto_simplificado=False,
	mes=12,
	outras_deducoes=0,
):
	"""Calcula uma estimativa mensal de IRRF usando a tabela do ano indicado."""
	renda = validar_valor_monetario(renda_bruta, "renda bruta")
	deducoes_adicionais = validar_valor_monetario(outras_deducoes, "outras deduções")
	quantidade_dependentes = validar_dependentes(dependentes)
	tabela = obter_tabela_por_competencia(ano, mes)
	deducao = calcular_deducoes(
		renda,
		quantidade_dependentes,
		tabela,
		outras_deducoes=deducoes_adicionais,
		desconto_simplificado=desconto_simplificado,
	)
	base_calculo = max(Decimal("0"), renda - deducao).quantize(CENTAVO)

	for indice, faixa in enumerate(tabela["faixas"], start=1):
		limite = faixa["limite_superior"]
		if limite is None or base_calculo <= Decimal(str(limite)):
			aliquota = Decimal(str(faixa["aliquota"]))
			parcela_deduzir = Decimal(str(faixa["deducao"]))
			imposto_tabela = max(
				Decimal("0"), base_calculo * aliquota - parcela_deduzir
			).quantize(CENTAVO, rounding=ROUND_HALF_UP)
			reducao = _calcular_reducao(renda, imposto_tabela, tabela)
			imposto = max(Decimal("0"), imposto_tabela - reducao).quantize(
				CENTAVO, rounding=ROUND_HALF_UP
			)
			deducao_dependentes = (
				Decimal(str(tabela["deducao_dependente"])) * quantidade_dependentes
			).quantize(CENTAVO, rounding=ROUND_HALF_UP)
			return {
				"ano": int(ano),
				"mes": mes,
				"periodicidade": tabela["periodicidade"],
				"versao_regras": tabela["versao_regras"],
				"renda_bruta": renda.quantize(CENTAVO),
				"deducoes": deducao,
				"deducoes_detalhadas": {
					"dependentes": deducao_dependentes if not desconto_simplificado else Decimal("0.00"),
					"outras_deducoes": deducoes_adicionais if not desconto_simplificado else Decimal("0.00"),
					"desconto_simplificado": deducao if desconto_simplificado else Decimal("0.00"),
				},
				"base_calculo": base_calculo,
				"faixa_numero": indice,
				"limite_superior_faixa": None if limite is None else Decimal(str(limite)),
				"aliquota": aliquota,
				"parcela_deduzir": parcela_deduzir,
				"imposto_tabela": imposto_tabela,
				"reducao": reducao.quantize(CENTAVO, rounding=ROUND_HALF_UP),
				"imposto": imposto,
				"renda_apos_ir": (renda - imposto).quantize(CENTAVO, rounding=ROUND_HALF_UP),
				"fonte": tabela["fonte"],
			}

	raise ValueError("A tabela não contém uma faixa aplicável.")


def comparar_deducoes_mensais(
	renda_bruta,
	ano,
	*,
	dependentes=0,
	mes=12,
	outras_deducoes=0,
):
	"""Compara IRRF com deduções legais e desconto simplificado mensal."""
	cenario_legal = calcular_imposto(
		renda_bruta,
		ano,
		dependentes=dependentes,
		mes=mes,
		outras_deducoes=outras_deducoes,
	)
	cenario_simplificado = calcular_imposto(
		renda_bruta,
		ano,
		dependentes=dependentes,
		mes=mes,
		outras_deducoes=outras_deducoes,
		desconto_simplificado=True,
	)
	mais_vantajosa = (
		"deducoes_legais"
		if cenario_legal["imposto"] <= cenario_simplificado["imposto"]
		else "desconto_simplificado"
	)
	return {
		"mais_vantajosa": mais_vantajosa,
		"diferenca_entre_modalidades": abs(
			cenario_legal["imposto"] - cenario_simplificado["imposto"]
		).quantize(CENTAVO, rounding=ROUND_HALF_UP),
		"cenarios": {
			"deducoes_legais": cenario_legal,
			"desconto_simplificado": cenario_simplificado,
		},
		"resultado": (
			cenario_legal
			if mais_vantajosa == "deducoes_legais"
			else cenario_simplificado
		),
	}


def _calcular_reducao(renda, imposto_tabela, tabela):
	regra = tabela.get("reducao_mensal")
	if regra is None:
		return Decimal("0")

	limite_isencao = Decimal(str(regra["limite_isencao"]))
	limite_final = Decimal(str(regra["limite_final"]))
	if renda <= limite_isencao:
		reducao_calculada = Decimal(str(regra["valor_maximo"]))
	elif renda <= limite_final:
		reducao_calculada = Decimal(str(regra["termo_constante"])) - (
			Decimal(str(regra["coeficiente"])) * renda
		)
	else:
		return Decimal("0")

	reducao_calculada = max(Decimal("0"), reducao_calculada)
	return min(imposto_tabela, reducao_calculada).quantize(
		CENTAVO, rounding=ROUND_HALF_UP
	)
