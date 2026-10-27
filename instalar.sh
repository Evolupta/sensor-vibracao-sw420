#!/bin/bash
set -e
exec > >(tee "$HOME/resultado_teste_vm.txt") 2>&1
echo '=== 1. Montando pastas compartilhadas / CD ==='
sudo mkdir -p /mnt/desktop /mnt/projeto
sudo mount -t vboxsf desktop /mnt/desktop 2>/dev/null || true
sudo mount -t vboxsf projeto /mnt/projeto 2>/dev/null || true
echo '=== 2. Copiando arquivos para C:\Users\rapha e Desktop ==='
if [ -f /mnt/desktop/arm-buildroot-linux-gnueabihf_sdk-DK2.tar.gz ]; then
  cp -v /mnt/desktop/arm-buildroot-linux-gnueabihf_sdk-DK2.tar.gz "$HOME/"
fi
mkdir -p "$HOME/SensorVibracao"
cp -rf /mnt/projeto/* /mnt/projeto/.gitignore "$HOME/SensorVibracao/" 2>/dev/null || true
chmod -R u+rwX "$HOME/SensorVibracao"
if [ -d "$HOME/Desktop" ]; then cp -rf "$HOME/SensorVibracao" "$HOME/Desktop/"; fi
echo '=== 3. Extraindo a toolchain (arm-buildroot-linux-gnueabihf_sdk-DK2.tar.gz) ==='
cd "$HOME"
if [ ! -d "$HOME/arm-buildroot-linux-gnueabihf_sdk-buildroot" ]; then
  tar -xvf arm-buildroot-linux-gnueabihf_sdk-DK2.tar.gz
fi
SDK_DIR=$(find "$HOME" -maxdepth 2 -type d -name 'arm-buildroot-linux-gnueabihf*' | head -n 1)
if [ -n "$SDK_DIR" ] && [ -f "$SDK_DIR/relocate-sdk.sh" ]; then
  echo '=== 4. Configurando SDK (relocate-sdk.sh) ==='
  cd "$SDK_DIR" && ./relocate-sdk.sh
fi
echo '=== 5. Testando compilacao local (x86_64 Linux) ==='
cd "$HOME/SensorVibracao" && make clean && make && ./build/teste_sensor
if [ -n "$SDK_DIR" ]; then
  CROSS_CXX=$(find "$SDK_DIR" -name 'arm-buildroot-linux-gnueabihf-g++' | head -n 1)
  if [ -n "$CROSS_CXX" ]; then
    echo '=== 6. Compilando para a placa ARM STM32MP1 (Cross-Compile) ==='
    make clean && make CXX="$CROSS_CXX"
    file ./build/teste_sensor
    cp -f ./build/teste_sensor /mnt/projeto/teste_sensor_arm 2>/dev/null || true
  fi
fi
echo '=== CONCLUIDO COM SUCESSO! ==='
cp -f "$HOME/resultado_teste_vm.txt" /mnt/projeto/resultado_teste_vm.txt 2>/dev/null || true
