#!/usr/bin/env python3
"""interface_grafica.py - Interface grafica de monitoramento do sensor SW-420 (Entrega 4).

Projeto de Programacao Aplicada 2026 (IME) - Monitoramento Inteligente de Carga.
Grupo: Sensor de Vibracao Digital (SW-420) - Ferraiollo, Brasil Barreto, Oppelt.

Requisitos atendidos (todos encapsulados em classes, sem variaveis globais):
  - Valor atual do sensor em tempo real (tensao em V, bruto ADC, estado, sequencia, origem)
  - Historico grafico deslizante dos ultimos 30-60 segundos (Canvas Tkinter nativo)
  - Alerta visual imediato para valores acima do limite configurado
  - Salvamento continuo e sob demanda do historico em arquivo CSV
  - [Bonus] Configuracao dinamica do limite de alerta (V) e da janela temporal (30 s / 60 s)
  - [Bonus] Exportacao automatica e manual de relatorio estatistico (.txt)
  - [Bonus] Registro de timestamp do kit e do servidor
  - [Bonus] Indicador temporal da ultima atualizacao recebida ("ha X.X s")

Uso:
    python interface_grafica.py
    python interface_grafica.py --porta 5005 --log log_sensor.csv
    python interface_grafica.py --demo --captura evidencia_interface_grafica.png
"""

import argparse
import collections
import csv
import datetime
import math
import os
import queue
import random
import socket
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class AmostraSensor:
    """Representa uma leitura recebida do kit STM32MP1-DK1 via protocolo UDP CSV."""

    CAMPOS = ["id_sensor", "sequencia", "timestamp_ms", "valor", "unidade", "vibracao", "bruto"]

    def __init__(self, id_sensor, sequencia, timestamp_ms, valor, unidade, vibracao, bruto, ip_origem):
        self.id_sensor = id_sensor
        self.sequencia = sequencia
        self.timestamp_ms = timestamp_ms
        self.valor = valor
        self.unidade = unidade
        self.vibracao = vibracao
        self.bruto = bruto
        self.ip_origem = ip_origem
        self.instante_recepcao = time.time()
        self.horario_recepcao = datetime.datetime.now()

    @classmethod
    def de_csv(cls, texto, ip_origem):
        """Interpreta uma linha CSV de 7 campos; retorna None se for invalida."""
        partes = texto.strip().split(",")
        if len(partes) != len(cls.CAMPOS):
            return None
        try:
            id_sensor = partes[0].strip()
            sequencia = int(partes[1])
            timestamp_ms = int(partes[2])
            valor = float(partes[3])
            unidade = partes[4].strip()
            vibracao = int(partes[5])
            bruto = int(partes[6])
            # Rejeita datagramas numericamente invalidos antes de exibi-los ou registrar alertas.
            if (not id_sensor or sequencia < 1 or timestamp_ms <= 0
                    or unidade != "V" or vibracao not in (0, 1)
                    or bruto < 0 or bruto > 65535
                    or not math.isfinite(valor)
                    or valor < 0.0 or valor > 3.301
                    or abs(valor - bruto * 3.3 / 65535.0) > 0.002):
                return None
            return cls(
                id_sensor=id_sensor,
                sequencia=sequencia,
                timestamp_ms=timestamp_ms,
                valor=valor,
                unidade=unidade,
                vibracao=vibracao,
                bruto=bruto,
                ip_origem=ip_origem,
            )
        except (ValueError, OverflowError):
            return None

    def horario_kit_formatado(self):
        """Formata o timestamp_ms do kit em YYYY-MM-DD HH:MM:SS.mmm."""
        try:
            dt = datetime.datetime.fromtimestamp(self.timestamp_ms / 1000.0)
            return dt.strftime("%Y-%m-%d %H:%M:%S.") + ("%03d" % (self.timestamp_ms % 1000))
        except (OSError, OverflowError, ValueError):
            return str(self.timestamp_ms)

    def linha_csv(self):
        """Retorna a lista de valores para gravacao no arquivo CSV."""
        return [
            self.horario_recepcao.isoformat(timespec="milliseconds"),
            self.ip_origem,
            self.id_sensor,
            self.sequencia,
            self.timestamp_ms,
            "%.3f" % self.valor,
            self.unidade,
            self.vibracao,
            self.bruto,
        ]


