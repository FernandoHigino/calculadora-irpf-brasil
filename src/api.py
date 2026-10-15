"""API stateless para os cálculos mensais e anuais do IRPF."""

from decimal import Decimal
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from src.calculadora.faixas import (
	carregar_tabelas,
	carregar_tabelas_anuais,
	obter_tabela_anual,
	obter_tabela_por_competencia,
)
from src.calculadora.imposto import calcular_imposto, comparar_deducoes_mensais
from src.calculadora.irpf_anual import calcular_irpf_anual


Money = Annotated[
	Decimal,
	Field(ge=Decimal("0"), max_digits=16, decimal_places=2, allow_inf_nan=False),
]
MonthlyMode = Literal["deducoes_legais", "desconto_simplificado", "mais_vantajosa"]
AnnualMode = Literal["deducoes_legais", "desconto_simplificado", "mais_vantajosa"]


class RequestModel(BaseModel):
	model_config = ConfigDict(extra="forbid")


class MonthlyCalculationRequest(RequestModel):
	ano: int = Field(ge=1900, le=2200)
	mes: int = Field(ge=1, le=12)
	renda_bruta: Money
	inss_contribuicao: Money = Decimal("0.00")
	dependentes: int = Field(default=0, ge=0)
	outras_deducoes: Money = Decimal("0.00")
	modalidade: MonthlyMode = "deducoes_legais"


class AnnualCalculationRequest(RequestModel):
	ano_calendario: int = Field(ge=1900, le=2200)
	rendimentos_tributaveis: Money
	rendimentos_isentos: Money = Decimal("0.00")
	irrf_retido: Money = Decimal("0.00")
	dependentes: int = Field(default=0, ge=0)
	despesas_medicas: Money = Decimal("0.00")
	despesas_educacionais: list[Money] = Field(default_factory=list)
	previdencia_privada: Money = Decimal("0.00")
	outras_deducoes: Money = Decimal("0.00")
	modalidade: AnnualMode = "mais_vantajosa"


app = FastAPI(
	title="Calculadora IRPF Brasil",
	version="1.0.0",
	description="API stateless para estimativas mensais de IRRF e anuais de IRPF.",
)
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
	allow_credentials=False,
	allow_methods=["GET", "POST"],
	allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health_check():
	return {"status": "ok"}


@app.get("/api/tabelas")
def consultar_tabelas():
	return _execute(
		lambda: {
			"mensais": carregar_tabelas(),
			"anuais": carregar_tabelas_anuais(),
		}
	)


@app.get("/api/tabelas/mensal/{ano}/{mes}")
def consultar_tabela_mensal(ano: int, mes: int):
	return _execute(lambda: obter_tabela_por_competencia(ano, mes))


@app.get("/api/tabelas/anual/{ano_calendario}")
def consultar_tabela_anual(ano_calendario: int):
	return _execute(lambda: obter_tabela_anual(ano_calendario))


@app.get("/api/deducoes/mensal/{ano}/{mes}")
def consultar_deducoes_mensais(ano: int, mes: int):
	def consultar():
		tabela = obter_tabela_por_competencia(ano, mes)
		return {
			"ano": ano,
			"mes": mes,
			"versao_regras": tabela["versao_regras"],
			"deducao_dependente": tabela["deducao_dependente"],
			"desconto_simplificado_maximo": tabela["desconto_simplificado_maximo"],
			"fonte": tabela["fonte"],
		}

	return _execute(consultar)


@app.get("/api/deducoes/anual/{ano_calendario}")
def consultar_deducoes_anuais(ano_calendario: int):
	def consultar():
		tabela = obter_tabela_anual(ano_calendario)
		return {
			"ano_calendario": ano_calendario,
			"exercicio": tabela["exercicio"],
			"versao_regras": tabela["versao_regras"],
			"deducao_dependente": tabela["deducao_dependente"],
			"limite_educacao_por_beneficiario": tabela["limite_educacao_por_beneficiario"],
			"desconto_simplificado_percentual": tabela["desconto_simplificado_percentual"],
			"desconto_simplificado_maximo": tabela["desconto_simplificado_maximo"],
			"fonte": tabela["fonte"],
		}

	return _execute(consultar)


