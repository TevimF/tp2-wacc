# Trabalho 2 — Custo de capital da frota

Administração Financeira, UFMG, 2026/2. Professor Bruno Pérez Ferreira.
Dupla: Estêvão Felipe da Fonseca e João Marcos de Sousa Rezende.

## Objetivo

Calcular o custo médio ponderado de capital (WACC) de uma empresa que pretende
financiar uma frota combinando capital próprio e dívida. O tema escolhido é
**Estrutura de Capital**, previsto no enunciado do Trabalho 2.

É uma aplicação pequena de terminal, sem instalação de pacotes. Mantém o contexto
da frota do Trabalho 1, mas aborda outro conteúdo: o custo das fontes de
financiamento. Não é necessário instalar nem executar o projeto anterior.

## Como executar

Requer Python 3.10 ou superior. Extraia o ZIP, abra o terminal na pasta e execute:

```bash
python wacc.py
```

No Linux, o comando pode ser `python3`. No Windows, pode ser `py`.
Os campos mostram valores de exemplo; pressione Enter para mantê-los.
Aceita `1,2` ou `1.2`, sem separador de milhar.

Para executar imediatamente um exemplo fictício, sem internet nem digitação:

```bash
python wacc.py --exemplo
```

O programa mostra os resultados e grava `relatorio_wacc.txt` na pasta atual.
O relatório pode ser aberto em qualquer editor de texto. Para outro nome:

```bash
python wacc.py --exemplo --saida meu_relatorio.txt
```

## Relação com os critérios de avaliação

| Critério do enunciado | Onde aparece |
|---|---|
| Execução da aplicação | Entrada pelo terminal, cálculo e resultado imediato |
| Captura de dados | Consulta opcional à API oficial do Banco Central, com data e fonte |
| Comentários no código | Docstrings e comentários explicam CAPM, pesos, impostos e unidades |
| Geração de relatórios | TXT gerado pela execução com entradas, metodologia e interpretação |

Se a API estiver indisponível, o programa informa a falha e permite digitar a taxa.
Ele não apresenta os valores de exemplo como se tivessem sido capturados.

## Conferência manual do exemplo

Todos os valores são **fictícios**. A taxa de 10% não representa a Selic atual.

| Entrada | Valor |
|---|---:|
| Capital próprio (E) | R$ 300.000 |
| Dívida (D) | R$ 200.000 |
| Taxa livre de risco (Rf) | 10% a.a. |
| Prêmio de risco de mercado | 6 pontos percentuais a.a. |
| Beta | 1,2 |
| Spread de crédito | 3 pontos percentuais a.a. |
| Alíquota corporativa assumida | 30% |

- Ke = 10% + 1,2 × 6% = **17,20% a.a.**
- Kd = 10% + 3% = **13,00% a.a.**
- Kd após impostos = 13% × (1 − 0,30) = **9,10% a.a.**
- Peso E = 300.000 / 500.000 = **60%**; peso D = **40%**.
- WACC = 0,60 × 17,20% + 0,40 × 9,10% = **13,96% a.a.**

Prêmio de risco é Rm − Rf; não se deve informar o retorno total de mercado nesse
campo. Os pesos são valores de mercado, conforme o capítulo 12.

## Ligação com os materiais da turma

Foram consultados o enunciado, os capítulos 12 a 15 e o exemplo `WACC.html`.

| Material | Uso no trabalho |
|---|---|
| Cap. 12 — Determinando o Custo de Capital | CAPM, pesos a mercado e WACC |
| Cap. 13 — Levantando Capital Social | Contexto do financiamento por capital próprio |
| Cap. 14 — Financiamento por Dívida | Contexto da fonte de recursos de terceiros |
| Cap. 15 — Estrutura de Capital | Benefício fiscal e risco da alavancagem |
| WACC.html | Referência da turma para CAPM, Kd por spread e ponderação E/D |

A aplicação tem escopo menor que o exemplo do professor: não estima volatilidade,
não gera curvas de sensibilidade e não procura uma estrutura ótima.

O WACC não é uma prestação nem o lucro esperado. É o custo médio exigido pelos
financiadores. Para avaliar um projeto ainda seriam necessários seus fluxos de
caixa, com risco e estrutura de capital compatíveis. A alíquota de 30% é uma
hipótese didática, sem representar um regime tributário brasileiro específico.

## Roteiro curto para demonstrar

1. Execute `python wacc.py --exemplo` e confira o WACC de 13,96%.
2. Abra `relatorio_wacc.txt` e mostre entradas, fórmulas e interpretação.
3. Execute `python wacc.py` e escolha `s` para demonstrar a captura do BCB.
4. Explique: "Mais dívida pode aumentar o risco dos acionistas e os juros do
   crédito. Nosso cálculo avalia uma estrutura informada; não afirma que mais
   dívida sempre reduz o custo de capital."

Para testar os cálculos e o tratamento da resposta da API:

```bash
python -m unittest -v
```

Os testes da captura usam resposta simulada. A consulta real depende da internet
e da disponibilidade do Banco Central.

Fonte oficial: https://dadosabertos.bcb.gov.br/dataset/432-taxa-de-juros---meta-selic-definida-pelo-copom

Materiais da turma: https://virtual.ufmg.br/20262/course/view.php?id=11631
