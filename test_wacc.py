"""Valida os resultados financeiros e a captura sem depender de internet."""

import io
import json
import unittest
from unittest.mock import patch

from wacc import buscar_selic, calcular, gerar_relatorio


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
    def test_rejeita_data_futura(self, requisicao):
        requisicao.return_value = io.BytesIO(json.dumps([
            {'valor': '10', 'data': '31/12/2999'}]).encode())
        with self.assertRaises(ValueError):
            buscar_selic()

    def test_relatorio(self):
        entradas = dict(capital_proprio=300000, divida=200000, livre_risco=10,
                        premio=6, beta=1.2, spread=3, imposto=30)
        texto = gerar_relatorio(entradas, calcular(**entradas), 'Fonte de teste')
        self.assertIn('13.96%', texto)
        self.assertIn('Fonte de teste', texto)
        self.assertIn('NÃO identifica uma estrutura de capital ótima', texto)


if __name__ == '__main__':
    unittest.main()
