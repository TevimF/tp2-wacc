"""Trabalho 2 — Administração Financeira/UFMG, 2026/2.

Tema: Estrutura de Capital. Exemplo: financiamento de uma frota.
Autores: Estêvão Felipe da Fonseca e João Marcos de Sousa Rezende.

Calcula o WACC da estrutura informada e a curva de estrutura de capital:
o WACC para cada proporção de dívida de 0% a 80%, com beta realavancado
(Hamada) e spread crescente, indicando a estrutura de menor WACC.

Interface gráfica (principal): python main.py
Modo terminal: python wacc.py
Exemplo sem digitação e sem internet: python wacc.py --exemplo
Usa somente a biblioteca padrão do Python 3.10+.
"""

import argparse
import http.client
import json
import math
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen


# A série 432 do SGS informa a Meta Selic em percentual ao ano.
# Pede as 2 últimas observações (usa-se a mais recente, dados[-1]): em nov/2026
# o endereço ".../ultimos/1" passou a responder "304 Not Modified" a qualquer
# cliente (inclusive curl), enquanto ".../ultimos/2" responde normalmente.
URL_SELIC = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/2?formato=json"

# A curva vai de 0% a DIVIDA_MAXIMA% de dívida no capital total, de 1 em 1 p.p.
# Acima de ~80% o D/E explode (80% de dívida já é D/E = 4) e o modelo perde sentido.
DIVIDA_MAXIMA = 80

# Valor padrão da sensibilidade do spread (p.p. por unidade de (D/V)²).
# Com o exemplo do trabalho, produz uma curva em U com mínimo interno.
SENSIBILIDADE_PADRAO = 6


def numero_br(valor, casas=2):
    """Formata um número no padrão brasileiro: 300000 -> '300.000,00'.

    O Python formata no padrão americano (vírgula no milhar, ponto decimal).
    Troca-se os dois separadores usando um caractere provisório ("X").
    """
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def moeda(valor):
    """Formata valores em reais: 300000 -> 'R$ 300.000,00'."""
    return f"R$ {numero_br(valor)}"


def percentual(taxa, casas=2):
    """Converte uma taxa decimal em percentual brasileiro: 0.1396 -> '13,96%'."""
    return f"{numero_br(taxa * 100, casas)}%"


def calcular(capital_proprio, divida, livre_risco, premio, beta, spread, imposto):
    """Calcula CAPM e WACC; todas as taxas de entrada estão em % ao ano.

    Cap. 12: os pesos usam valores de mercado, e o CAPM estima Ke.
    Cap. 15: os juros dedutíveis reduzem o custo efetivo da dívida.
    Prêmio é o retorno de mercado esperado MENOS a taxa livre de risco.
    Spread é o acréscimo de juros de crédito sobre a taxa de referência.
    """
    valores = (capital_proprio, divida, livre_risco, premio, beta, spread, imposto)
    if any(not math.isfinite(v) or v < 0 for v in valores):
        raise ValueError("Informe apenas números finitos e não negativos.")
    if capital_proprio + divida <= 0:
        raise ValueError("A soma do capital próprio e da dívida deve ser positiva.")
    if imposto > 100:
        raise ValueError("O imposto deve estar entre 0% e 100%.")

    # Divide por 100 para converter percentuais em taxas decimais.
    rf, pm, s, t = livre_risco / 100, premio / 100, spread / 100, imposto / 100
    ke = rf + beta * pm                       # CAPM: Ke = Rf + beta × prêmio.
    kd = rf + s                               # Estimativa simplificada de Kd.
    total = capital_proprio + divida
    peso_e, peso_d = capital_proprio / total, divida / total
    kd_liquido = kd * (1 - t)                  # Supõe aproveitamento do benefício fiscal.
    wacc_sem_imposto = peso_e * ke + peso_d * kd
    wacc = peso_e * ke + peso_d * kd_liquido    # WACC com impostos corporativos.
    return dict(ke=ke, kd=kd, kd_liquido=kd_liquido, peso_e=peso_e,
                peso_d=peso_d, wacc=wacc, sem_imposto=wacc_sem_imposto)


def desalavancar_beta(beta, d_sobre_e, imposto):
    """Hamada: beta sem dívida βU = βL / [1 + (1 − T) × D/E]; imposto em %."""
    return beta / (1 + (1 - imposto / 100) * d_sobre_e)


