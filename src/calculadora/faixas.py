"""Carregamento e validação das tabelas tributárias versionadas."""

import json
from datetime import date
from pathlib import Path


CAMINHO_TABELAS = Path(__file__).resolve().parents[1] / "dados" / "tabelas_ir.json"
CAMINHO_TABELAS_ANUAIS = Path(__file__).resolve().parents[1] / "dados" / "tabelas_ir_anuais.json"


def carregar_tabelas(caminho=CAMINHO_TABELAS):
	"""Carrega o arquivo de tabelas e valida as faixas antes do uso."""
	with Path(caminho).open(encoding="utf-8") as arquivo:
		dados = json.load(arquivo)

	tabelas = dados.get("tabelas")
	if not isinstance(tabelas, dict) or not tabelas:
		raise ValueError("Nenhuma tabela tributária foi cadastrada.")

	for ano, tabela in tabelas.items():
		_validar_tabela(ano, tabela)
	return tabelas


def obter_tabela(ano, caminho=CAMINHO_TABELAS):
	"""Retorna a tabela vigente no mês informado, sem fallback silencioso."""
	return obter_tabela_por_competencia(ano, 12, caminho)


def obter_tabela_por_competencia(ano, mes, caminho=CAMINHO_TABELAS):
	tabelas = carregar_tabelas(caminho)
	if isinstance(ano, bool) or not isinstance(ano, int):
		raise ValueError("Ano deve ser um número inteiro.")
	if isinstance(mes, bool) or not isinstance(mes, int) or not 1 <= mes <= 12:
		raise ValueError("Mês deve ser um inteiro entre 1 e 12.")

	competencia = date(ano, mes, 1).isoformat()
	for tabela in tabelas.values():
		inicio = tabela.get("vigencia_inicio")
		fim = tabela.get("vigencia_fim")
		if inicio <= competencia and (fim is None or competencia <= fim):
			return tabela

	competencias = ", ".join(sorted(tabelas))
	raise ValueError(
		f"Não há tabela para {ano}-{mes:02d}. Períodos disponíveis: {competencias}."
	)


def carregar_tabelas_anuais(caminho=CAMINHO_TABELAS_ANUAIS):
	"""Carrega e valida as tabelas anuais versionadas."""
	with Path(caminho).open(encoding="utf-8") as arquivo:
		dados = json.load(arquivo)

	tabelas = dados.get("tabelas")
	if not isinstance(tabelas, dict) or not tabelas:
		raise ValueError("Nenhuma tabela anual foi cadastrada.")

	for ano, tabela in tabelas.items():
		_validar_tabela_anual(ano, tabela)
	return tabelas


def obter_tabela_anual(ano_calendario, caminho=CAMINHO_TABELAS_ANUAIS):
	"""Retorna somente uma tabela anual cadastrada e validada."""
	if isinstance(ano_calendario, bool) or not isinstance(ano_calendario, int):
		raise ValueError("Ano-calendário deve ser um número inteiro.")

	tabelas = carregar_tabelas_anuais(caminho)
	try:
		return tabelas[str(ano_calendario)]
	except KeyError:
		periodos = ", ".join(sorted(tabelas))
		raise ValueError(
			f"Não há tabela anual verificada para {ano_calendario}. "
			f"Anos disponíveis: {periodos}."
		) from None


def _validar_tabela(ano, tabela):
	if not isinstance(tabela, dict) or not tabela.get("fonte"):
		raise ValueError(f"Tabela de {ano} precisa informar uma fonte.")
	faixas = tabela.get("faixas")
	if not isinstance(faixas, list) or not faixas:
		raise ValueError(f"Tabela de {ano} precisa conter faixas.")

	limites_anteriores = []
	for indice, faixa in enumerate(faixas):
		aliquota = faixa.get("aliquota")
		deducao = faixa.get("deducao")
		limite = faixa.get("limite_superior")
		if not isinstance(aliquota, (int, float)) or not 0 <= aliquota <= 1:
			raise ValueError(f"Alíquota inválida na tabela de {ano}.")
		if not isinstance(deducao, (int, float)) or deducao < 0:
			raise ValueError(f"Dedução inválida na tabela de {ano}.")
		if limite is None:
			if indice != len(faixas) - 1:
				raise ValueError(f"A faixa sem limite deve ser a última em {ano}.")
		elif not isinstance(limite, (int, float)) or limite <= 0:
			raise ValueError(f"Limite inválido na tabela de {ano}.")
		else:
			limites_anteriores.append(limite)

	if limites_anteriores != sorted(set(limites_anteriores)):
		raise ValueError(f"Os limites da tabela de {ano} devem ser crescentes.")
	if faixas[-1].get("limite_superior") is not None:
		raise ValueError(f"A última faixa da tabela de {ano} deve ser aberta.")

	for campo in ("deducao_dependente", "desconto_simplificado_maximo"):
		valor = tabela.get(campo)
		if not isinstance(valor, (int, float)) or valor < 0:
			raise ValueError(f"Campo {campo} inválido na tabela de {ano}.")

	inicio = tabela.get("vigencia_inicio")
	fim = tabela.get("vigencia_fim")
	try:
		date.fromisoformat(inicio)
		if fim is not None:
			date.fromisoformat(fim)
			if fim < inicio:
				raise ValueError
	except (TypeError, ValueError):
		raise ValueError(f"Vigência inválida na tabela de {ano}.") from None

	redutor = tabela.get("reducao_mensal")
	if redutor is not None:
		campos = ("limite_isencao", "limite_final", "valor_maximo", "termo_constante", "coeficiente")
		if any(not isinstance(redutor.get(campo), (int, float)) for campo in campos):
			raise ValueError(f"Redução mensal inválida na tabela de {ano}.")


def _validar_tabela_anual(ano, tabela):
	_validar_tabela(ano, tabela)
	try:
		ano_numero = int(ano)
		if tabela.get("ano_calendario") != ano_numero:
			raise ValueError
		if tabela.get("exercicio") != ano_numero + 1:
			raise ValueError
		if not tabela.get("versao_regras") or tabela.get("periodicidade") != "anual":
			raise ValueError
		data_publicacao = tabela.get("data_publicacao")
		if data_publicacao is not None:
			date.fromisoformat(data_publicacao)
		for campo in ("limite_educacao_por_beneficiario", "desconto_simplificado_percentual"):
			valor = tabela.get(campo)
			if not isinstance(valor, (int, float)) or valor < 0:
				raise ValueError
		if tabela["desconto_simplificado_percentual"] > 1:
			raise ValueError
		reducao = tabela.get("reducao_anual")
		if reducao is not None:
			campos = ("limite_isencao", "limite_final", "valor_maximo", "termo_constante", "coeficiente")
			if any(not isinstance(reducao.get(campo), (int, float)) for campo in campos):
				raise ValueError
	except (TypeError, ValueError):
		raise ValueError(f"Metadados anuais inválidos para {ano}.") from None
