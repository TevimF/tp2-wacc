# TP2 — Custo de capital da frota

Aplicação de Administração Financeira (UFMG, 2026/2), sobre estrutura de capital.
Calcula CAPM, custo da dívida e WACC, com captura opcional da Meta Selic no Banco Central e relatório em TXT.

## Executar

Requer Python 3.10 ou superior. Não utiliza pacotes externos.

```powershell
python wacc.py --exemplo
python wacc.py
```

O primeiro comando executa um exemplo fictício offline (WACC de 13,96% a.a.).
O segundo permite informar premissas e consultar a Selic. Ambos geram `relatorio_wacc.txt`.

## Testar

```powershell
python -m unittest -v
```

Veja [LEIA_ME.md](LEIA_ME.md) para fórmulas, hipóteses, limitações e roteiro de demonstração.
