# Regras de cálculo

## Escopo

A implementação calcula estimativas de IRRF mensal e do ajuste anual de IRPF para os anos-calendário com regras cadastradas. Ano-calendário, exercício da declaração e período de vigência são conceitos diferentes; o cálculo anual informa ambos. A tabela deve ser conferida para o período efetivamente calculado.

## Tabelas cadastradas

O arquivo `src/dados/tabelas_ir.json` contém as tabelas progressivas mensais de janeiro a abril de 2025, de maio a dezembro de 2025 e de 2026. Cada entrada inclui vigência, fonte, faixas, alíquotas, parcelas a deduzir, dedução mensal por dependente e teto do desconto simplificado. Em 2026, inclui também a redução prevista na Lei 15.270/2025. Fontes: [Receita Federal - Tributação de 2025](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas/2025), [Receita Federal - Tributação de 2026](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas/2026) e [exemplos oficiais da redução](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas/exemplos-de-aplicacao-da-lei-15-270-2025).

O cálculo usa `imposto_tabela = max(0, base_calculo * aliquota - parcela_deduzir)`. A base é a renda bruta subtraída das deduções legais informadas (dependentes e outras) ou do desconto simplificado mensal cadastrado. As duas modalidades não são acumuladas. Em 2026, aplica-se ainda a redução mensal cadastrada: até R$ 5.000, limitada ao imposto calculado; de R$ 5.000,01 a R$ 7.350, usa-se R$ 978,62 menos 0,133145 vezes a renda tributável mensal; acima disso, não há redução.

## Ajuste anual

`src/dados/tabelas_ir_anuais.json` mantém tabelas anuais separadas das mensais: ano-calendário 2025 (exercício 2026) e 2026 (exercício 2027). O motor compara deduções legais e desconto simplificado e seleciona a modalidade com menor imposto, ou permite selecionar uma delas. O desconto simplificado é 20% dos rendimentos tributáveis, limitado ao teto anual. A dedução de educação é limitada por beneficiário elegível; envie cada valor individualmente em `despesas_educacionais`. Rendimentos isentos são registrados, mas não compõem a base tributável deste cálculo.

No ano-calendário 2026, além da tabela anual progressiva, aplica-se a redução da Lei 15.270/2025: redução limitada ao imposto progressivo para rendimentos tributáveis até R$ 60.000,00; acima desse valor e abaixo de R$ 88.200,00, `R$ 8.429,73 - (0,095575 x rendimentos tributáveis)`; a partir de R$ 88.200,00, não há redução. O imposto após a redução é comparado com o IRRF informado para estimar restituição ou saldo a pagar.

O campo `data_publicacao` fica nulo quando a página oficial consultada não informa uma data de publicação da tabela; a fonte oficial permanece registrada no próprio conjunto de regras.

O cálculo anual aceita despesas médicas e outras deduções legais informadas pelo usuário; a legitimidade e os comprovantes dessas despesas precisam ser conferidos. Rendimentos de categorias especiais, INSS, PGBL, carnê-leão, ganhos de capital e compensações não são calculados por este módulo.

## Atualização e limitações

Cada período de vigência deve ter uma entrada própria e fonte oficial verificada. Não existe atualização automática: tabelas oficiais podem mudar e novas leis podem criar redutores, regras transitórias ou tributos que não cabem no modelo de faixas simples. Para esses casos, além de atualizar dados, o algoritmo e os testes precisam ser revistos. A tabela de 2026 não deve ser presumida válida para anos futuros.

Este projeto é educativo e não constitui orientação fiscal. As fontes oficiais anuais usadas são [Receita Federal - Tributação de 2025](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas/2025) e [Receita Federal - Tributação de 2026](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/tabelas/2026). Antes de tomar decisões, valide o período, as deduções aplicáveis e a regra vigente em fonte oficial ou com profissional habilitado.