@app.post("/api/calculos/mensal")
def calcular_mensal(request: MonthlyCalculationRequest):
	return _execute(lambda: _calcular_mensal(request))


@app.post("/api/calculos/anual")
def calcular_anual(request: AnnualCalculationRequest):
	return _execute(lambda: _calcular_anual(request))


@app.post("/api/memoria-calculo/mensal")
def memoria_calculo_mensal(request: MonthlyCalculationRequest):
	return _execute(lambda: _calcular_mensal(request)["memoria_calculo"])


@app.post("/api/memoria-calculo/anual")
def memoria_calculo_anual(request: AnnualCalculationRequest):
	return _execute(lambda: _calcular_anual(request)["memoria_calculo"])


def _calcular_mensal(request: MonthlyCalculationRequest):
	tabela = obter_tabela_por_competencia(request.ano, request.mes)
	comparacao = comparar_deducoes_mensais(
		request.renda_bruta,
		request.ano,
		dependentes=request.dependentes,
		mes=request.mes,
		outras_deducoes=request.inss_contribuicao + request.outras_deducoes,
	)
	if request.modalidade == "mais_vantajosa":
		modalidade_aplicada = comparacao["mais_vantajosa"]
	else:
		modalidade_aplicada = request.modalidade
	resultado = _com_aliquota_efetiva(
		comparacao["cenarios"][modalidade_aplicada],
		"renda_bruta",
		"imposto",
	)
	memoria = {
		"tipo": "mensal",
		"ano": request.ano,
		"mes": request.mes,
		"versao_regras": tabela["versao_regras"],
		"fonte": tabela["fonte"],
		"rendimentos_considerados": {"renda_bruta": resultado["renda_bruta"]},
		"inss_informado": request.inss_contribuicao,
		"outras_deducoes_informadas": request.outras_deducoes,
		"deducoes_utilizadas": resultado["deducoes_detalhadas"],
		"modalidade_aplicada": modalidade_aplicada,
		"base_calculo": resultado["base_calculo"],
		"faixa_numero": resultado["faixa_numero"],
		"limite_superior_faixa": resultado["limite_superior_faixa"],
		"aliquota": resultado["aliquota"],
		"parcela_deduzir": resultado["parcela_deduzir"],
		"imposto_tabela": resultado["imposto_tabela"],
		"reducao": resultado["reducao"],
		"imposto_devido": resultado["imposto"],
		"renda_apos_ir": resultado["renda_apos_ir"],
		"formula_base": f"{resultado['renda_bruta']} - {resultado['deducoes']} = {resultado['base_calculo']}",
		"formula_imposto": (
			f"max(0, {resultado['base_calculo']} × {resultado['aliquota']} - "
			f"{resultado['parcela_deduzir']}) = {resultado['imposto_tabela']}; "
			f"{resultado['imposto_tabela']} - {resultado['reducao']} = {resultado['imposto']}"
		),
	}
	return {
		"tipo": "mensal",
		"resultado": resultado,
		"comparacao": {
			"mais_vantajosa": comparacao["mais_vantajosa"],
			"diferenca_entre_modalidades": comparacao["diferenca_entre_modalidades"],
			"cenarios": comparacao["cenarios"],
		},
		"memoria_calculo": memoria,
	}


