#!/usr/bin/env python3
"""Teste local de regressão da GUI: UDP por loopback, parsing, histórico e alarme.
Execute com display disponível: python teste_gui_local.py.
Não substitui a validação com o kit STM32 físico.
"""
import csv
import os
import socket
import tempfile
import time
from pathlib import Path
from interface_grafica import AmostraSensor, GerenciadorHistorico, InterfaceMonitoramento


def testar():
    amostra = 'VIBRACAO_SW420,1,1794351651959,0.134,V,0,2660'
    assert AmostraSensor.de_csv(amostra, '127.0.0.1') is not None
    invalidos = [
        'incompleto',
        'VIBRACAO_SW420,0,1794351651959,0.134,V,0,2660',
        'VIBRACAO_SW420,1,1794351651959,nan,V,0,2660',
        'VIBRACAO_SW420,1,1794351651959,3.8,V,1,65535',
        'VIBRACAO_SW420,1,1794351651959,0.134,V,2,2660',
        'VIBRACAO_SW420,1,1794351651959,0.134,A,0,2660',
        'VIBRACAO_SW420,1,1794351651959,2.729,V,1,2660',
    ]
    for s in invalidos:
        assert AmostraSensor.de_csv(s, '127.0.0.1') is None, s

    with tempfile.TemporaryDirectory(prefix='gui-sw420-') as tmp:
        log = Path(tmp) / 'log_sensor.csv'
        log.write_text('EVIDENCIA ANTIGA\n', encoding='utf8')
        relatorio = Path(tmp) / 'relatorio_monitoramento.txt'
        relatorio.write_text('RELATORIO ANTIGO\n', encoding='utf8')
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('127.0.0.1', 0))
            porta = s.getsockname()[1]
        app = InterfaceMonitoramento(porta, str(log), str(relatorio))
        try:
            assert app.historico.caminho_csv != str(log), 'log antigo sobrescrito'
            assert app.historico.caminho_relatorio != str(relatorio), 'relatorio antigo sobrescrito'
            assert not app.modo_demo
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as cli:
                valores = [2660, 2800, 54200, 2690, 65535]
                for i, bruto in enumerate(valores,1):
                    volts=bruto*3.3/65535
                    cli.sendto(('VIBRACAO_SW420,%d,179435165%d,%.3f,V,%d,%d' %
                               (i,2000+i,volts,int(volts>=1.65),bruto)).encode(),
                               ('127.0.0.1', porta))
                cli.sendto(b'mensagem_invalida',('127.0.0.1',porta))
            time.sleep(.15)
            app.raiz.update()
            app._atualizar_ciclo()
            app.raiz.update()
            assert app.historico.total_validos == 5,app.historico.total_validos
            assert app.historico.total_invalidos == 1,app.historico.total_invalidos
            assert app.historico.total_com_alerta == 2,app.historico.total_com_alerta
            assert app.historico.total_perdidos == 0
            assert len(app.historico.amostras) == 5
            assert app.lbl_tensao.cget('text') == '3.300 V'
            assert 'ALERTA' in app.rotulo_titulo_status.cget('text')
            # Falha de comunicação não pode continuar verde.
            app.ultima_amostra.instante_recepcao -= 4.5
            app._atualizar_indicadores(False)
            assert 'SEM SINAL' in app.rotulo_titulo_status.cget('text')
        finally:
            app.encerrar()
        assert log.read_text(encoding='utf8') == 'EVIDENCIA ANTIGA\n'
        assert relatorio.read_text(encoding='utf8') == 'RELATORIO ANTIGO\n'
        with open(app.historico.caminho_csv, encoding='utf8',newline='') as f:
            rows=list(csv.DictReader(f))
        assert len(rows)==5, len(rows)
        assert sum(int(x['vibracao']) for x in rows)==2
        text=Path(app.historico.caminho_relatorio).read_text(encoding='utf8')
        assert 'Pacotes validos recebidos : 5' in text
        assert 'Pacotes invalidos         : 1' in text
    print('OK: protocolo, UDP real por loopback, GUI, alertas, perda de sinal, CSV e preservacao de arquivos')

if __name__=='__main__':
    testar()
