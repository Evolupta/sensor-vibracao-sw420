#!/usr/bin/env python3
"""Verificacao offline das evidencias UDP do sensor SW-420, Entrega 3.

Execute na pasta do servidor: python verificar_udp_entrega3.py
Nao usa internet, nem bibliotecas adicionais.
"""
import csv
from pathlib import Path

ARQUIVO = Path('log_sensor.csv')
ERROS = []
AVISOS = []

if not ARQUIVO.is_file():
    raise SystemExit('FALHA: nao encontrei log_sensor.csv nesta pasta.')
try:
    with ARQUIVO.open(newline='', encoding='utf-8-sig') as fh:
        leituras = list(csv.DictReader(fh))
except Exception as exc:
    raise SystemExit(f'FALHA: nao consegui ler CSV: {exc}')

campos = ('recebido_em', 'id_sensor', 'sequencia', 'timestamp_ms', 'valor', 'unidade', 'vibracao', 'bruto')
if not leituras:
    raise SystemExit('FALHA: CSV nao tem leituras.')
if not set(campos).issubset(leituras[0]):
    raise SystemExit('FALHA: colunas do CSV inesperadas.')

N = len(leituras)
if N != 80:
    ERROS.append(f'esperados 80 pacotes recebidos; encontrados {N}')
sequencias_esperadas = list(range(1, 31)) + list(range(1, 51))
alertas = []
for i, r in enumerate(leituras):
    try:
        seq = int(r['sequencia'])
        ts = int(r['timestamp_ms'])
        bruto = int(r['bruto'])
        v = float(r['valor'])
        alerta = int(r['vibracao'])
        if seq < 1 or not (0 <= bruto <= 65535) or alerta not in (0, 1):
            ERROS.append(f'pacote {i+1}: campo numerico fora da faixa')
        if r['unidade'] != 'V' or r['id_sensor'] != 'VIBRACAO_SW420':
            ERROS.append(f'pacote {i+1}: identificador/unidade nao esperado')
        if abs(v - bruto * 3.3 / 65535) > 0.002:
            ERROS.append(f'pacote {i+1}: valor e bruto inconsistentes')
        if alerta != int(v >= 1.65):
            ERROS.append(f'pacote {i+1}: alerta incompativel com limiar 1,65 V')
        if ts <= 0:
            ERROS.append(f'pacote {i+1}: timestamp invalido')
        if i < len(sequencias_esperadas) and seq != sequencias_esperadas[i]:
            ERROS.append(f'pacote {i+1}: sequencia {seq}, esperado {sequencias_esperadas[i]}')
        alertas.append(alerta)
    except (TypeError, ValueError, KeyError) as e:
        ERROS.append(f'pacote {i+1}: campos invalidos ({e})')

if len(alertas) >= 80:
    repouso = sum(alertas[:30]); movimento = sum(alertas[30:80])
    if repouso:
        AVISOS.append(f'{repouso}/30 deteccoes na fase de repouso: revisar movimentacao/ligacao')
    if not movimento:
        ERROS.append('nenhuma vibracao detectada na fase com movimento')
    print(f'Deteccoes: repouso {repouso}/30 | movimento {movimento}/50 ({2 * movimento:.1f}%)')
print(f'Datagramas registrados no CSV: {N}')
print('Nota: a sequencia reinicia de 1 na fase 2; isso e esperado neste script.')
if AVISOS:
    print('AVISOS:')
    for msg in AVISOS[:20]: print(' -', msg)
if ERROS:
    print('RESULTADO: VERIFICACAO NAO APROVADA')
    for msg in ERROS[:25]: print(' -', msg)
    if len(ERROS) > 25: print(f' - e mais {len(ERROS)-25} erros')
    raise SystemExit(1)
print('RESULTADO: CONSISTENCIA DO CSV APROVADA')
print('ATENCAO: confirmar separadamente no terminal do servidor: invalidos=0, perdidos=0, fora_de_ordem=0.')
print('ATENCAO: este validador nao prova sozinho a origem fisica do pacote: preserve logs/fotos do kit.')
