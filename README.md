# Trabalho 2 — Custo de capital da frota

Administração Financeira (CAD 167), UFMG, 2026/2. Professor Bruno Pérez Ferreira.
Dupla: Estêvão Felipe da Fonseca e João Marcos de Sousa Rezende.

## Objetivo

Responder **como financiar uma frota** combinando capital próprio e dívida. A
aplicação calcula o custo médio ponderado de capital (WACC) da estrutura
informada e a **curva de estrutura de capital**: o WACC para cada proporção de
dívida de 0% a 80%, indicando a de menor custo sob as premissas. O tema
escolhido é **Estrutura de Capital**, previsto no enunciado do Trabalho 2.

Mantém o contexto da frota do Trabalho 1, mas aborda outro conteúdo: o custo das
fontes de financiamento. Não é necessário instalar nem executar o projeto anterior.

## Como executar

Requer Python 3.10 ou superior. **Não é preciso instalar pacotes** (nada de `pip`):
usa apenas a biblioteca padrão. Extraia o ZIP, abra o terminal na pasta e execute:

```bash
python main.py
```

No Linux, o comando pode ser `python3`; no Windows, pode ser `py`.

Abre uma janela (Tkinter) já preenchida com um exemplo fictício: a estrutura
informada (40% de dívida) tem WACC de **13,96% a.a.**, e o menor WACC da curva
é **13,91% a.a. com 49% de dívida**. Para usar:

1. Edite as premissas à esquerda (aceita `1,2` ou `1.2`, sem separador de milhar).
2. Opcional: clique em **Buscar Meta Selic (Banco Central)** para capturar a taxa
   oficial; a data e a fonte aparecem no rodapé e no relatório.
3. Clique em **Calcular WACC** (ou tecle Enter).
4. Clique em **Salvar relatório TXT** e escolha onde gravar.

À direita aparecem a proporção de dívida de menor WACC, a comparação com a
estrutura informada e o gráfico da curva (ponto laranja: informada; ponto azul:
menor WACC). Mude a **sensibilidade do spread** para ver o mínimo se deslocar;
com 0, o WACC cai sempre com a dívida.

### Modo terminal (alternativo)

Se o Tkinter não estiver instalado (algumas distribuições Linux não o incluem) ou
não houver tela, `python main.py` passa automaticamente para o modo terminal.
Ele também pode ser chamado diretamente:

```bash
python wacc.py              # pergunta as premissas (Enter mantém o exemplo)
python wacc.py --exemplo    # exemplo fictício, sem internet nem digitação
python wacc.py --exemplo --saida meu_relatorio.txt
```

O modo terminal grava `relatorio_wacc.txt` na pasta atual (ou no nome indicado).

### Relatório de exemplo

[`relatorio_exemplo.txt`](relatorio_exemplo.txt) mostra o relatório gerado para o
exemplo fictício (`python wacc.py --exemplo --saida relatorio_exemplo.txt`).
Valores saem no padrão brasileiro: R$ 300.000,00 e 13,96%.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `main.py` | Ponto de entrada: abre a janela ou cai para o modo terminal |
| `interface.py` | Interface gráfica Tkinter |
| `wacc.py` | Cálculos (CAPM, Kd, WACC, curva com Hamada), captura da Selic, relatório e modo terminal |
| `test_wacc.py` | Testes automáticos dos cálculos, da curva, da captura e do relatório |
| `relatorio_exemplo.txt` | Relatório gerado para o exemplo fictício |

## Relação com os critérios de avaliação

| Critério do enunciado | Onde aparece |
|---|---|
| Execução da aplicação | `python main.py`: janela com entrada, cálculo, curva e gráfico |
| Captura de dados | Consulta opcional à API oficial do Banco Central, com data e fonte |
| Comentários no código | Docstrings e comentários em todos os arquivos (CAPM, Hamada, pesos, impostos, unidades, interface) |
| Geração de relatórios | TXT com entradas, metodologia, tabela da curva, interpretação e limitações |

Se a API estiver indisponível, o programa informa a falha e permite digitar a taxa.
Ele não apresenta os valores de exemplo como se tivessem sido capturados.

## Conferência manual do exemplo

Todos os valores são **fictícios**. A taxa de 10% não representa a Selic atual.

| Entrada | Valor |
|---|---:|
| Capital próprio (E) | R$ 300.000,00 |
| Dívida (D) | R$ 200.000,00 |
| Taxa livre de risco (Rf) | 10% a.a. |
| Prêmio de risco de mercado | 6 pontos percentuais a.a. |
| Beta | 1,2 |
| Spread de crédito | 3 pontos percentuais a.a. |
| Alíquota corporativa assumida | 30% |
| Sensibilidade do spread (curva) | 6 pontos percentuais |

