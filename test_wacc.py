"""Valida os resultados financeiros e a captura sem depender de internet."""

import io
import json
import unittest
from unittest.mock import patch

from wacc import (buscar_selic, calcular, curva_estrutura, desalavancar_beta,
                  gerar_relatorio, moeda, numero_br, percentual, realavancar_beta)

# Exemplo do trabalho, usado em vários testes.
EXEMPLO = dict(capital_proprio=300000, divida=200000, livre_risco=10,
               premio=6, beta=1.2, spread=3, imposto=30)


class TestWacc(unittest.TestCase):
    """Os resultados esperados podem ser conferidos à mão."""

    def test_exemplo(self):
        # Ke = 10 + 1,2×6 = 17,2%; Kd = 13%; WACC = 0,6×17,2 + 0,4×9,1.
        r = calcular(300000, 200000, 10, 6, 1.2, 3, 30)
        self.assertAlmostEqual(r['ke'], .172)
        self.assertAlmostEqual(r['kd_liquido'], .091)
        self.assertAlmostEqual(r['wacc'], .1396)
        self.assertAlmostEqual(r['sem_imposto'], .1552)

    def test_sem_divida(self):
        # Sem dívida o custo total é exatamente o custo de capital próprio.
        r = calcular(500000, 0, 10, 6, 1.2, 3, 30)
        self.assertAlmostEqual(r['wacc'], r['ke'])

    def test_sem_imposto(self):
        r = calcular(300000, 200000, 10, 6, 1.2, 3, 0)
        self.assertAlmostEqual(r['wacc'], r['sem_imposto'])

    def test_entradas_invalidas(self):
        for dados in [(0, 0, 10, 6, 1.2, 3, 30),
                      (300000, -1, 10, 6, 1.2, 3, 30),
                      (300000, 200000, float('nan'), 6, 1.2, 3, 30),
                      (300000, 200000, 10, 6, 1.2, 3, 101)]:
            with self.subTest(dados=dados), self.assertRaises(ValueError):
                calcular(*dados)

    @patch('wacc.urlopen')
    def test_captura_preserva_data(self, requisicao):
        # Uma resposta simulada testa conversão, unidade e rastreabilidade da fonte.
        requisicao.return_value = io.BytesIO(json.dumps([
            {'valor': '12.50', 'data': '10/11/2026'}]).encode())
        taxa, fonte = buscar_selic()
        self.assertEqual(taxa, 12.5)
        self.assertIn('10/11/2026', fonte)
        self.assertIn('432', fonte)

    @patch('wacc.urlopen', return_value=io.BytesIO(b'[]'))
    def test_captura_vazia(self, _):
        with self.assertRaises(ValueError):
            buscar_selic()

    @patch('wacc.urlopen')
    def test_preserva_referencia_posterior_ao_cabecalho(self, requisicao):
        requisicao.return_value = io.BytesIO(json.dumps([
            {'valor': '10', 'data': '31/12/2999'}]).encode())
        requisicao.return_value.headers = {'Date': 'Tue, 17 Nov 2026 15:00:00 GMT'}
        self.assertIn('31/12/2999', buscar_selic()[1])

    @patch('wacc.urlopen')
    def test_captura_independe_do_relogio_local(self, requisicao):
        requisicao.return_value = io.BytesIO(json.dumps([
            {'valor': '12.50', 'data': '17/11/2026'}]).encode())
        requisicao.return_value.headers = {'Date': 'Tue, 17 Nov 2026 15:00:00 GMT'}
        with patch('wacc.datetime', wraps=__import__('datetime').datetime) as relogio:
            relogio.now.side_effect = AssertionError('Não deve consultar o relógio local')
            self.assertEqual(buscar_selic()[0], 12.5)

    def test_relatorio(self):
        texto = gerar_relatorio(EXEMPLO, calcular(**EXEMPLO), 'Fonte de teste',
                                curva_estrutura(**EXEMPLO))
        # Formato brasileiro: vírgula decimal e ponto no milhar.
        self.assertIn('13,96%', texto)
        self.assertIn('R$ 300.000,00', texto)
        self.assertNotIn('13.96%', texto)
        self.assertIn('Fonte de teste', texto)
        self.assertIn('NÃO demonstra que aumentar a dívida sempre é melhor', texto)
        self.assertIn('MENOR WACC DA CURVA: 49% de dívida, WACC de 13,91% a.a.', texto)
        self.assertIn('<- informada', texto)
        self.assertIn('Hamada', texto)

    def test_formato_brasileiro(self):
        self.assertEqual(moeda(1234567.891), 'R$ 1.234.567,89')
        self.assertEqual(percentual(0.1396), '13,96%')
        self.assertEqual(numero_br(1.2), '1,20')