class GerenciadorHistorico:
    """Armazena o historico de leituras, estatisticas de sessao e grava logs/relatorios."""

    CABECALHO_CSV = [
        "recebido_em",
        "ip_origem",
        "id_sensor",
        "sequencia",
        "timestamp_ms",
        "valor",
        "unidade",
        "vibracao",
        "bruto",
    ]

    def __init__(self, caminho_csv, caminho_relatorio, max_amostras=3600):
        # Cada sessao gera arquivos novos; nunca sobrescrever evidencias anteriores.
        self.caminho_csv = self._nome_disponivel(caminho_csv)
        self.caminho_relatorio = self._nome_disponivel(caminho_relatorio)
        self.amostras = collections.deque(maxlen=max_amostras)
        self.eventos_alerta = collections.deque(maxlen=200)
        self.inicio_sessao = datetime.datetime.now()
        self.ultima_sequencia = {}
        self.total_validos = 0
        self.total_invalidos = 0
        self.total_perdidos = 0
        self.total_fora_ordem = 0
        self.total_com_alerta = 0
        self.valor_minimo = None
        self.valor_maximo = None
        self.soma_valores = 0.0
        self.gravacao_continua = True
        self._inicializar_csv()

    @staticmethod
    def _nome_disponivel(caminho):
        """Mantem a extensao e acrescenta sufixo se o arquivo ja existir."""
        original = os.fspath(caminho)
        if not os.path.exists(original):
            return original
        raiz, extensao = os.path.splitext(original)
        carimbo = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        candidato = "%s_%s%s" % (raiz, carimbo, extensao)
        numero = 2
        while os.path.exists(candidato):
            candidato = "%s_%s_%d%s" % (raiz, carimbo, numero, extensao)
            numero += 1
        return candidato

    def _inicializar_csv(self):
        """Cria o arquivo CSV de log continuo com cabecalho."""
        try:
            with open(self.caminho_csv, "w", newline="", encoding="utf-8") as arq:
                escritor = csv.writer(arq)
                escritor.writerow(self.CABECALHO_CSV)
        except OSError:
            pass

    def registrar_invalido(self):
        """Incrementa o contador de pacotes descartados."""
        self.total_invalidos += 1

    def registrar_amostra(self, amostra, limiar_alerta):
        """Registra uma amostra valida, verifica sequencia/alerta e grava no CSV."""
        self.total_validos += 1
        self.amostras.append(amostra)

        seq_ant = self.ultima_sequencia.get(amostra.id_sensor)
        if seq_ant is not None:
            if amostra.sequencia > seq_ant + 1:
                self.total_perdidos += amostra.sequencia - seq_ant - 1
            elif amostra.sequencia != 1 and amostra.sequencia <= seq_ant:
                self.total_fora_ordem += 1
        if seq_ant is None or amostra.sequencia > seq_ant or amostra.sequencia == 1:
            self.ultima_sequencia[amostra.id_sensor] = amostra.sequencia

        if self.valor_minimo is None or amostra.valor < self.valor_minimo:
            self.valor_minimo = amostra.valor
        if self.valor_maximo is None or amostra.valor > self.valor_maximo:
            self.valor_maximo = amostra.valor
        self.soma_valores += amostra.valor

        em_alerta = (amostra.valor >= limiar_alerta) or (amostra.vibracao == 1)
        if em_alerta:
            self.total_com_alerta += 1
            resumo_evento = (
                "%s | %s #%d | %.3f %s (bruto=%d) | limiar=%.2f V"
                % (
                    amostra.horario_recepcao.strftime("%H:%M:%S.%f")[:-3],
                    amostra.id_sensor,
                    amostra.sequencia,
                    amostra.valor,
                    amostra.unidade,
                    amostra.bruto,
                    limiar_alerta,
                )
            )
            self.eventos_alerta.appendleft(resumo_evento)

        if self.gravacao_continua:
            try:
                with open(self.caminho_csv, "a", newline="", encoding="utf-8") as arq:
                    escritor = csv.writer(arq)
                    escritor.writerow(amostra.linha_csv())
            except OSError:
                pass

        return em_alerta

    def exportar_csv(self, destino):
        """Salva todas as amostras em memoria em um arquivo CSV escolhido pelo usuario."""
        with open(destino, "w", newline="", encoding="utf-8") as arq:
            escritor = csv.writer(arq)
            escritor.writerow(self.CABECALHO_CSV)
            for am in self.amostras:
                escritor.writerow(am.linha_csv())

    def gerar_relatorio_texto(self, limiar_alerta):
        """Gera o texto do relatorio consolidado da sessao de monitoramento."""
        fim = datetime.datetime.now()
        media = (self.soma_valores / self.total_validos) if self.total_validos > 0 else 0.0
        perc_alerta = (100.0 * self.total_com_alerta / self.total_validos) if self.total_validos > 0 else 0.0
        vmin = ("%.3f V" % self.valor_minimo) if self.valor_minimo is not None else "N/A"
        vmax = ("%.3f V" % self.valor_maximo) if self.valor_maximo is not None else "N/A"

        linhas = [
            "========================================================================",
            "RELATORIO DE MONITORAMENTO INTELIGENTE DE CARGA - SENSOR SW-420",
            "Projeto de Programacao Aplicada 2026 - IME",
            "Integrantes: Ferraiollo, Brasil Barreto, Oppelt",
            "========================================================================",
            "Inicio da sessao : %s" % self.inicio_sessao.strftime("%Y-%m-%d %H:%M:%S"),
            "Fim / geracao    : %s" % fim.strftime("%Y-%m-%d %H:%M:%S"),
            "Limiar de alerta : %.2f V" % limiar_alerta,
            "Arquivo CSV log  : %s" % os.path.abspath(self.caminho_csv),
            "------------------------------------------------------------------------",
            "RESUMO ESTATISTICO:",
            "  Pacotes validos recebidos : %d" % self.total_validos,
            "  Amostras com vibracao     : %d (%.1f %%)" % (self.total_com_alerta, perc_alerta),
            "  Pacotes perdidos (UDP)    : %d" % self.total_perdidos,
            "  Pacotes fora de ordem     : %d" % self.total_fora_ordem,
            "  Pacotes invalidos         : %d" % self.total_invalidos,
            "  Tensao minima medida      : %s" % vmin,
            "  Tensao media medida       : %.3f V" % media,
            "  Tensao maxima medida      : %s" % vmax,
            "------------------------------------------------------------------------",
            "ULTIMOS EVENTOS DE ALERTA REGISTRADOS (max 20):",
        ]
        if not self.eventos_alerta:
            linhas.append("  Nenhum alerta de vibracao registrado na sessao.")
        else:
            for ev in list(self.eventos_alerta)[:20]:
                linhas.append("  - " + ev)
        linhas.append("========================================================================")
        return "\n".join(linhas) + "\n"

    def salvar_relatorio(self, limiar_alerta, destino=None):
        """Salva o relatorio estatistico em disco e retorna o caminho."""
        caminho = destino if destino else self.caminho_relatorio
        conteudo = self.gerar_relatorio_texto(limiar_alerta)
        with open(caminho, "w", encoding="utf-8") as arq:
            arq.write(conteudo)
        return caminho