- Ke = 10% + 1,2 × 6% = **17,20% a.a.**
- Kd = 10% + 3% = **13,00% a.a.**
- Kd após impostos = 13% × (1 − 0,30) = **9,10% a.a.**
- Peso E = 300.000 / 500.000 = **60%**; peso D = **40%**.
- WACC = 0,60 × 17,20% + 0,40 × 9,10% = **13,96% a.a.**

Prêmio de risco é Rm − Rf; não se deve informar o retorno total de mercado nesse
campo. Os pesos são valores de mercado, conforme o capítulo 12.

## Curva de estrutura de capital

Para cada proporção de dívida D/V = D/(D+E), de 0% a 80% em passos de 1 p.p.:

1. **Beta (Hamada):** o beta informado (1,2) vale para a estrutura informada
   (D/E = 200/300). Desalavanca-se: βU = 1,2 / [1 + 0,7 × 0,667] = **0,818**; e
   realavanca-se para cada D/E: β = βU × [1 + (1 − T) × D/E].
2. **Spread crescente:** spread = base + sensibilidade × (D/V)². Com sensibilidade
   6, a base é 3 − 6 × 0,40² = **2,04 p.p.**, de modo que em 40% de dívida o spread
   é exatamente o informado (3 p.p.) e a curva passa pelo WACC de 13,96%.
3. Ke, Kd e WACC como acima.

| D/V | Beta | Spread | WACC |
|---:|---:|---:|---:|
| 0% | 0,82 | 2,04 p.p. | 14,91% |
| 40% (informada) | 1,20 | 3,00 p.p. | 13,96% |
| **49% (menor WACC)** | 1,37 | 3,48 p.p. | **13,91%** |
| 80% | 3,11 | 5,88 p.p. | 14,62% |

Até 49%, o benefício fiscal dos juros pesa mais; depois, o spread crescente (que
representa o risco de dificuldades financeiras) pesa mais: é a teoria do
trade-off do capítulo 15. Com sensibilidade 0 (spread fixo), o WACC cai sempre
com a dívida, como em Modigliani-Miller com impostos: **o formato em U vem
inteiramente da regra do spread**, que é uma hipótese editável. Por isso o
resultado ilustra a teoria; não estima a estrutura ótima real de uma empresa.
A fórmula de Hamada supõe beta da dívida igual a zero, o que é uma simplificação
diante de um spread crescente.

## Ligação com os materiais da turma

Foram consultados o enunciado, os capítulos 12 a 15 e o exemplo `WACC.html`.

| Material | Uso no trabalho |
|---|---|
| Cap. 12 — Determinando o Custo de Capital | CAPM, pesos a mercado e WACC |
| Cap. 13 — Levantando Capital Social | Contexto do financiamento por capital próprio |
| Cap. 14 — Financiamento por Dívida | Contexto da fonte de recursos de terceiros |
| Cap. 15 — Estrutura de Capital | Benefício fiscal, risco da alavancagem e curva do WACC (trade-off) |
| WACC.html | Referência da turma para CAPM, Kd por spread e ponderação E/D |
| Hamada (1972), *Journal of Finance* 27(2) | Fórmula do beta realavancado |

A aplicação tem escopo menor que o exemplo do professor: não estima volatilidade
e a curva depende de uma regra de spread assumida, não de dados de crédito.

O WACC não é uma prestação nem o lucro esperado. É o custo médio exigido pelos
financiadores. Para avaliar um projeto ainda seriam necessários seus fluxos de
caixa, com risco e estrutura de capital compatíveis. A alíquota de 30% é uma
hipótese didática, sem representar um regime tributário brasileiro específico.

## Roteiro curto para demonstrar

1. Execute `python main.py`: a estrutura informada (40%) tem WACC de 13,96%, e o
   menor WACC da curva é 13,91% com 49% de dívida.
2. Mude a sensibilidade do spread para 0 e recalcule: o WACC cai sempre (MM com
   impostos) e o "ótimo" vai para 80%. Volte para 6: reaparece o U.
3. Clique em **Buscar Meta Selic** e depois em **Calcular WACC**.
4. Salve o relatório e mostre entradas, tabela da curva, fonte da taxa e
   interpretação.
5. Explique: "Mais dívida traz benefício fiscal, mas aumenta o risco dos
   acionistas e os juros do crédito. O ponto de menor WACC depende de quanto o
   spread sobe com a dívida; não afirmamos que mais dívida sempre é melhor."

## Testes

```bash
python -m unittest -v
```

Os testes da captura usam resposta simulada. A consulta real depende da internet
e da disponibilidade do Banco Central.

Fonte oficial: https://dadosabertos.bcb.gov.br/dataset/432-taxa-de-juros---meta-selic-definida-pelo-copom

Materiais da turma: https://virtual.ufmg.br/20262/course/view.php?id=11631