class TestCurva(unittest.TestCase):
    """Curva de estrutura de capital: Hamada + spread crescente."""

    def test_hamada_ida_e_volta(self):
        # Desalavancar e realavancar no mesmo D/E devolve o beta original.
        beta_u = desalavancar_beta(1.2, 200000 / 300000, 30)
        self.assertAlmostEqual(beta_u, 1.2 / (1 + 0.7 * 2 / 3))
        self.assertAlmostEqual(realavancar_beta(beta_u, 200000 / 300000, 30), 1.2)

    def test_curva_passa_pela_estrutura_informada(self):
        # Na estrutura informada, beta, spread e WACC coincidem com calcular().
        curva = curva_estrutura(**EXEMPLO, sensibilidade=6)
        atual = curva['atual']
        self.assertAlmostEqual(atual['peso_d'], 0.4)
        self.assertAlmostEqual(atual['beta'], 1.2)
        self.assertAlmostEqual(atual['spread'], 0.03)
        self.assertAlmostEqual(atual['wacc'], calcular(**EXEMPLO)['wacc'])
        # O ponto de 40% da grade é o mesmo ponto.
        self.assertAlmostEqual(curva['pontos'][40]['wacc'], atual['wacc'])

    def test_spread_fixo_wacc_sempre_cai(self):
        # Sem aumento do spread vale MM com impostos: o WACC cai com a dívida.
        curva = curva_estrutura(**EXEMPLO, sensibilidade=0)
        waccs = [p['wacc'] for p in curva['pontos']]
        self.assertTrue(all(a > b for a, b in zip(waccs, waccs[1:])))
        self.assertAlmostEqual(curva['otimo']['peso_d'], 0.80)

    def test_spread_crescente_gera_u(self):
        # Com spread crescente há mínimo interno: a curva desce e depois sobe.
        curva = curva_estrutura(**EXEMPLO, sensibilidade=6)
        otimo, pontos = curva['otimo'], curva['pontos']
        self.assertAlmostEqual(otimo['peso_d'], 0.49)
        self.assertAlmostEqual(otimo['wacc'], 0.13911, places=4)
        self.assertGreater(pontos[0]['wacc'], otimo['wacc'])
        self.assertGreater(pontos[-1]['wacc'], otimo['wacc'])

    def test_curva_tem_81_pontos(self):
        curva = curva_estrutura(**EXEMPLO)
        self.assertEqual(len(curva['pontos']), 81)
        self.assertAlmostEqual(curva['pontos'][-1]['peso_d'], 0.80)

    def test_curva_entradas_invalidas(self):
        casos = [dict(EXEMPLO, capital_proprio=0),          # Não dá para desalavancar.
                 dict(EXEMPLO, sensibilidade=-1),           # Sensibilidade negativa.
                 dict(EXEMPLO, sensibilidade=30),           # Spread base negativo.
                 dict(EXEMPLO, imposto=101)]                # Validação de calcular().
        for dados in casos:
            with self.subTest(dados=dados), self.assertRaises(ValueError):
                curva_estrutura(**dados)


if __name__ == '__main__':
    unittest.main()
