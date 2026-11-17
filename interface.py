"""Interface Tkinter: entrada de premissas, cálculo e relatório do WACC."""
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from wacc import buscar_selic, calcular, gerar_relatorio


def percentual(valor):
    return f"{valor * 100:.2f}%".replace(".", ",")


class Aplicacao:
    def __init__(self, root):
        self.root = root
        root.title("TP2 — Custo de capital da frota")
        root.geometry("1000x740")
        root.minsize(940, 700)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)
        ttk.Label(root, text="Como financiar a frota?", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(16, 8))
        esquerda = ttk.Frame(root, padding=(18, 0, 8, 12))
        esquerda.grid(row=1, column=0, sticky="nsew")
        direita = ttk.LabelFrame(root, text="Resultados", padding=16)
        direita.grid(row=1, column=1, sticky="nsew", padx=(8, 18), pady=(0, 12))
        direita.columnconfigure(0, weight=1)
        self.campos = {}
        self.fonte = "Exemplo fictício de 10% a.a.; não representa a Selic atual."
        self.taxa_capturada = None
        self.relatorio = None
        self.status = tk.StringVar(value="Exemplo fictício carregado. Edite os valores para simular.")
        secoes = [
            ("1. Fontes de financiamento", [
                ("capital_proprio", "Capital próprio (R$)", "300000", "Valor de mercado dos recursos dos sócios."),
                ("divida", "Dívida (R$)", "200000", "Valor de mercado dos recursos de terceiros.")]),
            ("2. Taxas e premissas", [
                ("livre_risco", "Taxa de referência (% a.a.)", "10", "Pode ser preenchida com a Meta Selic."),
                ("premio", "Prêmio de mercado (p.p. a.a.)", "6", "Retorno esperado do mercado menos a taxa livre de risco."),
                ("beta", "Beta", "1,2", "Sensibilidade das ações ao risco do mercado."),
                ("spread", "Spread da dívida (p.p. a.a.)", "3", "Acréscimo de juros sobre a taxa de referência."),
                ("imposto", "Alíquota assumida (%)", "30", "Hipótese de benefício fiscal sobre os juros.")])]
        for titulo, campos in secoes:
            quadro = ttk.LabelFrame(esquerda, text=titulo, padding=10)
            quadro.pack(fill="x", pady=(0, 10))
            quadro.columnconfigure(0, weight=1)
            for linha, (chave, rotulo, padrao, ajuda) in enumerate(campos):
                ttk.Label(quadro, text=rotulo).grid(row=linha*2, column=0, sticky="w")
                variavel = tk.StringVar(value=padrao)
                campo = ttk.Entry(quadro, textvariable=variavel, width=16)
                campo.grid(row=linha*2, column=1, padx=(8, 0), sticky="e")
                ttk.Label(quadro, text=ajuda, wraplength=390, foreground="#555555").grid(
                    row=linha*2+1, column=0, columnspan=2, sticky="w", pady=(2, 8))
                self.campos[chave] = variavel
                variavel.trace_add("write", self.invalidar)
        self.botao_busca = ttk.Button(esquerda, text="Buscar Meta Selic (Banco Central)", command=self.buscar)
        self.botao_busca.pack(fill="x")
        ttk.Label(esquerda, text="Use vírgula ou ponto decimal, sem separador de milhar.", wraplength=420).pack(anchor="w", pady=8)
        ttk.Button(esquerda, text="Calcular WACC", command=self.calcular).pack(fill="x")
        self.destaque = ttk.Label(direita, font=("Segoe UI", 25, "bold"))
        self.destaque.grid(row=0, column=0, sticky="w", pady=(0, 12))
        self.detalhes = ttk.Label(direita, justify="left", font=("Segoe UI", 11))
        self.detalhes.grid(row=1, column=0, sticky="w", pady=8)
        self.barra = tk.Canvas(direita, height=58, highlightthickness=0)
        self.barra.grid(row=2, column=0, sticky="ew", pady=12)
        self.barra.bind("<Configure>", lambda event: self.desenhar())
        self.resultado = None
        self.explicacao = ttk.Label(direita, wraplength=390, justify="left")
        self.explicacao.grid(row=3, column=0, sticky="nw", pady=8)
        ttk.Label(direita, text="Ke = Rf + beta × prêmio\nKd = Rf + spread\nWACC = peso E × Ke + peso D × Kd × (1 − T)",
                  wraplength=390, justify="left").grid(row=4, column=0, sticky="w", pady=14)
        self.exportar = ttk.Button(direita, text="Salvar relatório TXT", command=self.salvar)
        self.exportar.grid(row=5, column=0, sticky="ew")
        ttk.Label(root, textvariable=self.status, wraplength=940).grid(row=2, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 12))
        root.bind("<Return>", lambda event: self.calcular())
        self.calcular()

    def invalidar(self, *_):
        """Evita exportar resultados antigos depois de editar uma premissa."""
        self.relatorio = None
        if hasattr(self, "exportar"):
            self.exportar.state(["disabled"])
            self.status.set("Dados alterados. Clique em Calcular WACC para atualizar.")
            self.destaque.config(text="Recalcule o WACC")

    def calcular(self):
        try:
            entradas = {}
            for chave, campo in self.campos.items():
                try:
                    entradas[chave] = float(campo.get().strip().replace(",", "."))
                except ValueError:
                    raise ValueError("Preencha todos os campos com números válidos, sem separador de milhar.") from None
            r = calcular(**entradas)
        except ValueError as erro:
            messagebox.showerror("Confira os dados", str(erro), parent=self.root)
            return
        fonte = self.fonte if entradas["livre_risco"] == self.taxa_capturada else "Taxa informada pelo usuário; demais valores são premissas da simulação."
        if self.taxa_capturada is None and entradas["livre_risco"] == 10:
            fonte = "Taxa de 10% informada/exemplo didático; não representa a Selic atual."
        self.relatorio = gerar_relatorio(entradas, r, fonte)
        self.resultado = r
        self.destaque.config(text=f"{percentual(r['wacc'])} a.a.")
        self.detalhes.config(text=(f"Custo do capital próprio (Ke): {percentual(r['ke'])}\n\n"
            f"Custo da dívida (Kd): {percentual(r['kd'])}\n"
            f"Dívida após impostos: {percentual(r['kd_liquido'])}\n\n"
            f"Média sem ajuste fiscal: {percentual(r['sem_imposto'])}\n"
            f"Efeito fiscal: {(r['sem_imposto']-r['wacc'])*100:.2f} p.p.".replace(".", ",")))
        self.explicacao.config(text=f"O custo médio estimado das fontes é {percentual(r['wacc'])} ao ano.\n\n"
            "O cálculo considera a composição informada. Mais dívida pode aumentar o risco e os juros; esta simulação não determina a estrutura ótima.")
        self.desenhar()
        self.exportar.state(["!disabled"])
        self.status.set("Cálculo atualizado. " + fonte)

    def desenhar(self):
        """Mostra os pesos das duas fontes em uma barra simples."""
        self.barra.delete("all")
        if not self.resultado:
            return
        r = self.resultado
        largura = max(1, self.barra.winfo_width())
        divisao = largura * r["peso_e"]
        self.barra.create_rectangle(0, 0, divisao, 22, fill="#3568a8", width=0)
        self.barra.create_rectangle(divisao, 0, largura, 22, fill="#df9841", width=0)
        self.barra.create_text(0, 40, anchor="w", text=f"Próprio: {percentual(r['peso_e'])}", fill="#3568a8")
        self.barra.create_text(largura, 40, anchor="e", text=f"Dívida: {percentual(r['peso_d'])}", fill="#98601d")

    def buscar(self):
        """Consulta em outra thread; somente a thread principal modifica a janela."""
        self.botao_busca.state(["disabled"])
        self.status.set("Consultando o Banco Central...")
        retorno = queue.Queue()

        def trabalhar():
            try:
                retorno.put((True, buscar_selic()))
            except Exception as erro:
                retorno.put((False, str(erro)))

        def concluir():
            try:
                sucesso, valor = retorno.get_nowait()
            except queue.Empty:
                self.root.after(100, concluir)
                return
            self.botao_busca.state(["!disabled"])
            if sucesso:
                self.taxa_capturada, self.fonte = valor
                self.campos["livre_risco"].set(str(self.taxa_capturada).replace(".", ","))
                self.status.set(self.fonte + " — Clique em Calcular WACC.")
            else:
                self.status.set("Consulta indisponível. Informe a taxa manualmente.")
                messagebox.showwarning("Banco Central", f"Não foi possível buscar a Selic.\n{valor}\n\nVocê pode informar a taxa manualmente.", parent=self.root)
        threading.Thread(target=trabalhar, daemon=True).start()
        self.root.after(100, concluir)

    def salvar(self):
        if self.relatorio is None:
            return
        destino = filedialog.asksaveasfilename(parent=self.root, title="Salvar relatório", defaultextension=".txt",
            initialfile="relatorio_wacc.txt", filetypes=[("Relatório de texto", "*.txt")])
        if destino:
            try:
                Path(destino).write_text(self.relatorio, encoding="utf-8")
            except OSError as erro:
                messagebox.showerror("Erro ao salvar", str(erro), parent=self.root)
                return
            self.status.set(f"Relatório salvo em: {destino}")


def main():
    root = tk.Tk()
    Aplicacao(root)
    root.mainloop()


if __name__ == "__main__":
    main()