class ReceptorUdpAssincrono:
    """Thread em segundo plano que escuta a porta UDP e coloca pacotes na fila da GUI."""

    def __init__(self, porta, fila_mensagens):
        self.porta = porta
        self.fila = fila_mensagens
        self.ativo = False
        self.soquete = None
        self.tarefa = None

    def iniciar(self):
        """Abre o socket UDP e inicia a thread receptora."""
        self.soquete = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.soquete.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.soquete.bind(("0.0.0.0", self.porta))
        self.soquete.settimeout(0.25)
        self.ativo = True
        self.tarefa = threading.Thread(target=self._laco_recepcao, daemon=True)
        self.tarefa.start()

    def _laco_recepcao(self):
        """Laco interno da thread de recepcao UDP."""
        while self.ativo:
            try:
                dados, origem = self.soquete.recvfrom(1024)
                texto = dados.decode("utf-8", errors="replace")
                self.fila.put((texto, origem[0]))
            except socket.timeout:
                continue
            except OSError:
                break

    def parar(self):
        """Encerra a thread receptora e fecha o socket."""
        self.ativo = False
        if self.soquete is not None:
            try:
                self.soquete.close()
            except OSError:
                pass


class SimuladorKitLocal:
    """Envia pacotes UDP locais (127.0.0.1) imitando o kit STM32MP1-DK1 para testes."""

    def __init__(self, porta, fila_contingencia=None, historico=None, intervalo_ms=100):
        self.porta = porta
        self.fila_contingencia = fila_contingencia
        self.historico = historico
        self.intervalo_ms = intervalo_ms
        self.ativo = False
        self.sequencia = 0
        self.tarefa = None

    def iniciar(self):
        """Inicia o envio de pacotes simulados em segundo plano."""
        if self.ativo:
            return
        self.ativo = True
        self.tarefa = threading.Thread(target=self._laco_envio, daemon=True)
        self.tarefa.start()

    def parar(self):
        """Interrompe o envio simulado."""
        self.ativo = False

    def _laco_envio(self):
        """Alterna periodos de repouso (~0.13 V) e rajadas de vibracao (~2.5-2.9 V)."""
        soquete = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        usar_contingencia = False
        try:
            while self.ativo:
                self.sequencia += 1
                agora_ms = int(time.time() * 1000)
                ciclo = self.sequencia % 18
                if ciclo in (6, 7, 8, 9, 14, 15, 16, 17):
                    bruto = random.randint(48500, 57800)
                else:
                    bruto = random.randint(2450, 3150)
                tensao = bruto * 3.3 / 65535.0
                vibrando = 1 if tensao >= 1.65 else 0
                msg = "VIBRACAO_SW420,%d,%d,%.3f,V,%d,%d" % (
                    self.sequencia,
                    agora_ms,
                    tensao,
                    vibrando,
                    bruto,
                )
                if self.sequencia >= 3 and self.historico is not None and self.historico.total_validos == 0:
                    usar_contingencia = True

                if usar_contingencia and self.fila_contingencia is not None:
                    self.fila_contingencia.put((msg, "127.0.0.1"))
                else:
                    try:
                        soquete.sendto(msg.encode("utf-8"), ("127.0.0.1", self.porta))
                    except OSError:
                        if self.fila_contingencia is not None:
                            self.fila_contingencia.put((msg, "127.0.0.1"))
                time.sleep(self.intervalo_ms / 1000.0)
        finally:
            soquete.close()


