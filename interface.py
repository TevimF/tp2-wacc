"""Interface gráfica (Tkinter) do Trabalho 2 — custo de capital da frota.

A janela tem duas colunas:
- à esquerda, os campos das premissas (fontes de financiamento, taxas e a
  sensibilidade do spread), o botão de captura da Meta Selic e o de cálculo;
- à direita, a resposta à pergunta do título: a proporção de dívida de menor
  WACC sob as premissas, o WACC da estrutura informada, o gráfico da curva de
  estrutura de capital e o botão para salvar o relatório.

Toda a parte financeira fica em wacc.py; este arquivo só cuida da tela.
Usa apenas a biblioteca padrão do Python (tkinter já acompanha o instalador).
"""
import queue        # Fila segura para trocar dados entre threads.
import threading    # Executa a consulta ao Banco Central sem travar a janela.
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Cálculo, curva, captura, relatório e formatação brasileira (R$ 1.000,00; 13,96%).
from wacc import (DIVIDA_MAXIMA, SENSIBILIDADE_PADRAO, buscar_selic, calcular,
                  curva_estrutura, gerar_relatorio, numero_br, percentual)

# Cores usadas no gráfico.
AZUL = "#3568a8"      # Linha do WACC e ponto de menor WACC.
LARANJA = "#c77a1f"   # Ponto da estrutura informada.
CINZA = "#888888"     # Eixos, grade e rótulos.


