#!/bin/sh
# teste_no_kit.sh - roda NO KIT STM32MP1-DK1 (Entrega 3). Le o sensor SW-420 e ENVIA
# cada leitura por UDP ao PC. Salva a saida em /home/root/resultado_teste_kit.txt
#
# Uso (no kit, na pasta onde esta o teste_sensor):
#     sh teste_no_kit.sh <IP_DO_PC> [canal] [porta]
#     sh teste_no_kit.sh 192.168.42.10          # canal 6 (pino A4), porta 5005
#     sh teste_no_kit.sh 192.168.42.10 13       # canal 13 (pino A5)

IP=$1
CANAL=${2:-6}
PORTA=${3:-5005}
BIN=./teste_sensor
SAIDA=/home/root/resultado_teste_kit.txt

if [ -z "$IP" ]; then
  echo "Uso: sh teste_no_kit.sh <IP_DO_PC> [canal] [porta]"
  exit 1
fi
if [ ! -x "$BIN" ]; then
  echo "ERRO: $BIN nao encontrado ou sem permissao. Rode: chmod +x teste_sensor"
  exit 1
fi

{
  echo "=== TESTE NO KIT STM32MP1-DK1 - canal $CANAL - UDP para $IP:$PORTA ==="
  uname -a
  date
  echo
  echo "--- ping no PC ---"
  ping -c 2 $IP
  echo
  echo "=== PARTE 1: REPOUSO (sensor parado) - 30 leituras ==="
  $BIN $CANAL 100 30 $IP $PORTA
} 2>&1 | tee $SAIDA

echo
echo ">>> PARTE 2: em 5 segundos comece a CHACOALHAR / BATER no sensor e continue ate acabar <<<"
for s in 5 4 3 2 1; do echo "$s..."; sleep 1; done

{
  echo
  echo "=== PARTE 2: COM VIBRACAO (chacoalhando) - 50 leituras ==="
  $BIN $CANAL 100 50 $IP $PORTA
} 2>&1 | tee -a $SAIDA

echo
echo "Pronto! Resultado salvo em $SAIDA (confira tambem a janela do servidor no PC)"
