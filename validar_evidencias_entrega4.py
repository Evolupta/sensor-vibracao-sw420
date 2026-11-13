#!/usr/bin/env python3
"""Valida os dois CSVs físicos e seus relatórios da Entrega 4, sem rede."""
import csv
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
CASOS = [
    ('log_sensor_20261113_102602.csv','relatorio_monitoramento_20261113_102602.txt',15),
    ('log_sensor_20261113_103150.csv','relatorio_monitoramento_20261113_103150.txt',7),
]

def verificar(csv_nome,rel_nome,alertas_esperados):
    with (BASE / csv_nome).open(newline='',encoding='utf-8-sig') as f:
        dados=list(csv.DictReader(f))
    assert len(dados)==80, f'{csv_nome}: {len(dados)} registros, esperados 80'
    assert [int(d['sequencia']) for d in dados]==list(range(1,31))+list(range(1,51))
    assert {d['ip_origem'] for d in dados}=={'10.0.1.101'}
    assert {d['id_sensor'] for d in dados}=={'VIBRACAO_SW420'}
    assert {d['unidade'] for d in dados}=={'V'}
    assert all(0<=int(d['bruto'])<=65535 for d in dados)
    assert all(abs(float(d['valor'])-int(d['bruto'])*3.3/65535)<=0.002 for d in dados)
    assert all(int(d['vibracao'])==int(float(d['valor'])>=1.65) for d in dados)
    assert sum(int(d['vibracao']) for d in dados[:30])==0
    assert sum(int(d['vibracao']) for d in dados[30:])==alertas_esperados
    assert len({(d['sequencia'],d['timestamp_ms']) for d in dados})==80
    gap=(datetime.fromisoformat(dados[30]['recebido_em'])-datetime.fromisoformat(dados[29]['recebido_em'])).total_seconds()
    assert 4.5<=gap<=6.0, f'intervalo fora do esperado: {gap}'
    rel=(BASE/rel_nome).read_text(encoding='utf-8-sig')
    for parte in [f'Pacotes validos recebidos : 80',f'Amostras com vibracao     : {alertas_esperados}',
                  'Pacotes perdidos (UDP)    : 0','Pacotes fora de ordem     : 0',
                  'Pacotes invalidos         : 0']:
        assert parte in rel, f'{rel_nome}: falta {parte}'
    print(f'PASSOU: {csv_nome} — 80 pacotes, 0 em repouso, {alertas_esperados} em movimento, pausa {gap:.2f}s')

if __name__=='__main__':
    for a,b,c in CASOS: verificar(a,b,c)
    print('CONCLUSAO: DOIS ENSAIOS FISICOS CONSISTENTES COM OS RELATORIOS')
