# 🇧🇷 Calculadora IRPF Brasil

Uma calculadora de Imposto de Renda desenvolvida para facilitar a vida de quem deseja entender melhor seus impostos.

O projeto permite simular o **Imposto de Renda Retido na Fonte (IRRF)** mensal e estimar o **ajuste anual do Imposto de Renda Pessoa Física (IRPF)**, apresentando os resultados de forma clara e detalhada.

A ideia é tornar os cálculos tributários mais acessíveis, permitindo que qualquer pessoa consulte uma estimativa do imposto e entenda como os valores foram calculados.

O projeto ainda está em desenvolvimento, e novas funcionalidades serão adicionadas gradualmente.

## 💻 Interface gráfica

A calculadora possui uma interface web desenvolvida com **React, TypeScript, Tailwind CSS e Lucide**, localizada na pasta `frontend/`.

O objetivo é oferecer uma experiência simples e intuitiva, sem exigir que o usuário conheça programação ou regras tributárias.

Atualmente, a interface permite realizar simulações mensais e anuais, consultar as tabelas utilizadas e visualizar a memória de cálculo.

### Como iniciar a aplicação

Primeiro, instale as dependências necessárias e inicie o backend:

```powershell
uv run --python 3.12 --with-requirements requirements.txt uvicorn src.api:app --reload --port 8000
```

Em outro terminal, com o Node.js instalado, execute:

```powershell
cd frontend
npm install
npm run dev
```

Depois, abra no navegador o endereço local informado pelo Vite.

## 🧮 Funcionalidades

A calculadora já conta com:

- Simulação mensal de IRRF.
- Estimativa do ajuste anual do IRPF.
- Aplicação das deduções previstas nas regras implementadas.
- Comparação entre deduções legais e desconto simplificado.
- Consulta às tabelas tributárias.
- Memória de cálculo para entender os resultados.
- Seleção das regras conforme o período informado.
- Interface web integrada ao backend em Python.

### Funcionalidades em desenvolvimento

Ainda pretendo implementar:

- Cálculo automático do INSS.
- Suporte às contribuições de PGBL.
- Histórico de simulações.
- Monitoramento de despesas dedutíveis.
- Importação de comprovantes, extratos e faturas.
- Atualizações e verificações das regras tributárias.

Por enquanto, o INSS deve ser informado manualmente. A aplicação também impede o uso de valores de PGBL que ainda não possuem tratamento implementado, evitando apresentar resultados incompletos como se fossem definitivos.

## ⚙️ Tecnologias utilizadas

**Backend**
- Python 3.12
- FastAPI
- Tabelas tributárias em JSON

**Frontend**
- React
- TypeScript
- Tailwind CSS
- Lucide

**Testes e distribuição**
- Pytest
- PyInstaller
- uv

As regras tributárias ficam separadas da lógica de cálculo, facilitando a manutenção e a inclusão de novos períodos.

## 🚀 Executar pelo terminal

Também é possível utilizar a calculadora diretamente pelo terminal, sem abrir a interface gráfica.

Na pasta principal do projeto, execute:

```powershell
uv run --python 3.12 --with-requirements requirements.txt python -m src.main
```

## 📦 Criar um executável para Windows

O projeto inclui um script para gerar um executável do Windows.

Com o `uv` disponível, execute:

```powershell
.\build_windows.ps1
```

O arquivo será gerado em:

```text
dist/CalculadoraIRPF.exe
```

O executável inclui as tabelas tributárias e utiliza uma janela de console para receber os dados.

Após a compilação, o usuário final poderá executar o programa sem precisar instalar Python.

## 🧪 Executar os testes

Para verificar o funcionamento dos cálculos, execute:

```powershell
uv run --python 3.12 --with-requirements requirements.txt python -m pytest -q
```

Os testes ajudam a identificar erros e verificar se alterações no código afetam os resultados.

## 📅 Atualizações das regras tributárias

As regras do Imposto de Renda mudam ao longo do tempo. Por isso, o projeto utiliza tabelas organizadas por período de vigência.

Atualmente, estão cadastradas as tabelas mensais de:

- Janeiro a abril de 2025.
- Maio a dezembro de 2025.
- 2026, incluindo a redução prevista na Lei nº 15.270/2025.

As informações ficam armazenadas em:

`src/dados/tabelas_ir.json`

Para adicionar novas regras, é necessário consultar as fontes oficiais, registrar o período de vigência e executar os testes antes de disponibilizar a atualização.

**As regras não são atualizadas automaticamente.** Como mudanças tributárias podem exigir interpretação jurídica, qualquer alteração precisa ser verificada antes de ser aplicada aos cálculos.

Para conhecer melhor o funcionamento do projeto, consulte:

- [Regras de cálculo](docs/regras_calculo.md)
- [Funcionamento da aplicação](docs/funcionamento.md)

## 🎯 Objetivo do projeto

Quero transformar esta calculadora em uma ferramenta cada vez mais completa para quem precisa organizar suas informações tributárias.

A proposta é reunir, em um único lugar, simulações de impostos, acompanhamento de despesas dedutíveis e recursos que ajudem o usuário a se preparar para a declaração anual.

Tudo isso com uma interface acessível e explicações que facilitem a compreensão dos resultados.

## ⚠️ Aviso importante

Este projeto está em desenvolvimento e fornece apenas **estimativas de Imposto de Renda**.

Os resultados não substituem a declaração oficial, a consulta às informações da Receita Federal ou a orientação de um profissional especializado.

Antes de tomar decisões financeiras, confira as regras vigentes e os valores apresentados.

---

**Desenvolvido por [FernandoHigino](https://github.com/FernandoHigino).**
## 📸 Capturas de tela

### Calculadora mensal 
![Calculadora mensal](assets/calculadora.png)

### Calculadora anual 
![Calculadora anual IRPF](assets/calculadora(2).png)

### Tabelas e regras
![Tabelas e regras](assets/calculadora(3).png)