def _calcular_anual(request: AnnualCalculationRequest):
	if request.previdencia_privada > 0:
		raise HTTPException(
			status_code=422,
			detail="PGBL ainda não está disponível; zere esse campo para calcular sem essa dedução.",
		)
	resultado = calcular_irpf_anual(
		request.rendimentos_tributaveis,
		request.ano_calendario,
		rendimentos_isentos=request.rendimentos_isentos,
		dependentes=request.dependentes,
		despesas_medicas=request.despesas_medicas,
		despesas_educacionais=request.despesas_educacionais,
		outras_deducoes=request.outras_deducoes,
		irrf_retido=request.irrf_retido,
		modalidade=request.modalidade,
	)
	resultado["cenarios"] = {
		modalidade: _com_aliquota_efetiva(
			cenario,
			"",
			"imposto_devido",
			request.rendimentos_tributaveis,
		)
		for modalidade, cenario in resultado["cenarios"].items()
	}
	resultado_selecionado = _com_aliquota_efetiva(
		resultado,
		"rendimentos_tributaveis",
		"imposto_devido",
	)
	modalidade_aplicada = resultado_selecionado["modalidade_aplicada"]
	cenario = resultado_selecionado["cenarios"][modalidade_aplicada]
	tabela = obter_tabela_anual(request.ano_calendario)
	memoria = {
		"tipo": "anual",
		"ano_calendario": resultado["ano_calendario"],
		"exercicio": resultado["exercicio"],
		"versao_regras": resultado["versao_regras"],
		"fonte": resultado["fonte"],
		"rendimentos_considerados": {
			"tributaveis": resultado["rendimentos_tributaveis"],
			"isentos": resultado["rendimentos_isentos"],
		},
		"irrf_retido": resultado["irrf_retido"],
		"deducoes_utilizadas": cenario["deducoes_detalhadas"],
		"modalidade_aplicada": modalidade_aplicada,
		"base_calculo": resultado["base_calculo"],
		"faixa_numero": resultado["faixa_numero"],
		"limite_superior_faixa": cenario["limite_superior_faixa"],
		"aliquota": resultado_selecionado["aliquota"],
		"aliquota_efetiva": resultado_selecionado["aliquota_efetiva"],
		"parcela_deduzir": resultado_selecionado["parcela_deduzir"],
		"imposto_tabela": resultado_selecionado["imposto_tabela"],
		"reducao": resultado_selecionado["reducao"],
		"imposto_devido": resultado_selecionado["imposto_devido"],
		"imposto_a_pagar": resultado_selecionado["imposto_a_pagar"],
		"restituicao_estimada": resultado_selecionado["restituicao_estimada"],
		"formula_base": f"{resultado_selecionado['rendimentos_tributaveis']} - {resultado_selecionado['deducoes']} = {resultado_selecionado['base_calculo']}",
		"formula_imposto": (
			f"max(0, {resultado_selecionado['base_calculo']} × {resultado_selecionado['aliquota']} - "
			f"{resultado_selecionado['parcela_deduzir']}) = {resultado_selecionado['imposto_tabela']}; "
			f"{resultado_selecionado['imposto_tabela']} - {resultado_selecionado['reducao']} = "
			f"{resultado_selecionado['imposto_devido']}"
		),
		"data_publicacao": tabela["data_publicacao"],
	}
	return {
		"tipo": "anual",
		"resultado": resultado_selecionado,
		"comparacao": {
			"mais_vantajosa": resultado_selecionado["mais_vantajosa"],
			"diferenca_entre_modalidades": resultado_selecionado["diferenca_entre_modalidades"],
			"cenarios": resultado_selecionado["cenarios"],
		},
		"memoria_calculo": memoria,
	}


def _com_aliquota_efetiva(resultado, chave_renda, chave_imposto, renda_considerada=None):
	completo = dict(resultado)
	renda = (
		Decimal(str(completo[chave_renda]))
		if renda_considerada is None
		else Decimal(str(renda_considerada))
	)
	imposto = Decimal(str(completo[chave_imposto]))
	completo["aliquota_efetiva"] = Decimal("0") if renda == 0 else imposto / renda
	return completo


def _execute(operation):
	try:
		return _serializar(operation())
	except HTTPException:
		raise
	except (ValueError, TypeError) as error:
		raise HTTPException(status_code=422, detail=str(error)) from error


def _serializar(value):
	if isinstance(value, Decimal):
		return format(value, "f")
	if isinstance(value, dict):
		return {key: _serializar(item) for key, item in value.items()}
	if isinstance(value, (list, tuple)):
		return [_serializar(item) for item in value]
	return value
