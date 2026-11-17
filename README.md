# TP2 — Custo de capital da frota

Aplicação de Administração Financeira (UFMG, 2026/2), sobre estrutura de capital.
Calcula CAPM, custo da dívida e WACC, com captura opcional da Meta Selic no Banco Central e relatório em TXT.

## Executar

Requer Python 3.10 ou superior. Não utiliza pacotes externos.

```powershell
python main.py
```

A janela usa Tkinter, como no TP1. Já abre com um exemplo fictício (WACC de
13,96% a.a.). Edite as premissas, clique em **Calcular WACC** e use **Salvar
relatório TXT** para escolher onde salvar. A barra mostra a composição do capital.
A busca da Selic é opcional; sua data e fonte aparecem no relatório.

O modo de terminal continua disponível com `python wacc.py` ou
`python wacc.py --exemplo`. Não é necessário instalar pacotes com pip.

## Testar

```powershell
python -m unittest -v
```

Veja [LEIA_ME.md](LEIA_ME.md) para fórmulas, hipóteses, limitações e roteiro de demonstração.
