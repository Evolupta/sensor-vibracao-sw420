#!/bin/sh
# Teste físico do SW-420: 30 leituras em repouso e 50 com vibração.
# Uso: sh teste_no_kit.sh 13
# O canal 13 foi validado na montagem documentada; informe outro canal se necessário.

CANAL=${1:-13}
BIN=./teste_sensor
SAIDA=/home/root/resultado_teste_kit.txt
IIO=/sys/bus/iio/devices/iio:device0/in_voltage${CANAL}_raw

mkdir -p /home/root || exit 1
if [ ! -x "$BIN" ]; then
  echo "ERRO: $BIN ausente ou sem permissão de execução. Execute: chmod +x teste_sensor" >&2
  exit 1
fi
if [ ! -r "$IIO" ]; then
  echo "ERRO: canal ADC $CANAL indisponível em $IIO" >&2
  exit 1
fi

{
  echo "=== TESTE NO KIT STM32MP1-DK1 - canal $CANAL ==="
  uname -a
  date
  echo
  echo "--- Leitura direta do ADC (5 amostras) ---"
  for i in 1 2 3 4 5; do cat "$IIO"; sleep 0.2; done
  echo
  echo "=== PARTE 1: REPOUSO (sensor parado) - 30 leituras ==="
  "$BIN" "$CANAL" 100 30
} 2>&1 | tee "$SAIDA"

echo
echo ">>> PARTE 2: em 5 segundos comece a CHACOALHAR / BATER no sensor e continue ate acabar <<<"
for s in 5 4 3 2 1; do echo "$s..."; sleep 1; done

{
  echo
  echo "=== PARTE 2: COM VIBRACAO (chacoalhando) - 50 leituras ==="
  "$BIN" "$CANAL" 100 50
} 2>&1 | tee -a "$SAIDA"

echo
echo "Pronto! Resultado salvo em $SAIDA"
