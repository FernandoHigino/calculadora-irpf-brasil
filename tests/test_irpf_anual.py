from decimal import Decimal

import pytest

from src.calculadora.faixas import obter_tabela_anual
from src.calculadora.irpf_anual import calcular_irpf_anual


def test_calculo_anual_2025_compara_modalidades_e_calcula_restituicao():
	resultado = calcular_irpf_anual(
		"50.000,00",
		2025,
		irrf_retido="2.000,00",
	)

	assert resultado["exercicio"] == 2026
	assert resultado["versao_regras"] == "2025.1"
	assert resultado["mais_vantajosa"] == "desconto_simplificado"
	assert resultado["cenarios"]["deducoes_legais"]["imposto_devido"] == Decimal("3195.03")
	assert resultado["cenarios"]["desconto_simplificado"]["deducoes"] == Decimal("10000.00")
	assert resultado["imposto_devido"] == Decimal("1320.97")
	assert resultado["restituicao_estimada"] == Decimal("679.03")
	assert resultado["imposto_a_pagar"] == Decimal("0.00")


def test_deducoes_legais_aplicam_limite_de_educacao_por_beneficiario():
	resultado = calcular_irpf_anual(
		50000,
		2025,
		dependentes=1,
		despesas_medicas=1000,
		despesas_educacionais=[5000, 2000],
		modalidade="deducoes_legais",
	)
	deducoes = resultado["cenarios"]["deducoes_legais"]["deducoes_detalhadas"]

	assert deducoes["dependentes"] == Decimal("2275.08")
	assert deducoes["despesas_educacionais_informadas"] == Decimal("7000.00")
	assert deducoes["despesas_educacionais_dedutiveis"] == Decimal("5561.50")
	assert resultado["deducoes"] == Decimal("8836.58")
	assert resultado["base_calculo"] == Decimal("41163.42")


def test_reducao_anual_2026_zera_imposto_ate_limite_legal():
	resultado = calcular_irpf_anual(60000, 2026, irrf_retido=1000)

	assert resultado["exercicio"] == 2027
	assert resultado["imposto_devido"] == Decimal("0.00")
	assert resultado["restituicao_estimada"] == Decimal("1000.00")


def test_reducao_anual_2026_decresce_na_faixa_intermediaria():
	resultado = calcular_irpf_anual(80000, 2026, modalidade="deducoes_legais")

	assert resultado["reducao"] == Decimal("783.73")
	assert resultado["imposto_devido"] == Decimal("10311.61")


def test_reducao_anual_termina_no_limite_publicado():
	no_limite = calcular_irpf_anual(88200, 2026, modalidade="deducoes_legais")
	acima = calcular_irpf_anual(88200.01, 2026, modalidade="deducoes_legais")

	assert no_limite["reducao"] == Decimal("0.00")
	assert acima["reducao"] == Decimal("0.00")


@pytest.mark.parametrize(
	("ano", "renda", "faixa"),
	[
		(2025, "28.467,20", 1),
		(2025, "28.467,21", 2),
		(2025, "33.919,80", 2),
		(2025, "33.919,81", 3),
		(2025, "45.012,60", 3),
		(2025, "45.012,61", 4),
		(2025, "55.976,16", 4),
		(2025, "55.976,17", 5),
		(2026, "29.145,60", 1),
		(2026, "29.145,61", 2),
	],
)
def test_seleciona_faixa_anual_nos_limites(ano, renda, faixa):
	resultado = calcular_irpf_anual(
		renda,
		ano,
		modalidade="deducoes_legais",
	)
	assert resultado["faixa_numero"] == faixa


def test_periodo_anual_sem_tabela_e_bloqueado():
	with pytest.raises(ValueError, match="Não há tabela anual verificada para 2024"):
		calcular_irpf_anual(50000, 2024)


@pytest.mark.parametrize("valor", ["-1", "invalido", float("inf"), True])
def test_rejeita_rendimentos_anuais_invalidos(valor):
	with pytest.raises(ValueError):
		calcular_irpf_anual(valor, 2025)


def test_rejeita_modalidade_de_deducao_desconhecida():
	with pytest.raises(ValueError, match="Modalidade deve ser"):
		calcular_irpf_anual(50000, 2025, modalidade="ambas")


def test_tabela_anual_expõe_fonte_oficial_e_metadados():
	tabela = obter_tabela_anual(2026)

	assert tabela["ano_calendario"] == 2026
	assert tabela["exercicio"] == 2027
	assert tabela["data_publicacao"] == "2025-11-26"
	assert "gov.br/receitafederal" in tabela["fonte"]