class InterfaceMonitoramento:
    """Janela principal Tkinter para visualizacao em tempo real do sensor SW-420."""

    def __init__(self, porta, caminho_csv, caminho_relatorio, modo_demo=False, caminho_captura=None):
        self.porta = porta
        self.modo_demo = modo_demo
        self.caminho_captura = caminho_captura
        self.fila = queue.Queue()
        self.historico = GerenciadorHistorico(caminho_csv, caminho_relatorio)
        self.receptor = ReceptorUdpAssincrono(porta, self.fila)
        self.simulador = SimuladorKitLocal(porta, fila_contingencia=self.fila, historico=self.historico, intervalo_ms=100)

        self.limiar_alerta = 1.65
        self.janela_segundos = 60
        self.ultima_amostra = None

        if sys.platform.startswith("win"):
            try:
                import ctypes

                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        self.raiz = tk.Tk()
        self.raiz.title("Monitoramento Inteligente de Carga — Sensor de Vibração SW-420 (IME 2026)")
        self.raiz.geometry("1220x740+20+20")
        self.raiz.minsize(1020, 660)
        self.raiz.configure(bg="#0f172a")
        self.raiz.protocol("WM_DELETE_WINDOW", self.encerrar)

        self._construir_interface()
        self.receptor.iniciar()

        if self.modo_demo:
            self.janela_segundos = 30
            self.var_janela.set(30)
            self._ao_mudar_janela()
            self._preencher_historico_demo()
            self.alternar_simulacao()
            if self.caminho_captura:
                self.raiz.after(950, self._salvar_evidencia_e_fechar)

        self.raiz.after(80, self._atualizar_ciclo)

    def _construir_interface(self):
        """Monta todos os paineis, indicadores, controles e o Canvas do grafico."""
        # 1. Banner de Status / Alerta Visual
        self.quadro_alerta = tk.Frame(self.raiz, bg="#1e293b", bd=0, highlightthickness=2, highlightbackground="#334155")
        self.quadro_alerta.pack(fill=tk.X, padx=14, pady=(12, 6))

        self.rotulo_titulo_status = tk.Label(
            self.quadro_alerta,
            text="AGUARDANDO DADOS DO KIT STM32MP1-DK1 (UDP PORTA %d)..." % self.porta,
            font=("Segoe UI", 13, "bold"),
            fg="#f8fafc",
            bg="#1e293b",
            pady=8,
        )
        self.rotulo_titulo_status.pack(side=tk.LEFT, padx=14)

        self.rotulo_ultima_atualizacao = tk.Label(
            self.quadro_alerta,
            text="Última atualização: aguardando pacotes...",
            font=("Segoe UI", 10, "bold"),
            fg="#cbd5e1",
            bg="#1e293b",
        )
        self.rotulo_ultima_atualizacao.pack(side=tk.RIGHT, padx=14)

        # 2. Cartoes de Leitura em Tempo Real
        quadro_cartoes = tk.Frame(self.raiz, bg="#0f172a")
        quadro_cartoes.pack(fill=tk.X, padx=14, pady=6)
        for col in range(4):
            quadro_cartoes.columnconfigure(col, weight=1)

        self.lbl_tensao = self._criar_cartao(quadro_cartoes, 0, "TENSÃO ATUAL (SINAL)", "-- V", "#38bdf8")
        self.lbl_bruto = self._criar_cartao(quadro_cartoes, 1, "VALOR BRUTO ADC (16 BITS)", "-- / 65535", "#a78bfa")
        self.lbl_estado = self._criar_cartao(quadro_cartoes, 2, "ESTADO DO SENSOR", "AGUARDANDO", "#4ade80")
        self.lbl_estat = self._criar_cartao(
            quadro_cartoes, 3, "PACOTES / ALERTAS / PERDAS", "0 válidos | 0 alertas | 0 perdas", "#facc15"
        )

        # 3. Area Central: Grafico Temporal (esquerda) + Painel de Controle e Alertas (direita)
        quadro_central = tk.Frame(self.raiz, bg="#0f172a")
        quadro_central.pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        quadro_central.columnconfigure(0, weight=3)
        quadro_central.columnconfigure(1, weight=1)
        quadro_central.rowconfigure(0, weight=1)

        # 3a. Grafico Temporal (30-60s)
        quadro_grafico = tk.Frame(quadro_central, bg="#1e293b", highlightthickness=1, highlightbackground="#334155")
        quadro_grafico.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        cab_grafico = tk.Frame(quadro_grafico, bg="#1e293b")
        cab_grafico.pack(fill=tk.X, padx=12, pady=(8, 2))
        self.lbl_titulo_grafico = tk.Label(
            cab_grafico,
            text="Histórico Temporal (Últimos 60 s)",
            font=("Segoe UI", 10, "bold"),
            fg="#e2e8f0",
            bg="#1e293b",
        )
        self.lbl_titulo_grafico.pack(side=tk.LEFT)

        self.lbl_timestamp_kit = tk.Label(
            cab_grafico,
            text="Timestamp do kit: --",
            font=("Consolas", 9),
            fg="#94a3b8",
            bg="#1e293b",
        )
        self.lbl_timestamp_kit.pack(side=tk.RIGHT)

        self.tela_grafico = tk.Canvas(quadro_grafico, bg="#0b1120", highlightthickness=0)
        self.tela_grafico.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 10))

        # 3b. Painel Direito: Configuracoes Dinamicas (Bonus) + Acoes + Lista de Alertas
        quadro_direito = tk.Frame(quadro_central, bg="#1e293b", highlightthickness=1, highlightbackground="#334155")
        quadro_direito.grid(row=0, column=1, sticky="nsew")

        tk.Label(
            quadro_direito,
            text="Configurações e Ações",
            font=("Segoe UI", 11, "bold"),
            fg="#f8fafc",
            bg="#1e293b",
        ).pack(anchor="w", padx=12, pady=(10, 6))

        # Limiar de alerta dinamico
        quadro_limiar = tk.Frame(quadro_direito, bg="#1e293b")
        quadro_limiar.pack(fill=tk.X, padx=12, pady=4)
        tk.Label(
            quadro_limiar,
            text="Limiar de Alerta (V):",
            font=("Segoe UI", 9, "bold"),
            fg="#cbd5e1",
            bg="#1e293b",
        ).pack(anchor="w")

        self.var_limiar = tk.DoubleVar(value=1.65)
        escala_limiar = tk.Scale(
            quadro_limiar,
            from_=0.20,
            to=3.10,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.var_limiar,
            command=self._ao_mudar_limiar,
            bg="#1e293b",
            fg="#f8fafc",
            highlightthickness=0,
            troughcolor="#0f172a",
            activebackground="#38bdf8",
        )
        escala_limiar.pack(fill=tk.X)

        # Janela temporal (30s / 60s)
        quadro_janela = tk.Frame(quadro_direito, bg="#1e293b")
        quadro_janela.pack(fill=tk.X, padx=12, pady=4)
        tk.Label(
            quadro_janela,
            text="Janela do Histórico:",
            font=("Segoe UI", 9, "bold"),
            fg="#cbd5e1",
            bg="#1e293b",
        ).pack(side=tk.LEFT)

        self.var_janela = tk.IntVar(value=60)
        for seg in (30, 60):
            tk.Radiobutton(
                quadro_janela,
                text="%d s" % seg,
                variable=self.var_janela,
                value=seg,
                command=self._ao_mudar_janela,
                bg="#1e293b",
                fg="#f8fafc",
                selectcolor="#0f172a",
                activebackground="#1e293b",
                activeforeground="#38bdf8",
            ).pack(side=tk.LEFT, padx=6)

        # Checkbox de log automatico
        self.var_log_auto = tk.BooleanVar(value=True)
        tk.Checkbutton(
            quadro_direito,
            text="Gravar continuamente em CSV (%s)" % os.path.basename(self.historico.caminho_csv),
            variable=self.var_log_auto,
            command=self._ao_mudar_log_auto,
            bg="#1e293b",
            fg="#cbd5e1",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=12, pady=4)

        # Botoes de acao
        quadro_botoes = tk.Frame(quadro_direito, bg="#1e293b")
        quadro_botoes.pack(fill=tk.X, padx=12, pady=6)

        tk.Button(
            quadro_botoes,
            text="Salvar Histórico (CSV)...",
            command=self.salvar_csv_manual,
            bg="#0284c7",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=5,
        ).pack(fill=tk.X, pady=3)

        tk.Button(
            quadro_botoes,
            text="Exportar Relatório (.txt)",
            command=self.exportar_relatorio_manual,
            bg="#0d9488",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=5,
        ).pack(fill=tk.X, pady=3)

        tk.Button(
            quadro_botoes,
            text="Capturar Print da Janela (.png)",
            command=self.capturar_print_manual,
            bg="#334155",
            fg="#f8fafc",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=5,
        ).pack(fill=tk.X, pady=3)

        self.btn_simular = tk.Button(
            quadro_botoes,
            text="Iniciar Simulador Local (Teste)",
            command=self.alternar_simulacao,
            bg="#4f46e5",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=5,
        )
        self.btn_simular.pack(fill=tk.X, pady=3)

        # Lista de eventos de alerta
        tk.Label(
            quadro_direito,
            text="Registro de Alertas Recentes:",
            font=("Segoe UI", 9, "bold"),
            fg="#fca5a5",
            bg="#1e293b",
        ).pack(anchor="w", padx=12, pady=(8, 2))

        self.lista_alertas = tk.Listbox(
            quadro_direito,
            bg="#0b1120",
            fg="#fecaca",
            font=("Consolas", 8),
            highlightthickness=0,
            bd=0,
        )
        self.lista_alertas.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

    def _criar_cartao(self, pai, coluna, titulo, valor_inicial, cor_valor):
        """Cria um cartao padronizado para exibicao de metrica em tempo real."""
        cartao = tk.Frame(pai, bg="#1e293b", highlightthickness=1, highlightbackground="#334155", padx=12, pady=8)
        cartao.grid(row=0, column=coluna, sticky="nsew", padx=4)
        tk.Label(cartao, text=titulo, font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#1e293b").pack(anchor="w")
        rotulo_valor = tk.Label(
            cartao, text=valor_inicial, font=("Segoe UI", 13, "bold"), fg=cor_valor, bg="#1e293b", pady=2
        )
        rotulo_valor.pack(anchor="w")
        return rotulo_valor

    def _ao_mudar_limiar(self, _valor=None):
        """Atualiza dinamicamente o limiar de tensao para disparo de alerta."""
        self.limiar_alerta = float(self.var_limiar.get())

    def _ao_mudar_janela(self):
        """Altera a janela do grafico entre 30 e 60 segundos."""
        self.janela_segundos = int(self.var_janela.get())
        self.lbl_titulo_grafico.configure(text="Histórico Temporal (Últimos %d s)" % self.janela_segundos)

    def _preencher_historico_demo(self):
        """Preenche 26 segundos de leituras sinteticas para demonstracao imediata do grafico."""
        agora = time.time()
        total = 130
        passo = 0.20
        for idx in range(total):
            instante = agora - (total - idx) * passo
            seq = idx + 1
            em_pulso = (idx in range(25, 34)) or (idx in range(68, 78)) or (idx in range(110, 122))
            bruto = random.randint(49500, 57500) if em_pulso else random.randint(2450, 3150)
            tensao = bruto * 3.3 / 65535.0
            vibracao = 1 if tensao >= 1.65 else 0
            am = AmostraSensor(
                id_sensor="VIBRACAO_SW420",
                sequencia=seq,
                timestamp_ms=int(instante * 1000),
                valor=tensao,
                unidade="V",
                vibracao=vibracao,
                bruto=bruto,
                ip_origem="127.0.0.1",
            )
            am.instante_recepcao = instante
            am.horario_recepcao = datetime.datetime.fromtimestamp(instante)
            self.historico.registrar_amostra(am, self.limiar_alerta)
            self.ultima_amostra = am
        self.simulador.sequencia = total

    def _ao_mudar_log_auto(self):
        """Ativa ou pausa a escrita automatica no arquivo CSV."""
        self.historico.gravacao_continua = bool(self.var_log_auto.get())

    def alternar_simulacao(self):
        """Liga ou desliga o gerador local de pacotes UDP para demonstracao/teste."""
        if not self.modo_demo and not self.simulador.ativo:
            messagebox.showwarning(
                "Simulação separada",
                "Para não misturar dados reais e simulados, feche esta sessão e rode:\n"
                "python interface_grafica.py --demo",
            )
            return
        if self.simulador.ativo:
            self.simulador.parar()
            self.btn_simular.configure(text="Iniciar Simulador Local (Teste)", bg="#4f46e5")
        else:
            self.simulador.iniciar()
            self.btn_simular.configure(text="Parar Simulador Local (Ativo)", bg="#d97706")

    def salvar_csv_manual(self):
        """Abre dialogo para salvar o historico acumulado em CSV."""
        destino = filedialog.asksaveasfilename(
            title="Salvar Histórico CSV",
            defaultextension=".csv",
            initialfile="historico_sensor_sw420.csv",
            filetypes=[("Arquivo CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        )
        if destino:
            self.historico.exportar_csv(destino)
            messagebox.showinfo("Histórico Salvo", "Dados exportados com sucesso para:\n%s" % destino)

    def exportar_relatorio_manual(self):
        """Gera e salva imediatamente o relatorio estatistico em .txt."""
        caminho = self.historico.salvar_relatorio(self.limiar_alerta)
        messagebox.showinfo("Relatório Exportado", "Relatório salvo automaticamente em:\n%s" % os.path.abspath(caminho))

    def capturar_print_manual(self):
        """Salva um print (.png) da janela da interface em evidencia_interface_kit.png."""
        destino = "evidencia_interface_kit.png"
        if self._capturar_janela_png(destino):
            messagebox.showinfo("Captura Salva", "Print da interface salvo em:\n%s" % os.path.abspath(destino))
        else:
            messagebox.showwarning(
                "Captura Indisponível",
                "Use a tecla PrintScreen / Ferramenta de Captura do Windows para salvar o print da janela.",
            )

    def _capturar_janela_png(self, destino):
        """Captura a regiao da janela na tela e salva em PNG."""
        try:
            from PIL import ImageGrab

            self.raiz.lift()
            self.raiz.attributes("-topmost", True)
            self.raiz.update_idletasks()
            self.raiz.update()
            x = self.raiz.winfo_rootx()
            y = self.raiz.winfo_rooty()
            w = self.raiz.winfo_width()
            h = self.raiz.winfo_height()
            img = ImageGrab.grab(bbox=(max(0, x), max(0, y - 31), x + w, y + h), all_screens=True)
            img.save(destino)
            return True
        except Exception:
            return False
        finally:
            try:
                self.raiz.attributes("-topmost", False)
            except tk.TclError:
                pass

    def _atualizar_ciclo(self):
        """Consome pacotes da fila UDP, atualiza indicadores e redesenha o grafico."""
        novos_alertas = False
        while True:
            try:
                texto, ip_origem = self.fila.get_nowait()
            except queue.Empty:
                break

            amostra = AmostraSensor.de_csv(texto, ip_origem)
            if amostra is None:
                self.historico.registrar_invalido()
                continue

            self.ultima_amostra = amostra
            if self.historico.registrar_amostra(amostra, self.limiar_alerta):
                novos_alertas = True

        self._atualizar_indicadores(novos_alertas)
        self._desenhar_grafico()
        self.raiz.after(80, self._atualizar_ciclo)

    def _atualizar_indicadores(self, novos_alertas):
        """Atualiza os cartoes, o banner de alerta e o contador de tempo desde o ultimo pacote."""
        if self.ultima_amostra is None:
            return

        am = self.ultima_amostra
        em_alerta = (am.valor >= self.limiar_alerta) or (am.vibracao == 1)
        decorrido = max(0.0, time.time() - am.instante_recepcao)

        self.lbl_tensao.configure(text="%.3f %s" % (am.valor, am.unidade))
        self.lbl_bruto.configure(text="%d / 65535 (seq #%d)" % (am.bruto, am.sequencia))
        self.lbl_estat.configure(
            text="%d válidos | %d alertas | %d perdas"
            % (self.historico.total_validos, self.historico.total_com_alerta, self.historico.total_perdidos)
        )
        self.lbl_timestamp_kit.configure(
            text="%s | %s (%s)" % (am.id_sensor, am.horario_kit_formatado(), am.ip_origem)
        )

        hora_rec = am.horario_recepcao.strftime("%H:%M:%S.%f")[:-3]
        if decorrido > 3.0:
            self.quadro_alerta.configure(bg="#713f12", highlightbackground="#facc15")
            self.rotulo_titulo_status.configure(
                bg="#713f12",
                text="SEM SINAL DO KIT (última leitura há %.1f s)" % decorrido,
            )
            self.rotulo_ultima_atualizacao.configure(
                bg="#713f12",
                text="Última atualização: %s (SEM SINAL há %.1f s)" % (hora_rec, decorrido),
                fg="#fde047",
            )
            self.lbl_estado.configure(text="SEM SINAL (ÚLTIMA LEITURA)", fg="#fde047")
            return
        else:
            self.rotulo_ultima_atualizacao.configure(
                text="Última atualização: %s (há %.1f s)" % (hora_rec, decorrido),
                fg="#f8fafc",
            )

        if em_alerta:
            cor_fundo = "#991b1b"
            self.quadro_alerta.configure(bg=cor_fundo, highlightbackground="#f87171")
            self.rotulo_titulo_status.configure(
                bg=cor_fundo,
                text="ALERTA DE VIOLAÇÃO: VIBRAÇÃO DETECTADA! (%.3f V >= %.2f V)" % (am.valor, self.limiar_alerta),
            )
            self.rotulo_ultima_atualizacao.configure(bg=cor_fundo)
            self.lbl_estado.configure(text="VIBRANDO <<< ALERTA", fg="#f87171")
        else:
            cor_fundo = "#14532d"
            self.quadro_alerta.configure(bg=cor_fundo, highlightbackground="#4ade80")
            self.rotulo_titulo_status.configure(
                bg=cor_fundo,
                text="CARGA ÍNTEGRA — SENSOR EM REPOUSO (%.3f V < %.2f V)" % (am.valor, self.limiar_alerta),
            )
            self.rotulo_ultima_atualizacao.configure(bg=cor_fundo)
            self.lbl_estado.configure(text="REPOUSO (NORMAL)", fg="#4ade80")

        if novos_alertas:
            self.lista_alertas.delete(0, tk.END)
            for item in list(self.historico.eventos_alerta)[:40]:
                self.lista_alertas.insert(tk.END, item)

    def _desenhar_grafico(self):
        """Desenha o grafico deslizante de tensao (0..3.3 V) e a faixa de estado digital."""
        c = self.tela_grafico
        c.delete("all")
        largura = c.winfo_width()
        altura = c.winfo_height()
        if largura < 120 or altura < 120:
            return

        margem_esq = 56
        margem_dir = 42
        margem_sup = 18
        margem_inf = 68
        altura_util = altura - margem_sup - margem_inf
        largura_util = largura - margem_esq - margem_dir

        # Grade de tensao (0.0 V a 3.3 V)
        for v in (0.0, 0.825, 1.65, 2.475, 3.3):
            y = margem_sup + altura_util * (1.0 - (v / 3.3))
            c.create_line(margem_esq, y, largura - margem_dir, y, fill="#1e293b", dash=(2, 2))
            c.create_text(margem_esq - 6, y, text="%.2f V" % v, anchor="e", fill="#94a3b8", font=("Consolas", 8))

        # Grade temporal (divisoes de 10 s)
        passo_s = 10
        for s in range(0, self.janela_segundos + 1, passo_s):
            x = margem_esq + largura_util * (1.0 - (float(s) / self.janela_segundos))
            c.create_line(x, margem_sup, x, margem_sup + altura_util, fill="#1e293b", dash=(2, 4))
            c.create_text(
                x,
                margem_sup + altura_util + 12,
                text="-%ds" % s if s > 0 else "0s (agora)",
                fill="#94a3b8",
                font=("Consolas", 8),
            )

        # Linha do Limiar de Alerta
        y_lim = margem_sup + altura_util * (1.0 - (self.limiar_alerta / 3.3))
        c.create_line(margem_esq, y_lim, largura - margem_dir, y_lim, fill="#f59e0b", width=2, dash=(6, 4))
        c.create_text(
            margem_esq + 8,
            max(margem_sup + 8, y_lim - 8),
            text="Limiar de Alerta: %.2f V" % self.limiar_alerta,
            anchor="w",
            fill="#fbbf24",
            font=("Segoe UI", 8, "bold"),
        )

        # Faixa inferior: pulso digital de vibracao (0 / 1)
        topo_faixa = altura - 34
        base_faixa = altura - 12
        c.create_rectangle(margem_esq, topo_faixa, largura - margem_dir, base_faixa, outline="#334155", fill="#0f172a")
        c.create_text(margem_esq - 6, (topo_faixa + base_faixa) / 2, text="Pulso", anchor="e", fill="#94a3b8", font=("Consolas", 8))

        agora = time.time()
        inicio_janela = agora - self.janela_segundos
        visiveis = [a for a in self.historico.amostras if a.instante_recepcao >= inicio_janela]
        if not visiveis:
            c.create_text(
                margem_esq + largura_util / 2,
                margem_sup + altura_util / 2,
                text="Aguardando pacotes UDP na porta %d..." % self.porta,
                fill="#64748b",
                font=("Segoe UI", 11),
            )
            return

        pontos = []
        for am in visiveis:
            frac_x = (am.instante_recepcao - inicio_janela) / float(self.janela_segundos)
            frac_x = max(0.0, min(1.0, frac_x))
            x = margem_esq + frac_x * largura_util
            v_clamp = max(0.0, min(3.3, am.valor))
            y = margem_sup + altura_util * (1.0 - (v_clamp / 3.3))
            pontos.append((x, y, am))

        if len(pontos) >= 2:
            coords = []
            for x, y, _ in pontos:
                coords.extend([x, y])
            c.create_line(*coords, fill="#38bdf8", width=2)

        for x, y, am in pontos:
            alerta = (am.valor >= self.limiar_alerta) or (am.vibracao == 1)
            if alerta:
                c.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#ef4444", outline="#fecaca")
                c.create_line(x, topo_faixa + 2, x, base_faixa - 2, fill="#ef4444", width=3)
            else:
                c.create_oval(x - 2, y - 2, x + 2, y + 2, fill="#38bdf8", outline="")

    def _salvar_evidencia_e_fechar(self):
        """Em modo --captura, salva prints da interface (repouso e alerta) e encerra."""
        self.simulador.parar()
        agora_ms = int(time.time() * 1000)
        seq = self.historico.total_validos + 1
        am_rep = AmostraSensor("VIBRACAO_SW420", seq, agora_ms, 0.134, "V", 0, 2660, "127.0.0.1")
        self.ultima_amostra = am_rep
        self.historico.registrar_amostra(am_rep, self.limiar_alerta)
        self._atualizar_indicadores(True)
        self._desenhar_grafico()
        self._capturar_janela_png("evidencia_interface_repouso.png")

        seq += 1
        am_alerta = AmostraSensor("VIBRACAO_SW420", seq, agora_ms + 100, 2.729, "V", 1, 54200, "127.0.0.1")
        self.ultima_amostra = am_alerta
        self.historico.registrar_amostra(am_alerta, self.limiar_alerta)
        self._atualizar_indicadores(True)
        self._desenhar_grafico()
        self._capturar_janela_png(self.caminho_captura)
        self.encerrar()

    def encerrar(self):
        """Para threads, exporta automaticamente o relatorio final e fecha a janela."""
        self.simulador.parar()
        self.receptor.parar()
        try:
            self.historico.salvar_relatorio(self.limiar_alerta)
        except OSError:
            pass
        self.raiz.destroy()

    def executar(self):
        """Inicia o laco principal de eventos da interface grafica."""
        self.raiz.mainloop()
        return 0

    @staticmethod
    def principal():
        """Analisa argumentos de linha de comando e inicia a aplicacao."""
        analisador = argparse.ArgumentParser(description="Interface grafica UDP do sensor SW-420 (Entrega 4)")
        analisador.add_argument("--porta", type=int, default=5005, help="porta UDP (padrao 5005)")
        analisador.add_argument("--log", default="log_sensor.csv", help="arquivo CSV de log continuo")
        analisador.add_argument(
            "--relatorio", default="relatorio_monitoramento.txt", help="arquivo de relatorio automatico"
        )
        analisador.add_argument("--demo", action="store_true", help="inicia com o simulador local ativo")
        analisador.add_argument("--captura", default=None, help="salva print da janela neste caminho e encerra")
        args = analisador.parse_args()
        app = InterfaceMonitoramento(
            porta=args.porta,
            caminho_csv=args.log,
            caminho_relatorio=args.relatorio,
            modo_demo=args.demo,
            caminho_captura=args.captura,
        )
        return app.executar()


if __name__ == "__main__":
    sys.exit(InterfaceMonitoramento.principal())
