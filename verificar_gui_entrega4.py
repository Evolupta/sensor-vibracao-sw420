#!/usr/bin/env python3
"""Confere o CSV real da GUI com 30 amostras em repouso e 50 em movimento.
Uso: python verificar_gui_entrega4.py log_sensor.csv --ip-kit 10.0.1.101
Não substitui a observação presencial do sensor e da interface.
"""
import argparse
import csv
import math
import sys
from pathlib import Path


class VerificadorEntrega4:
    CAMPOS = ('recebido_em', 'ip_origem', 'id_sensor', 'sequencia', 'timestamp_ms', 'valor', 'unidade', 'vibracao', 'bruto')

    def __init__(self, caminho, ip_kit):
        self.caminho = caminho
        self.ip_kit = ip_kit
        self.erros = []

    def executar(self):
        with self.caminho.open(encoding='utf-8-sig', newline='') as arquivo:
            leitor = csv.DictReader(arquivo)
            if not set(self.CAMPOS).issubset(leitor.fieldnames or []):
                print('FALHA: colunas da GUI incompletas')
                return 1
            registros = list(leitor)

        if len(registros) != 80:
            self.erros.append('esperados 80 registros reais, recebidos %d' % len(registros))
        if len(registros) != len({(x['ip_origem'],x['id_sensor'],x['timestamp_ms'],x['sequencia']) for x in registros}):
            self.erros.append('duplicatas exatas na amostra')
        sequencias = list(range(1,31)) + list(range(1,51))
        alertas = [0,0]
        for i, reg in enumerate(registros):
            try:
                seq = int(reg['sequencia'])
                valor = float(reg['valor'])
                bruto = int(reg['bruto'])
                vib = int(reg['vibracao'])
                ts = int(reg['timestamp_ms'])
                if reg['id_sensor'] != 'VIBRACAO_SW420' or reg['unidade'] != 'V':
                    raise ValueError('sensor ou unidade incorreta')
                if (seq < 1 or ts <= 0 or not math.isfinite(valor) or not 0 <= bruto <= 65535
                    or not 0 <= valor <= 3.301 or vib not in (0,1)
                    or abs(valor-bruto*3.3/65535) > 0.002 or vib != (valor >= 1.65)):
                    raise ValueError('campos inconsistentes')
                if i < 80 and seq != sequencias[i]:
                    self.erros.append('posição %d: sequência %d em vez de %d' % (i+1, seq, sequencias[i]))
                if self.ip_kit and reg['ip_origem'] != self.ip_kit:
                    self.erros.append('posição %d: IP de origem %s diferente de %s' % (i+1, reg['ip_origem'],self.ip_kit))
                if reg['ip_origem'] == '127.0.0.1':
                    self.erros.append('posição %d: origem 127.0.0.1 indica teste local, não físico' % (i+1))
                if i < 30:
                    alertas[0] += vib
                elif i < 80:
                    alertas[1] += vib
            except (ValueError,TypeError) as exc:
                self.erros.append('posição %d: %s' % (i+1,exc))

        if alertas[0] > 0:
            self.erros.append('houve %d alertas nas 30 leituras de repouso' % alertas[0])
        if len(registros) == 80 and alertas[1] <= 0:
            self.erros.append('nenhuma vibração nas 50 leituras com movimento')

        print('CSV GUI:', self.caminho)
        print('Registros:',len(registros),'| Alertas em repouso:',alertas[0],'/30 | Alertas com movimento:',alertas[1],'/50')
        if self.erros:
            print('VERIFICAÇÃO NÃO APROVADA:')
            for e in self.erros[:25]: print(' -',e)
            if len(self.erros)>25: print(' - mais',len(self.erros)-25,'erros')
            return 1
        print('CSV CONSISTENTE — validação de integridade e sequência aprovada')
        print('Confronte o CSV com o log físico do kit e capture a interface real; isso não é provado apenas pelo CSV.')
        return 0


def main():
    parser = argparse.ArgumentParser(description='Verifica o CSV real da interface (Entrega 4)')
    parser.add_argument('arquivo',nargs='?',default='log_sensor.csv')
    parser.add_argument('--ip-kit',default=None,help='endereço IPv4 atual do STM32')
    args = parser.parse_args()
    caminho=Path(args.arquivo)
    if not caminho.is_file():
        print('FALHA: arquivo não encontrado:',caminho)
        return 1
    return VerificadorEntrega4(caminho,args.ip_kit).executar()

if __name__ == '__main__':
    sys.exit(main())
