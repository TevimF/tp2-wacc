"""Trabalho 2 — Administração Financeira/UFMG, 2026/2.

Tema: Estrutura de Capital. Exemplo: financiamento de uma frota.
Autores: Estêvão Felipe da Fonseca e João Marcos de Sousa Rezende.

Executar: python wacc.py
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
URL_SELIC = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"


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
    if referencia.date() > datetime.now().date():
        raise ValueError("A data retornada é futura. Confira o relógio e informe a taxa manualmente.")
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


def gerar_relatorio(entradas, resultado, fonte):
    """Produz um relatório reprodutível com entradas, fórmulas e conclusões."""
    e, r = entradas, resultado
    return f"""TRABALHO 2 — ESTRUTURA DE CAPITAL: FINANCIAMENTO DE UMA FROTA
Administração Financeira — UFMG — 2026/2
Estêvão Felipe da Fonseca e João Marcos de Sousa Rezende
Gerado em: {datetime.now().astimezone().isoformat(timespec='seconds')}

1. PROBLEMA PRÁTICO
Uma empresa pretende financiar uma frota com recursos próprios e dívida.
Qual é o custo médio anual dessas fontes de financiamento?
Os valores abaixo são premissas de um exemplo, não dados de uma empresa real.

2. DADOS DE ENTRADA
Capital próprio (E), a valor de mercado: R$ {e['capital_proprio']:,.2f}
Dívida (D), a valor de mercado: R$ {e['divida']:,.2f}
Taxa livre de risco de referência: {e['livre_risco']:.2f}% a.a.
Prêmio de risco de mercado: {e['premio']:.2f} pontos percentuais a.a.
Beta das ações: {e['beta']:.2f}
Spread de crédito: {e['spread']:.2f} pontos percentuais a.a.
Alíquota corporativa assumida: {e['imposto']:.2f}%
Fonte da taxa de referência: {fonte}
Demais entradas: premissas informadas pelo usuário/exemplo didático.

3. METODOLOGIA E RESULTADOS
Ke = Rf + beta × prêmio de risco = {r['ke']:.2%} a.a.
Kd = Rf + spread = {r['kd']:.2%} a.a.
Kd após impostos = Kd × (1 - T) = {r['kd_liquido']:.2%} a.a.
Peso do capital próprio = E / (E + D) = {r['peso_e']:.2%}
Peso da dívida = D / (E + D) = {r['peso_d']:.2%}
WACC = peso E × Ke + peso D × Kd × (1 - T)
WACC COM IMPOSTOS = {r['wacc']:.2%} a.a.
Média ponderada sem o ajuste fiscal, mantendo Ke e Kd = {r['sem_imposto']:.2%} a.a.
Efeito isolado do ajuste fiscal = {(r['sem_imposto'] - r['wacc']) * 100:.2f} pontos percentuais.

4. INTERPRETAÇÃO
O custo médio estimado das fontes de financiamento é {r['wacc']:.2%} ao ano.
O custo do capital próprio representa a remuneração exigida pelos acionistas;
ele não é um pagamento contratual de juros. O WACC pode servir de taxa de
desconto para fluxos de caixa livres de projetos com risco compatível com a
empresa e estrutura de capital estável, conforme o capítulo 12.

5. HIPÓTESES E LIMITAÇÕES
- Todas as taxas são nominais, anuais e em reais.
- A Selic, quando capturada, é apenas uma aproximação didática de Rf.
- Beta, prêmio, spread e alíquota são hipóteses editáveis, não estimativas oficiais.
- Kd = Rf + spread é uma simplificação; o custo real depende do novo crédito.
- O benefício fiscal pressupõe juros dedutíveis e lucro tributável suficiente.
  A alíquota é informada para simulação, sem modelar um regime tributário real.
- O comparativo sem ajuste fiscal isola apenas esse efeito nas taxas informadas.
  Não simula um novo equilíbrio de mercado de Modigliani e Miller.
- Mais dívida pode elevar beta, spread e risco de dificuldades financeiras.
  Este cálculo NÃO identifica uma estrutura de capital ótima e NÃO demonstra
  que aumentar a dívida sempre é melhor (capítulo 15).
- Não há fluxos de caixa do projeto: o WACC sozinho não decide sua viabilidade.

6. REFERÊNCIAS
Materiais disponibilizados pelo professor Bruno Pérez Ferreira no Moodle:
Berk, DeMarzo e Harford, Fundamentos de Finanças Empresariais,
capítulo 12 (Custo de Capital), capítulo 14 (Financiamento por Dívida) e
capítulo 15 (Estrutura de Capital); exemplo da turma: WACC.html.
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
    fonte = "Valor fictício didático de 10% a.a.; não representa a Selic atual."
    print("\nTRABALHO 2 — CUSTO DE CAPITAL DA FROTA\n")
    if not args.exemplo:
        print("Pressione Enter para usar o exemplo. Valores sem separador de milhar.")
        entradas['capital_proprio'] = ler_numero("Capital próprio a valor de mercado (R$)", 300000)
        entradas['divida'] = ler_numero("Dívida a valor de mercado (R$)", 200000)
        if input("Buscar Meta Selic no Banco Central? [s/N]: ").strip().lower() == 's':
            try:
                entradas['livre_risco'], fonte = buscar_selic()
                print(f"Taxa capturada: {entradas['livre_risco']:.2f}% a.a.\n{fonte}")
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

    try:
        resultado = calcular(**entradas)
        relatorio = gerar_relatorio(entradas, resultado, fonte)
        Path(args.saida).write_text(relatorio, encoding="utf-8")
    except (ValueError, OSError) as erro:
        parser.exit(1, f"Erro: {erro}\n")
    print(f"Ke: {resultado['ke']:.2%} | Kd: {resultado['kd']:.2%}")
    print(f"WACC: {resultado['wacc']:.2%} ao ano")
    print(f"Relatório salvo em: {Path(args.saida).resolve()}")


if __name__ == '__main__':
    main()
