# Calculadora IRPF Brasil

Calculadora de estimativa mensal de IRRF e ajuste anual de IRPF em Python. As regras ficam em tabelas JSON versionadas por período, separadas da lógica de cálculo.

## Interface gráfica

O frontend React está em `frontend/` e usa TypeScript, Tailwind CSS e Lucide. Instale as dependências Python e inicie o backend:

```powershell
uv run --python 3.12 --with-requirements requirements.txt uvicorn src.api:app --reload --port 8000
```

Em outro terminal, com Node.js instalado, inicie a interface:

```powershell
cd frontend
npm install
npm run dev
```

Os formulários mensal e anual usam a API local, que também fornece as tabelas e a memória de cálculo. A contribuição ao INSS é informada manualmente e deduzida no IRRF; o cálculo automático do INSS, PGBL, histórico e atualizações automáticas ainda não estão implementados. A tela bloqueia valores de PGBL não suportados em vez de ignorá-los.

## Executar

```powershell
uv run --python 3.12 --with-requirements requirements.txt python -m src.main
```

Para gerar o executável de Windows, com Python 3.12 e PyInstaller gerenciados pelo `uv`:

```powershell
.\build_windows.ps1
```

O arquivo será criado em `dist/CalculadoraIRPF.exe`. O executável inclui a tabela tributária e abre uma janela de console para receber os dados. Para distribuir uma versão, envie esse `.exe` ao usuário final; não é necessário instalar Python na máquina dele.

Para rodar os testes:

```powershell
uv run --python 3.12 --with-requirements requirements.txt python -m pytest -q
```

## Atualizações tributárias

A tabela mensal cobre janeiro a abril e maio a dezembro de 2025, além da tabela de 2026 com a redução da Lei 15.270/2025. Para incluir um período novo, confira os atos legais e as tabelas oficiais, adicione uma entrada com início/fim de vigência em `src/dados/tabelas_ir.json` e registre a fonte. Rode todos os testes antes de publicar. O programa seleciona pela competência e não substitui uma tabela ausente por outra mais antiga.

Não há sincronização automática com a Receita Federal: mudanças legais exigem interpretação e validação humana, e uma busca automática na web não é fonte suficientemente confiável para mudar cálculos financeiros. Veja [docs/regras_calculo.md](docs/regras_calculo.md) e [docs/funcionamento.md](docs/funcionamento.md).

> Esta versão fornece estimativas mensais e anuais apenas para períodos cadastrados; não substitui a declaração oficial nem orientação fiscal. Confirme as regras vigentes com fontes oficiais antes de usar o resultado para decisões financeiras.

## 📸 Capturas de tela

### Calculadora mensal 
![Calculadora mensal](assets/calculadora.png)

### Calculadora anual 
![Calculadora anual IRPF](assets/calculadora(2).png)

### Tabelas e regras
![Tabelas e regras](assets/calculadora(3).png)