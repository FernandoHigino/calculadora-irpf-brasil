from fastapi.testclient import TestClient

from src.api import app


client = TestClient(app)


def test_calculo_mensal_retorna_resultado_e_memoria_oficiais():
	response = client.post(
		"/api/calculos/mensal",
		json={
			"ano": 2026,
			"mes": 1,
			"renda_bruta": "6000.00",
			"inss_contribuicao": "649.60",
			"dependentes": 0,
			"outras_deducoes": "0.00",
			"modalidade": "deducoes_legais",
		},
	)

	assert response.status_code == 200
	payload = response.json()
	assert payload["resultado"]["imposto"] == "382.88"
	assert payload["resultado"]["base_calculo"] == "5350.40"
	assert payload["memoria_calculo"]["faixa_numero"] == 5
	assert payload["memoria_calculo"]["parcela_deduzir"] == "908.73"
	assert payload["memoria_calculo"]["reducao"] == "179.75"
	assert payload["memoria_calculo"]["formula_base"] == "6000.00 - 649.60 = 5350.40"
	assert payload["memoria_calculo"]["versao_regras"] == "2026.1"


def test_calculo_anual_retorna_imposto_e_restituicao():
	response = client.post(
		"/api/calculos/anual",
		json={
			"ano_calendario": 2025,
			"rendimentos_tributaveis": "50000.00",
			"rendimentos_isentos": "0.00",
			"irrf_retido": "2000.00",
			"dependentes": 0,
			"despesas_medicas": "0.00",
			"despesas_educacionais": [],
			"previdencia_privada": "0.00",
			"outras_deducoes": "0.00",
			"modalidade": "mais_vantajosa",
		},
	)

	assert response.status_code == 200
	payload = response.json()
	assert payload["resultado"]["imposto_devido"] == "1320.97"
	assert payload["resultado"]["restituicao_estimada"] == "679.03"
	assert payload["memoria_calculo"]["exercicio"] == 2026
	assert payload["memoria_calculo"]["fonte"].startswith("Receita Federal")


def test_consulta_tabelas_e_deducoes_anuais():
	colecao = client.get("/api/tabelas")
	tabela = client.get("/api/tabelas/anual/2026")
	deducoes = client.get("/api/deducoes/anual/2026")
	tabela_mensal = client.get("/api/tabelas/mensal/2026/1")
	deducoes_mensais = client.get("/api/deducoes/mensal/2026/1")

	assert colecao.status_code == 200
	assert "2026-01-em-diante" in colecao.json()["mensais"]
	assert "2026" in colecao.json()["anuais"]
	assert tabela.status_code == 200
	assert tabela.json()["exercicio"] == 2027
	assert deducoes.status_code == 200
	assert deducoes.json()["limite_educacao_por_beneficiario"] == 3561.5
	assert tabela_mensal.status_code == 200
	assert tabela_mensal.json()["versao_regras"] == "2026.1"
	assert deducoes_mensais.status_code == 200
	assert deducoes_mensais.json()["deducao_dependente"] == 189.59


def test_memoria_de_calculo_pode_ser_consultada_separadamente():
	response = client.post(
		"/api/memoria-calculo/mensal",
		json={"ano": 2025, "mes": 12, "renda_bruta": "5000.00"},
	)

	assert response.status_code == 200
	assert response.json()["tipo"] == "mensal"
	assert response.json()["base_calculo"] == "5000.00"
	assert response.json()["imposto_devido"] == "466.27"


def test_memoria_anual_pode_ser_consultada_separadamente():
	response = client.post(
		"/api/memoria-calculo/anual",
		json={
			"ano_calendario": 2025,
			"rendimentos_tributaveis": "50000.00",
			"irrf_retido": "2000.00",
			"modalidade": "desconto_simplificado",
		},
	)

	assert response.status_code == 200
	assert response.json()["tipo"] == "anual"
	assert response.json()["imposto_devido"] == "1320.97"
	assert response.json()["restituicao_estimada"] == "679.03"


def test_periodo_sem_tabela_e_explicado_com_status_422():
	response = client.post(
		"/api/calculos/mensal",
		json={"ano": 2024, "mes": 12, "renda_bruta": "5000.00"},
	)

	assert response.status_code == 422
	assert "Não há tabela para 2024-12" in response.json()["detail"]


def test_rejeita_entradas_monetarias_negativas():
	response = client.post(
		"/api/calculos/anual",
		json={"ano_calendario": 2025, "rendimentos_tributaveis": "-1.00"},
	)

	assert response.status_code == 422


def test_pgbl_nao_suportado_nao_e_silenciosamente_ignorado():
	response = client.post(
		"/api/calculos/anual",
		json={
			"ano_calendario": 2025,
			"rendimentos_tributaveis": "50000.00",
			"previdencia_privada": "1000.00",
		},
	)

	assert response.status_code == 422
	assert "PGBL ainda não está disponível" in response.json()["detail"]


def test_endpoint_inss_informado_eh_mapeado_como_deducao_mensal():
	response = client.post(
		"/api/calculos/mensal",
		json={
			"ano": 2025,
			"mes": 12,
			"renda_bruta": "5000.00",
			"inss_contribuicao": "500.00",
			"modalidade": "deducoes_legais",
		},
	)

	assert response.status_code == 200
	assert response.json()["resultado"]["deducoes_detalhadas"]["outras_deducoes"] == "500.00"
