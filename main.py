"""Ponto de entrada do Trabalho 2: abre a interface gráfica (Tkinter).

Se o Tkinter não estiver disponível (algumas instalações Linux não o incluem)
ou não houver tela (ex.: servidor sem interface gráfica), cai para o modo
terminal de wacc.py, que oferece o mesmo cálculo e o mesmo relatório.
"""
import sys


def principal():
    """Tenta abrir a janela; em caso de falha, usa o modo terminal."""
    try:
        from interface import main as abrir_janela  # Importa tkinter internamente.
    except ImportError as erro:
        print(f"Interface gráfica indisponível ({erro}). Usando o modo terminal.\n", file=sys.stderr)
    else:
        try:
            abrir_janela()
            return
        except Exception as erro:  # tkinter.TclError quando não há tela disponível.
            if type(erro).__name__ != "TclError":
                raise
            print(f"Não foi possível abrir a janela ({erro}). Usando o modo terminal.\n", file=sys.stderr)
    from wacc import main as modo_terminal
    modo_terminal()


if __name__ == "__main__":
    principal()
