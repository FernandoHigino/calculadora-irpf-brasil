from src.calculadora.faixas import carregar_tabelas
from src.calculadora.imposto import calcular_imposto
from src.utils.formatacao import formatar_reais


def main():
	tabelas = carregar_tabelas()
	periodo_padrao = max(tabelas.values(), key=lambda tabela: tabela["vigencia_inicio"])
	competencia_padrao = periodo_padrao["vigencia_inicio"][:7]
	print("Calculadora mensal de IRRF - estimativa")
	print(f"Competência mais recente cadastrada: {competencia_padrao}")

	competencia = input(f"Competência (AAAA-MM) [{competencia_padrao}]: ").strip()
	competencia = competencia or competencia_padrao
	ano, mes = (int(parte) for parte in competencia.split("-"))
	renda = input("Renda bruta mensal: ")
	dependentes = int(input("Número de dependentes [0]: ") or "0")
	outras_deducoes = input("Outras deduções legais mensais, como INSS [0]: ") or "0"
	simplificado = input("Usar desconto simplificado? (s/N): ").strip().lower() == "s"

	resultado = calcular_imposto(
		renda,
		ano,
		dependentes=dependentes,
		desconto_simplificado=simplificado,
		mes=mes,
		outras_deducoes=outras_deducoes,
	)
	print(f"Base de cálculo: {formatar_reais(resultado['base_calculo'])}")
	print(f"Redução legal: {formatar_reais(resultado['reducao'])}")
	print(f"Imposto estimado: {formatar_reais(resultado['imposto'])}")
	print(f"Renda após IR (sem outras retenções): {formatar_reais(resultado['renda_apos_ir'])}")
	print(f"Fonte cadastrada: {resultado['fonte']}")
	print("Este cálculo não substitui a apuração anual nem orientação profissional.")


if __name__ == "__main__":
	main()