def realavancar_beta(beta_u, d_sobre_e, imposto):
    """Hamada: beta com dívida βL = βU × [1 + (1 − T) × D/E]; imposto em %."""
    return beta_u * (1 + (1 - imposto / 100) * d_sobre_e)


def curva_estrutura(capital_proprio, divida, livre_risco, premio, beta, spread,
                    imposto, sensibilidade=SENSIBILIDADE_PADRAO):
    """Calcula o WACC para cada proporção de dívida D/(D+E) de 0% a 80%.

    Teoria do trade-off (cap. 15): mais dívida traz benefício fiscal dos juros,
    mas aumenta o risco dos acionistas e dos credores. O modelo representa isso:
    1. O beta informado corresponde à estrutura informada; ele é desalavancado
       (βU) e realavancado para cada D/E pela fórmula de Hamada.
    2. O spread cresce com a dívida: spread = base + sensibilidade × (D/V)².
       A base é calibrada para que, na estrutura informada, o spread seja o
       informado. Assim, a curva passa exatamente pelo WACC da seção principal.
    Sem aumento do spread (sensibilidade 0), o WACC cai continuamente com a
    dívida (MM com impostos); é o spread crescente que cria o formato em U.
    """
    calcular(capital_proprio, divida, livre_risco, premio, beta, spread, imposto)  # Mesmas validações.
    if capital_proprio <= 0:
        raise ValueError("Para desalavancar o beta, o capital próprio deve ser positivo.")
    if not math.isfinite(sensibilidade) or sensibilidade < 0:
        raise ValueError("A sensibilidade do spread deve ser um número não negativo.")

    rf, pm, t = livre_risco / 100, premio / 100, imposto / 100
    k = sensibilidade / 100                              # p.p. -> decimal.
    peso_d_atual = divida / (capital_proprio + divida)
    beta_u = desalavancar_beta(beta, divida / capital_proprio, imposto)
    spread_base = spread / 100 - k * peso_d_atual ** 2  # Calibração na estrutura informada.
    if spread_base < 0:
        raise ValueError(
            "Com essa sensibilidade, o spread ficaria negativo com pouca dívida "
            f"(base de {numero_br(spread_base * 100)} p.p.). Reduza a sensibilidade "
            "ou aumente o spread.")

    def ponto(peso_d):
        """WACC e componentes para uma proporção de dívida (decimal)."""
        d_sobre_e = peso_d / (1 - peso_d)
        beta_l = realavancar_beta(beta_u, d_sobre_e, imposto)
        ke = rf + beta_l * pm
        spread_w = spread_base + k * peso_d ** 2
        kd = rf + spread_w
        wacc = (1 - peso_d) * ke + peso_d * kd * (1 - t)
        return dict(peso_d=peso_d, beta=beta_l, ke=ke, spread=spread_w, kd=kd, wacc=wacc)

    # range com inteiros evita acumular erro de ponto flutuante (0,01 + 0,01 + ...).
    pontos = [ponto(i / 100) for i in range(DIVIDA_MAXIMA + 1)]
    otimo = min(pontos, key=lambda p: p["wacc"])  # Busca em passos de 1 p.p.
    return dict(beta_u=beta_u, spread_base=spread_base, sensibilidade=sensibilidade,
                total=capital_proprio + divida, pontos=pontos, otimo=otimo,
                atual=ponto(peso_d_atual))  # E > 0 garante peso_d_atual < 1.


def buscar_selic():
    """Captura a observação oficial, preservando data e endereço da fonte.

    A Selic é uma aproximação didática da taxa livre de risco em reais.
    Não equivale à taxa de um título com o mesmo prazo do projeto.
    """
    with urlopen(URL_SELIC, timeout=10) as resposta:
        dados = json.load(resposta)
    if not isinstance(dados, list) or not dados:
        raise ValueError("O Banco Central não retornou observações.")
    valor = float(dados[-1]["valor"])
    referencia = datetime.strptime(dados[-1]["data"], "%d/%m/%Y")
    # Preserva a referência publicada pela API, sem compará-la ao relógio local
    # ou ao cabeçalho HTTP (que pode vir de cache).
    data = referencia.strftime("%d/%m/%Y")
    if not math.isfinite(valor) or valor < 0:
        raise ValueError("O Banco Central retornou uma taxa inválida.")
    return valor, f"BCB/SGS, série 432; referência: {data}; URL: {URL_SELIC}"


