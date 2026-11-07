#!/usr/bin/env python3
"""servidor_udp.py - Servidor de teste do protocolo UDP do sensor SW-420 (Entrega 3).

Recebe os datagramas enviados pelo kit, valida o formato, mostra cada leitura,
detecta pacotes perdidos/fora de ordem pelo numero de sequencia e grava um log CSV.
(A interface grafica fica para a Entrega 4.)

Formato de cada mensagem (texto CSV, UTF-8, 7 campos):
    id_sensor,sequencia,timestamp_ms,valor,unidade,vibracao,bruto
    VIBRACAO_SW420,12,1762345678123,2.618,V,1,52000

Uso:
    python servidor_udp.py                       # porta 5005, log em log_sensor.csv
    python servidor_udp.py --porta 6000 --log meu_log.csv
    python servidor_udp.py --max 50              # encerra apos 50 pacotes validos
"""

import argparse
import csv
import datetime
import socket
import sys


class ServidorSensor:
    """Recebe, valida e registra as mensagens UDP do sensor."""

    CAMPOS = ["id_sensor", "sequencia", "timestamp_ms", "valor", "unidade", "vibracao", "bruto"]

    def __init__(self, porta, arquivo_log, maximo):
        self.porta = porta
        self.arquivo_log = arquivo_log
        self.maximo = maximo
        self.ultima_sequencia = {}   # id_sensor -> ultima sequencia recebida
        self.validos = 0
        self.invalidos = 0
        self.perdidos = 0
        self.fora_de_ordem = 0

    def interpretar(self, texto):
        """Converte o texto CSV em dicionario; devolve None se o formato for invalido."""
        partes = texto.strip().split(",")
        if len(partes) != len(self.CAMPOS):
            return None
        try:
            return {
                "id_sensor": partes[0],
                "sequencia": int(partes[1]),
                "timestamp_ms": int(partes[2]),
                "valor": float(partes[3]),
                "unidade": partes[4],
                "vibracao": int(partes[5]),
                "bruto": int(partes[6]),
            }
        except ValueError:
            return None

    def verificar_sequencia(self, leitura):
        """Atualiza contadores de perda/ordem; devolve texto de aviso (ou vazio)."""
        id_sensor = leitura["id_sensor"]
        seq = leitura["sequencia"]
        anterior = self.ultima_sequencia.get(id_sensor)
        aviso = ""
        if anterior is not None:
            if seq == anterior + 1:
                pass
            elif seq > anterior + 1:
                faltaram = seq - anterior - 1
                self.perdidos += faltaram
                aviso = " [PERDA: faltaram %d pacote(s)]" % faltaram
            elif seq == 1:
                aviso = " [REINICIO do emissor: sequencia voltou a 1]"
            else:
                self.fora_de_ordem += 1
                aviso = " [FORA DE ORDEM]"
        if anterior is None or seq > anterior or seq == 1:
            self.ultima_sequencia[id_sensor] = seq
        return aviso

    def executar(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", self.porta))
        print("Servidor UDP ouvindo na porta %d (Ctrl+C para parar). Log: %s" % (self.porta, self.arquivo_log))

        with open(self.arquivo_log, "w", newline="", encoding="utf-8") as arq:
            escritor = csv.writer(arq)
            escritor.writerow(["recebido_em"] + self.CAMPOS)
            try:
                while self.maximo == 0 or self.validos < self.maximo:
                    dados, origem = sock.recvfrom(1024)
                    texto = dados.decode("utf-8", errors="replace")
                    leitura = self.interpretar(texto)
                    if leitura is None:
                        self.invalidos += 1
                        print("[INVALIDO de %s] %r" % (origem[0], texto))
                        continue

                    self.validos += 1
                    aviso = self.verificar_sequencia(leitura)
                    hora = datetime.datetime.fromtimestamp(leitura["timestamp_ms"] / 1000.0)
                    estado = "VIBRANDO <<< ALERTA" if leitura["vibracao"] == 1 else "repouso"
                    print("%s | %s #%d | %.3f %s | %s | bruto=%d | de %s%s" % (
                        hora.strftime("%H:%M:%S.%f")[:-3], leitura["id_sensor"], leitura["sequencia"],
                        leitura["valor"], leitura["unidade"], estado, leitura["bruto"], origem[0], aviso))

                    escritor.writerow([datetime.datetime.now().isoformat(timespec="milliseconds")] +
                                      [leitura[c] for c in self.CAMPOS])
                    arq.flush()
            except KeyboardInterrupt:
                print()
            finally:
                sock.close()

        print("--- Resumo --- validos: %d | invalidos: %d | perdidos: %d | fora de ordem: %d" % (
            self.validos, self.invalidos, self.perdidos, self.fora_de_ordem))

    @staticmethod
    def principal():
        """Le os argumentos da linha de comando e executa o servidor."""
        analisador = argparse.ArgumentParser(description="Servidor UDP de teste do sensor SW-420")
        analisador.add_argument("--porta", type=int, default=5005, help="porta UDP (padrao 5005)")
        analisador.add_argument("--log", default="log_sensor.csv", help="arquivo CSV de log")
        analisador.add_argument("--max", type=int, default=0, help="encerra apos N pacotes validos (0 = infinito)")
        args = analisador.parse_args()
        ServidorSensor(args.porta, args.log, args.max).executar()


if __name__ == "__main__":
    sys.exit(ServidorSensor.principal())
