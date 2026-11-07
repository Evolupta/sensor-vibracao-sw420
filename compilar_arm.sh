#!/bin/bash
# compilar_arm.sh - Entrega 3: compila (nativo + cruzado ARM) e testa o envio UDP na VM Ubuntu.
# Uso na VM:  bash /media/sf_projeto/compilar_arm.sh   (ou /mnt/projeto, se montada manualmente)
set -e
exec > >(tee "$HOME/resultado_compilacao_arm.txt") 2>&1

echo "=== 1. Localizando pasta compartilhada ==="
PROJ=/media/sf_projeto
if [ ! -d "$PROJ/src" ]; then
  PROJ=/mnt/projeto
  sudo mkdir -p "$PROJ"
  sudo mount -t vboxsf projeto "$PROJ" 2>/dev/null || true
fi
echo "$PROJ"

echo "=== 2. Copiando fontes para ~/SensorVibracao ==="
rm -rf "$HOME/SensorVibracao"
mkdir -p "$HOME/SensorVibracao"
cp -r "$PROJ/src" "$PROJ/Makefile" "$PROJ/Doxyfile" "$PROJ/servidor_udp.py" "$HOME/SensorVibracao/"
cd "$HOME/SensorVibracao"

echo "=== 3. Localizando a toolchain ARM ==="
CROSS_CXX=$(find "$HOME" -name 'arm-buildroot-linux-gnueabihf-g++' 2>/dev/null | head -n 1)
if [ -z "$CROSS_CXX" ]; then
  echo "ERRO: arm-buildroot-linux-gnueabihf-g++ nao encontrado. Extraia o SDK: tar -xvf arm-buildroot-linux-gnueabihf_sdk-DK2.tar.gz"
  exit 1
fi
echo "$CROSS_CXX"

echo "=== 4. Compilacao nativa (x86_64) ==="
make clean && make

echo "=== 5. Teste do envio UDP em loopback (Linux): servidor Python + teste_sensor ==="
mkdir -p /tmp/iio_sim
python3 -u servidor_udp.py --porta 5005 --log /tmp/log_vm.csv --max 8 &
SERVIDOR=$!
sleep 1
echo 4000 > /tmp/iio_sim/in_voltage6_raw
./build/teste_sensor 6 50 4 127.0.0.1 5005 VIBRACAO_SW420 /tmp/iio_sim
echo 52000 > /tmp/iio_sim/in_voltage6_raw
./build/teste_sensor 6 50 4 127.0.0.1 5005 VIBRACAO_SW420 /tmp/iio_sim
wait $SERVIDOR
echo "--- log CSV do servidor ---"
cat /tmp/log_vm.csv

echo "=== 6. Compilacao cruzada para o kit STM32MP1-DK1 (ARM) ==="
make clean && make CXX="$CROSS_CXX"
file ./build/teste_sensor
cp -f ./build/teste_sensor "$PROJ/teste_sensor_arm"
cp -f "$HOME/resultado_compilacao_arm.txt" "$PROJ/resultado_compilacao_arm.txt" 2>/dev/null || true
echo "=== CONCLUIDO: $PROJ/teste_sensor_arm gerado ==="