def ler_numero(rotulo, padrao, maximo=None):
    """Lê uma premissa, aceita vírgula decimal e impede entradas inválidas."""
    while True:
        texto = input(f"{rotulo} [{padrao}]: ").strip()
        try:
            valor = float(texto.replace(",", ".")) if texto else float(padrao)
            if not math.isfinite(valor) or valor < 0 or (maximo is not None and valor > maximo):
                raise ValueError
            return valor
        except ValueError:
            print("Valor inválido. Use número não negativo, sem separador de milhar.")


def tabela_curva(curva):
    """Monta a tabela da curva em texto: linhas de 5 em 5 p.p. + informada + mínimo."""
    # Linhas a cada 5 p.p., mais a estrutura informada e a de menor WACC (se fora da grade).
    linhas = [p for p in curva["pontos"] if round(p["peso_d"] * 100) % 5 == 0]
    for extra in (curva["atual"], curva["otimo"]):
        if all(abs(extra["peso_d"] - p["peso_d"]) > 1e-9 for p in linhas):
            linhas.append(extra)
    linhas.sort(key=lambda p: p["peso_d"])

    texto = [f"{'D/(D+E)':>8} {'Dívida':>17} {'Beta':>6} {'Ke':>8} {'Spread':>10} {'Kd':>8} {'WACC':>8}"]
    for p in linhas:
        marca = ""
        if abs(p["peso_d"] - curva["atual"]["peso_d"]) < 1e-9:
            marca += "  <- informada"
        if abs(p["peso_d"] - curva["otimo"]["peso_d"]) < 1e-9:
            marca += "  <- menor WACC"
        texto.append(
            f"{percentual(p['peso_d'], 1):>8} {moeda(p['peso_d'] * curva['total']):>17} "
            f"{numero_br(p['beta']):>6} {percentual(p['ke']):>8} "
            f"{numero_br(p['spread'] * 100) + ' p.p.':>10} {percentual(p['kd']):>8} "
            f"{percentual(p['wacc']):>8}{marca}")
    return "\n".join(texto)


