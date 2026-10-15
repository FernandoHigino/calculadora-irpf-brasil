# Funcionamento

1. `src.main` pede a competência (`AAAA-MM`), a renda bruta mensal, a quantidade de dependentes, outras deduções legais e a opção de desconto simplificado.
2. `src.utils.validacoes` converte valores monetários (inclusive no formato `1.234,56`) para `Decimal` e rejeita entradas negativas ou inválidas.
3. `src.calculadora.faixas` carrega e valida `src/dados/tabelas_ir.json`; uma competência sem cadastro gera erro em vez de usar regras de outro período.
4. `src.calculadora.deducoes` calcula as deduções legais informadas (dependentes e outras) ou aplica o desconto simplificado, conforme a opção indicada.
5. `src.calculadora.imposto` calcula a base, aplica alíquota e parcela a deduzir da faixa e, quando previsto, a redução legal do imposto.
6. `src.calculadora.irpf_anual.calcular_irpf_anual` estima o ajuste anual, compara as deduções legais com o desconto simplificado e calcula restituição ou saldo a pagar para anos com tabela cadastrada.

O comando de terminal continua oferecendo somente o cálculo mensal. A interface comunica com `src.api` via FastAPI para cálculos mensal/anual, consulta de tabelas e memória. O backend é stateless e não armazena os valores enviados. A contribuição ao INSS é informada manualmente e entra como dedução no cálculo mensal; o simulador de INSS ainda não está implementado. O campo PGBL não é considerado e uma contribuição positiva é recusada explicitamente. Ainda não inclui categorias especiais de renda, compensações ou regras não expressas nas tabelas. A despesa educacional na interface representa um beneficiário por simulação nesta etapa.

## Executar a aplicação integrada

Inicie a API com `uv run --python 3.12 --with-requirements requirements.txt uvicorn src.api:app --reload --port 8000`. Em outro terminal, entre em `frontend/`, execute `npm install` e `npm run dev`. O Vite encaminha `/api` para `127.0.0.1:8000`.

Os endpoints incluem `POST /api/calculos/mensal`, `POST /api/calculos/anual`, `GET /api/tabelas`, consultas por período em `/api/tabelas/...` e `/api/deducoes/...`, e `POST /api/memoria-calculo/{mensal|anual}`. As requisições não são armazenadas.

## Atualizar uma tabela

Confira a publicação oficial aplicável ao período e adicione uma entrada mensal em `src/dados/tabelas_ir.json` ou uma entrada anual em `src/dados/tabelas_ir_anuais.json`. Registre início e fim de vigência e a fonte consultada; se a regra tiver um cálculo novo, atualize também a lógica e crie testes com exemplos oficiais. Execute `uv run --python 3.12 --with-requirements requirements.txt python -m pytest` antes de disponibilizar a alteração. Não edite períodos antigos para representar uma lei nova: mantenha cada período versionado.