class Aplicacao:
    """Monta a janela e reage aos botões (buscar Selic, calcular, salvar)."""

    def __init__(self, root):
        """Cria todos os elementos da tela e já calcula o exemplo inicial."""
        self.root = root

        # --- Janela principal -------------------------------------------------
        root.title("TP2 — Custo de capital da frota")
        root.geometry("1080x800")
        root.minsize(980, 760)
        # Duas colunas de mesma largura que crescem junto com a janela;
        # a linha 1 (conteúdo) é a que estica na vertical.
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)
        ttk.Label(root, text="Como financiar a frota?", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(16, 8))

        # Coluna da esquerda: entradas. Coluna da direita: resultados.
        esquerda = ttk.Frame(root, padding=(18, 0, 8, 12))
        esquerda.grid(row=1, column=0, sticky="nsew")
        direita = ttk.LabelFrame(root, text="Resultados", padding=16)
        direita.grid(row=1, column=1, sticky="nsew", padx=(8, 18), pady=(0, 12))
        direita.columnconfigure(0, weight=1)
        direita.rowconfigure(3, weight=1)  # O gráfico ocupa a altura que sobrar.

        # --- Estado da aplicação ----------------------------------------------
        self.campos = {}            # chave da premissa -> StringVar do campo digitado
        # Texto que vai ao relatório explicando de onde veio a taxa de referência.
        self.fonte = "Exemplo fictício de 10% a.a.; não representa a Selic atual."
        self.taxa_capturada = None  # Última Selic obtida do Banco Central (ou None).
        self.relatorio = None       # Texto do último relatório válido (None = desatualizado).
        self.curva = None           # Dicionário devolvido por curva_estrutura().
        self.status = tk.StringVar(value="Exemplo fictício carregado. Edite os valores para simular.")

        # --- Campos de entrada --------------------------------------------------
        # Cada item: (chave, rótulo, valor inicial, texto de ajuda).
        # As chaves coincidem com os parâmetros de wacc.calcular/curva_estrutura.
        secoes = [
            ("1. Fontes de financiamento (estrutura atual)", [
                ("capital_proprio", "Capital próprio (R$)", "300000", "Valor de mercado dos recursos dos sócios."),
                ("divida", "Dívida (R$)", "200000", "Valor de mercado dos recursos de terceiros.")]),
            ("2. Taxas e premissas", [
                ("livre_risco", "Taxa de referência (% a.a.)", "10", "Pode ser preenchida com a Meta Selic."),
                ("premio", "Prêmio de mercado (p.p. a.a.)", "6", "Retorno esperado do mercado menos a taxa livre de risco."),
                ("beta", "Beta", "1,2", "Sensibilidade das ações ao risco do mercado, na estrutura atual."),
                ("spread", "Spread da dívida (p.p. a.a.)", "3", "Acréscimo de juros sobre a taxa de referência, na estrutura atual."),
                ("imposto", "Alíquota assumida (%)", "30", "Hipótese de benefício fiscal sobre os juros.")]),
            ("3. Curva de estrutura de capital", [
                ("sensibilidade", "Sensibilidade do spread (p.p.)", numero_br(SENSIBILIDADE_PADRAO, 0),
                 "Quanto o juro sobe com mais dívida: spread = base + sensibilidade × (D/V)². Use 0 para spread fixo.")])]
        for titulo, campos in secoes:
            quadro = ttk.LabelFrame(esquerda, text=titulo, padding=10)
            quadro.pack(fill="x", pady=(0, 10))
            quadro.columnconfigure(0, weight=1)
            for linha, (chave, rotulo, padrao, ajuda) in enumerate(campos):
                # Cada premissa ocupa duas linhas da grade: rótulo + campo, e ajuda embaixo.
                ttk.Label(quadro, text=rotulo).grid(row=linha*2, column=0, sticky="w")
                variavel = tk.StringVar(value=padrao)
                campo = ttk.Entry(quadro, textvariable=variavel, width=16)
                campo.grid(row=linha*2, column=1, padx=(8, 0), sticky="e")
                ttk.Label(quadro, text=ajuda, wraplength=400, foreground="#555555").grid(
                    row=linha*2+1, column=0, columnspan=2, sticky="w", pady=(2, 6))
                self.campos[chave] = variavel
                # Qualquer edição invalida o resultado anterior (ver invalidar()).
                variavel.trace_add("write", self.invalidar)

        # --- Botões da coluna esquerda ----------------------------------------
        self.botao_busca = ttk.Button(esquerda, text="Buscar Meta Selic (Banco Central)", command=self.buscar)
        self.botao_busca.pack(fill="x")
        ttk.Label(esquerda, text="Use vírgula ou ponto decimal, sem separador de milhar.", wraplength=420).pack(anchor="w", pady=6)
        ttk.Button(esquerda, text="Calcular WACC", command=self.calcular).pack(fill="x")

        # --- Área de resultados (coluna direita) --------------------------------
        # Resposta principal: proporção de dívida com o menor WACC.
        ttk.Label(direita, text="Estrutura de menor custo de capital (WACC), sob as premissas:",
                  foreground="#555555").grid(row=0, column=0, sticky="w")
        self.destaque = ttk.Label(direita, font=("Segoe UI", 20, "bold"), foreground=AZUL)
        self.destaque.grid(row=1, column=0, sticky="w", pady=(2, 8))
        # Comparação com a estrutura informada e componentes Ke/Kd.
        self.detalhes = ttk.Label(direita, justify="left", font=("Segoe UI", 10))
        self.detalhes.grid(row=2, column=0, sticky="w")
        # Gráfico da curva: WACC (eixo y) contra a proporção de dívida (eixo x).
        self.grafico = tk.Canvas(direita, height=240, highlightthickness=0, background="white")
        self.grafico.grid(row=3, column=0, sticky="nsew", pady=10)
        # Redesenha o gráfico sempre que a janela muda de tamanho.
        self.grafico.bind("<Configure>", lambda event: self.desenhar())
        self.explicacao = ttk.Label(direita, wraplength=460, justify="left")
        self.explicacao.grid(row=4, column=0, sticky="w")
        # Fórmulas fixas, para o usuário conferir o método (capítulos 12 e 15).
        ttk.Label(direita, foreground="#555555", justify="left", text=(
            "Ke = Rf + β × prêmio   ·   Kd = Rf + spread\n"
            "WACC = E/V × Ke + D/V × Kd × (1 − T)\n"
            "β = βU × [1 + (1 − T) × D/E] (Hamada)   ·   spread = base + sens. × (D/V)²")
        ).grid(row=5, column=0, sticky="w", pady=10)
        self.exportar = ttk.Button(direita, text="Salvar relatório TXT", command=self.salvar)
        self.exportar.grid(row=6, column=0, sticky="ew")

        # Barra de status no rodapé: mensagens de andamento e a fonte da taxa.
        ttk.Label(root, textvariable=self.status, wraplength=1040).grid(row=2, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 12))
        # A tecla Enter também calcula.
        root.bind("<Return>", lambda event: self.calcular())
        # Mostra o exemplo já calculado ao abrir a janela.
        self.calcular()

    def invalidar(self, *_):
        """Evita exportar resultados antigos depois de editar uma premissa.

        É chamada pelo Tkinter a cada tecla digitada em qualquer campo
        (os argumentos que ele envia são ignorados).
        """
        self.relatorio = None
        # Durante o __init__ os campos são criados antes do botão "exportar";
        # nesse momento ainda não há o que desabilitar.
        if hasattr(self, "exportar"):
            self.exportar.state(["disabled"])
            self.status.set("Dados alterados. Clique em Calcular WACC para atualizar.")
            self.destaque.config(text="Recalcule o WACC", foreground=CINZA)

    def calcular(self):
        """Lê os campos, calcula o WACC e a curva, atualiza a tela e o relatório."""
        try:
            entradas = {}
            for chave, campo in self.campos.items():
                try:
                    # Aceita vírgula decimal ("1,2") convertendo para ponto ("1.2").
                    entradas[chave] = float(campo.get().strip().replace(",", "."))
                except ValueError:
                    raise ValueError("Preencha todos os campos com números válidos, sem separador de milhar.") from None
            # A sensibilidade só é usada pela curva; calcular() não a recebe.
            sensibilidade = entradas.pop("sensibilidade")
            # Ambas validam as entradas (negativos, soma zero, imposto > 100% etc.).
            r = calcular(**entradas)
            curva = curva_estrutura(**entradas, sensibilidade=sensibilidade)
        except ValueError as erro:
            messagebox.showerror("Confira os dados", str(erro), parent=self.root)
            return

        # Define a fonte da taxa de referência que irá ao relatório:
        # - se a taxa no campo é a Selic capturada, usa a fonte do Banco Central;
        # - se é o 10% do exemplo (sem captura), avisa que é didático;
        # - caso contrário, foi digitada pelo usuário.
        fonte = self.fonte if entradas["livre_risco"] == self.taxa_capturada else "Taxa informada pelo usuário; demais valores são premissas da simulação."
        if self.taxa_capturada is None and entradas["livre_risco"] == 10:
            fonte = "Taxa de 10% informada/exemplo didático; não representa a Selic atual."
        self.relatorio = gerar_relatorio(entradas, r, fonte, curva)
        self.curva = curva
        otimo = curva["otimo"]

        # Resposta principal (formato brasileiro): dívida de menor WACC e o WACC nela.
        self.destaque.config(foreground=AZUL, text=(
            f"{percentual(otimo['peso_d'], 0)} de dívida → WACC de {percentual(otimo['wacc'])} a.a."))
        self.detalhes.config(text=(
            f"Estrutura informada ({percentual(r['peso_d'], 1)} de dívida): WACC de {percentual(r['wacc'])} a.a. "
            f"(+{numero_br((r['wacc'] - otimo['wacc']) * 100)} p.p.)\n"
            f"Ke {percentual(r['ke'])}  ·  Kd {percentual(r['kd'])} ({percentual(r['kd_liquido'])} após impostos)  ·  "
            f"efeito fiscal {numero_br((r['sem_imposto'] - r['wacc']) * 100)} p.p."))
        self.explicacao.config(text=(
            "Mais dívida traz benefício fiscal, mas eleva o beta e o spread. O ponto azul é onde o "
            "custo médio é menor sob estas premissas; o resultado depende da sensibilidade do spread "
            "e não é a estrutura ótima real da empresa."))
        self.desenhar()
        # Só agora o relatório corresponde aos dados da tela: libera o botão Salvar.
        self.exportar.state(["!disabled"])
        self.status.set("Cálculo atualizado. " + fonte)

    def desenhar(self):
        """Desenha a curva do WACC contra a proporção de dívida D/(D+E)."""
        c = self.grafico
        c.delete("all")
        if not self.curva:
            return
        largura, altura = max(1, c.winfo_width()), max(1, c.winfo_height())
        # Margens em pixels: espaço para os rótulos dos eixos.
        esq, dir_, topo, base = 56, 16, 14, 38
        pontos = self.curva["pontos"]
        atual, otimo = self.curva["atual"], self.curva["otimo"]

        # Escalas: x vai de 0% ao máximo da curva (ou até a estrutura informada, se maior);
        # y cobre os valores do WACC com 10% de folga em cima e embaixo.
        x_max = max(DIVIDA_MAXIMA / 100, atual["peso_d"])
        valores = [p["wacc"] for p in pontos] + [atual["wacc"]]
        y_min, y_max = min(valores), max(valores)
        folga = (y_max - y_min) * 0.1 or 0.005  # Evita divisão por zero em curva plana.
        y_min, y_max = y_min - folga, y_max + folga

        def px(peso_d):
            """Converte a proporção de dívida em coordenada horizontal."""
            return esq + peso_d / x_max * (largura - esq - dir_)

        def py(wacc):
            """Converte o WACC em coordenada vertical (valores maiores ficam em cima)."""
            return topo + (y_max - wacc) / (y_max - y_min) * (altura - topo - base)

        # Grade horizontal com rótulos de WACC (5 linhas).
        for i in range(5):
            v = y_min + (y_max - y_min) * i / 4
            c.create_line(esq, py(v), largura - dir_, py(v), fill="#e6e6e6")
            c.create_text(esq - 6, py(v), anchor="e", text=percentual(v), fill=CINZA, font=("Segoe UI", 8))
        # Marcas do eixo x a cada 20 p.p. de dívida.
        for i in range(0, int(x_max * 100) + 1, 20):
            c.create_line(px(i / 100), altura - base, px(i / 100), altura - base + 4, fill=CINZA)
            c.create_text(px(i / 100), altura - base + 6, anchor="n", text=f"{i}%", fill=CINZA, font=("Segoe UI", 8))
        c.create_line(esq, altura - base, largura - dir_, altura - base, fill=CINZA)
        c.create_text((esq + largura - dir_) / 2, altura - 2, anchor="s", fill=CINZA, font=("Segoe UI", 8),
                      text="Dívida / (Dívida + Capital próprio)")

        # Curva do WACC: uma linha ligando os 81 pontos (0% a 80%).
        coordenadas = [valor for p in pontos for valor in (px(p["peso_d"]), py(p["wacc"]))]
        c.create_line(*coordenadas, fill=AZUL, width=2)

        # Linha tracejada vertical marcando a proporção de dívida de menor WACC.
        c.create_line(px(otimo["peso_d"]), py(otimo["wacc"]), px(otimo["peso_d"]), altura - base,
                      fill=AZUL, dash=(3, 3))

        # Pontos de destaque: estrutura informada (laranja) e menor WACC (azul).
        # Os rótulos ficam numa legenda no alto e ao centro, onde a curva em U não passa
        # (perto do mínimo os dois pontos costumam ficar próximos e os textos se sobreporiam).
        legenda_x = (esq + largura - dir_) / 2 - 150
        for ponto, cor, texto, deslocamento in (
                (atual, LARANJA, "Informada", 0),
                (otimo, AZUL, "Menor WACC", 18)):
            x, y = px(ponto["peso_d"]), py(ponto["wacc"])
            c.create_oval(x - 5, y - 5, x + 5, y + 5, fill=cor, outline="white", width=2)
            ly = topo + 6 + deslocamento
            c.create_oval(legenda_x - 4, ly - 4, legenda_x + 4, ly + 4, fill=cor, outline="")
            c.create_text(legenda_x + 10, ly, anchor="w", fill=cor, font=("Segoe UI", 9, "bold"),
                          text=f"{texto}: {percentual(ponto['peso_d'], 0)} de dívida, WACC {percentual(ponto['wacc'])}")

    def buscar(self):
        """Consulta a Meta Selic em outra thread; só a thread principal modifica a janela.

        O Tkinter não é seguro para uso por várias threads. Por isso a consulta
        (que pode demorar até 10 s) roda em segundo plano e coloca o resultado
        em uma fila; a janela verifica essa fila a cada 100 ms com root.after.
        """
        self.botao_busca.state(["disabled"])  # Evita cliques repetidos durante a consulta.
        self.status.set("Consultando o Banco Central...")
        retorno = queue.Queue()

        def trabalhar():
            """Roda em segundo plano: chama a API e guarda (sucesso, valor) na fila."""
            try:
                retorno.put((True, buscar_selic()))
            except Exception as erro:  # Qualquer falha de rede/dados vira mensagem ao usuário.
                retorno.put((False, str(erro)))

        def concluir():
            """Roda na thread da janela: aguarda a fila e mostra o resultado."""
            try:
                sucesso, valor = retorno.get_nowait()
            except queue.Empty:
                # Ainda sem resposta: verifica de novo em 100 ms.
                self.root.after(100, concluir)
                return
            self.botao_busca.state(["!disabled"])
            if sucesso:
                # valor = (taxa em % a.a., descrição da fonte com data e URL).
                self.taxa_capturada, self.fonte = valor
                # Preenche o campo no formato brasileiro (ex.: 15,0).
                self.campos["livre_risco"].set(str(self.taxa_capturada).replace(".", ","))
                self.status.set(self.fonte + " — Clique em Calcular WACC.")
            else:
                self.status.set("Consulta indisponível. Informe a taxa manualmente.")
                messagebox.showwarning("Banco Central", f"Não foi possível buscar a Selic.\n{valor}\n\nVocê pode informar a taxa manualmente.", parent=self.root)

        # daemon=True: a thread não impede o programa de fechar.
        threading.Thread(target=trabalhar, daemon=True).start()
        self.root.after(100, concluir)

    def salvar(self):
        """Pergunta onde salvar e grava o relatório TXT (UTF-8) do último cálculo."""
        if self.relatorio is None:  # Dados editados e ainda não recalculados.
            return
        destino = filedialog.asksaveasfilename(parent=self.root, title="Salvar relatório", defaultextension=".txt",
            initialfile="relatorio_wacc.txt", filetypes=[("Relatório de texto", "*.txt")])
        if destino:  # String vazia = usuário cancelou a janela.
            try:
                Path(destino).write_text(self.relatorio, encoding="utf-8")
            except OSError as erro:  # Ex.: pasta sem permissão ou arquivo aberto.
                messagebox.showerror("Erro ao salvar", str(erro), parent=self.root)
                return
            self.status.set(f"Relatório salvo em: {destino}")


def main():
    """Cria a janela, monta a aplicação e entra no laço de eventos do Tkinter."""
    root = tk.Tk()
    Aplicacao(root)
    root.mainloop()  # Mantém a janela aberta até o usuário fechá-la.


if __name__ == "__main__":
    main()