def gerar_relatorio(entradas, resultado, fonte, curva):
    """Produz um relatório reprodutível com entradas, fórmulas e conclusões.

    Valores monetários e taxas saem no padrão brasileiro (R$ 300.000,00; 13,96%).
    As entradas de taxa já estão em % (ex.: 10), por isso usam numero_br;
    os resultados de calcular() são decimais (ex.: 0.1396), por isso usam percentual.
    """
    e, r, c = entradas, resultado, curva
    p = percentual  # Abreviação para manter as linhas do relatório legíveis.
    otimo = c["otimo"]
    diferenca = (r["wacc"] - otimo["wacc"]) * 100
    return f"""TRABALHO 2 — ESTRUTURA DE CAPITAL: FINANCIAMENTO DE UMA FROTA
Administração Financeira — UFMG — 2026/2
Estêvão Felipe da Fonseca e João Marcos de Sousa Rezende
Gerado em: {datetime.now().astimezone().isoformat(timespec='seconds')}

1. PROBLEMA PRÁTICO
Uma empresa pretende financiar uma frota com recursos próprios e dívida.
Qual é o custo médio anual dessas fontes de financiamento, e como esse custo
muda conforme a proporção de dívida?
Os valores abaixo são premissas de um exemplo, não dados de uma empresa real.

2. DADOS DE ENTRADA
Capital próprio (E), a valor de mercado: {moeda(e['capital_proprio'])}
Dívida (D), a valor de mercado: {moeda(e['divida'])}
Taxa livre de risco de referência: {numero_br(e['livre_risco'])}% a.a.
Prêmio de risco de mercado: {numero_br(e['premio'])} pontos percentuais a.a.
Beta das ações (na estrutura informada): {numero_br(e['beta'])}
Spread de crédito (na estrutura informada): {numero_br(e['spread'])} pontos percentuais a.a.
Alíquota corporativa assumida: {numero_br(e['imposto'])}%
Sensibilidade do spread à alavancagem: {numero_br(c['sensibilidade'])} pontos percentuais
Fonte da taxa de referência: {fonte}
Demais entradas: premissas informadas pelo usuário/exemplo didático.

3. WACC DA ESTRUTURA INFORMADA
Ke = Rf + beta × prêmio de risco = {p(r['ke'])} a.a.
Kd = Rf + spread = {p(r['kd'])} a.a.
Kd após impostos = Kd × (1 - T) = {p(r['kd_liquido'])} a.a.
Peso do capital próprio = E / (E + D) = {p(r['peso_e'])}
Peso da dívida = D / (E + D) = {p(r['peso_d'])}
WACC = peso E × Ke + peso D × Kd × (1 - T)
WACC COM IMPOSTOS = {p(r['wacc'])} a.a.
Média ponderada sem o ajuste fiscal, mantendo Ke e Kd = {p(r['sem_imposto'])} a.a.
Efeito isolado do ajuste fiscal = {numero_br((r['sem_imposto'] - r['wacc']) * 100)} pontos percentuais.

4. CURVA DE ESTRUTURA DE CAPITAL
Beta desalavancado (Hamada): βU = βL / [1 + (1 - T) × D/E] = {numero_br(c['beta_u'], 3)}
Para cada proporção de dívida D/(D+E) de 0% a {DIVIDA_MAXIMA}%, em passos de 1 p.p.:
  beta realavancado = βU × [1 + (1 - T) × D/E]
  spread = base + sensibilidade × (D/(D+E))², com base = {numero_br(c['spread_base'] * 100)} p.p.
  (a base reproduz o spread informado na estrutura informada)
  Ke, Kd e WACC calculados como na seção 3.
Valores em R$ supõem o mesmo capital total: E + D = {moeda(c['total'])}.

{tabela_curva(c)}

Estrutura informada: {p(r['peso_d'], 1)} de dívida, WACC de {p(r['wacc'])} a.a.
MENOR WACC DA CURVA: {p(otimo['peso_d'], 0)} de dívida, WACC de {p(otimo['wacc'])} a.a.
Diferença em relação à estrutura informada: {numero_br(diferenca)} pontos percentuais.

5. INTERPRETAÇÃO
O custo médio estimado das fontes de financiamento é {p(r['wacc'])} ao ano.
O custo do capital próprio representa a remuneração exigida pelos acionistas;
ele não é um pagamento contratual de juros. O WACC pode servir de taxa de
desconto para fluxos de caixa livres de projetos com risco compatível com a
empresa e estrutura de capital estável, conforme o capítulo 12.

Sob estas premissas, a estrutura de menor WACC usa cerca de {p(otimo['peso_d'], 0)} de
dívida. Até esse ponto, o benefício fiscal dos juros pesa mais; depois dele, o
spread crescente, que representa o maior risco de dificuldades financeiras,
passa a pesar mais (teoria do trade-off, capítulo 15). Sem aumento do spread
(sensibilidade 0), o WACC cairia continuamente com a dívida, como no modelo de
Modigliani e Miller com impostos. Perto do mínimo a curva costuma ser achatada:
estruturas vizinhas têm custos muito parecidos.

6. HIPÓTESES E LIMITAÇÕES
- Todas as taxas são nominais, anuais e em reais.
- A Selic, quando capturada, é apenas uma aproximação didática de Rf.
- Beta, prêmio, spread, sensibilidade e alíquota são hipóteses editáveis, não
  estimativas oficiais.
- Kd = Rf + spread é uma simplificação; o custo real depende do novo crédito.
- O benefício fiscal pressupõe juros dedutíveis e lucro tributável suficiente
  em todos os níveis de dívida. A alíquota é informada para simulação, sem
  modelar um regime tributário real.
- O comparativo sem ajuste fiscal isola apenas esse efeito nas taxas informadas.
- A fórmula de Hamada supõe beta da dívida igual a zero, enquanto o spread
  crescente supõe que a dívida fica mais arriscada: é uma simplificação comum
  em exemplos didáticos.
- A regra do spread (quadrática) é uma hipótese. A estrutura de menor WACC
  depende inteiramente dela: não é uma estimativa da estrutura ótima real da
  empresa. Custos de dificuldades financeiras além do spread (perda de clientes,
  custos de agência) não são modelados.
- Este cálculo NÃO demonstra que aumentar a dívida sempre é melhor (capítulo 15).
- Não há fluxos de caixa do projeto: o WACC sozinho não decide sua viabilidade.

7. REFERÊNCIAS
Materiais disponibilizados pelo professor Bruno Pérez Ferreira no Moodle:
Berk, DeMarzo e Harford, Fundamentos de Finanças Empresariais,
capítulo 12 (Custo de Capital), capítulo 14 (Financiamento por Dívida) e
capítulo 15 (Estrutura de Capital); exemplo da turma: WACC.html.
Hamada, R. S. (1972). The Effect of the Firm's Capital Structure on the
Systematic Risk of Common Stocks. Journal of Finance, 27(2), 435-452.
Fonte de dados: Banco Central, SGS, série 432 (Meta Selic):
https://dadosabertos.bcb.gov.br/dataset/432-taxa-de-juros---meta-selic-definida-pelo-copom
"""


def main():
    """Coordena captura de dados, cálculo e gravação do relatório em texto."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exemplo", action="store_true", help="executa um caso fictício offline")
    parser.add_argument("--saida", default="relatorio_wacc.txt", help="caminho do relatório TXT")
    args = parser.parse_args()

    # Valores fictícios permitem ao docente testar mesmo sem conexão à internet.
    entradas = dict(capital_proprio=300000, divida=200000, livre_risco=10,
                    premio=6, beta=1.2, spread=3, imposto=30)
    sensibilidade = SENSIBILIDADE_PADRAO
    fonte = "Valor fictício didático de 10% a.a.; não representa a Selic atual."
    print("\nTRABALHO 2 — CUSTO DE CAPITAL DA FROTA\n")
    if not args.exemplo:
        print("Pressione Enter para usar o exemplo. Valores sem separador de milhar.")
        entradas['capital_proprio'] = ler_numero("Capital próprio a valor de mercado (R$)", 300000)
        entradas['divida'] = ler_numero("Dívida a valor de mercado (R$)", 200000)
        if input("Buscar Meta Selic no Banco Central? [s/N]: ").strip().lower() == 's':
            try:
                entradas['livre_risco'], fonte = buscar_selic()
                print(f"Taxa capturada: {numero_br(entradas['livre_risco'])}% a.a.\n{fonte}")
            except (OSError, http.client.HTTPException, ValueError, KeyError, TypeError, UnicodeError) as erro:
                print(f"Não foi possível capturar a taxa: {erro}")
                print("Continuaremos com a entrada manual.")
                entradas['livre_risco'] = ler_numero("Taxa de referência (% a.a.)", 10)
                fonte = "Entrada manual do usuário; sem captura externa confirmada."
        else:
            entradas['livre_risco'] = ler_numero("Taxa de referência (% a.a.)", 10)
            fonte = "Entrada manual do usuário; sem captura externa confirmada."
        entradas['premio'] = ler_numero("Prêmio de risco de mercado (p.p. a.a.)", 6)
        entradas['beta'] = ler_numero("Beta das ações", 1.2)
        entradas['spread'] = ler_numero("Spread de crédito (p.p. a.a.)", 3)
        entradas['imposto'] = ler_numero("Alíquota corporativa assumida (%)", 30, 100)
        sensibilidade = ler_numero("Sensibilidade do spread à alavancagem (p.p.)", SENSIBILIDADE_PADRAO)

    try:
        resultado = calcular(**entradas)
        curva = curva_estrutura(**entradas, sensibilidade=sensibilidade)
        relatorio = gerar_relatorio(entradas, resultado, fonte, curva)
        Path(args.saida).write_text(relatorio, encoding="utf-8")
    except (ValueError, OSError) as erro:
        parser.exit(1, f"Erro: {erro}\n")
    otimo = curva["otimo"]
    print(f"Ke: {percentual(resultado['ke'])} | Kd: {percentual(resultado['kd'])}")
    print(f"WACC da estrutura informada ({percentual(resultado['peso_d'], 1)} de dívida): "
          f"{percentual(resultado['wacc'])} ao ano")
    print(f"Menor WACC da curva: {percentual(otimo['wacc'])} ao ano com "
          f"{percentual(otimo['peso_d'], 0)} de dívida")
    print(f"Relatório salvo em: {Path(args.saida).resolve()}")


if __name__ == '__main__':
    main()
