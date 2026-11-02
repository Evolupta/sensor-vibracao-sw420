/**
 * @file main.cpp
 * @brief Programa funcional de leitura do sensor SW-420 no kit STM32MP1-DK1.
 *
 * Uso: teste_sensor [canal] [intervalo_ms] [leituras] [caminho_iio]
 *  - canal:        número X do arquivo in_voltageX_raw (padrão 6; na bancada foi validado o canal 13)
 *  - intervalo_ms: pausa entre leituras em milissegundos (padrão 100)
 *  - leituras:     quantidade de leituras; 0 = contínuo até Ctrl+C (padrão 0)
 *  - caminho_iio:  diretório IIO (padrão /sys/bus/iio/devices/iio:device0)
 *
 * O programa apenas instancia as classes SensorVibracao e MonitorSensor.
 */

#include <cstdlib>
#include <iostream>
#include <string>

#include "MonitorSensor.h"
#include "SensorVibracao.h"

/**
 * @brief Ponto de entrada do programa.
 * @param argc Quantidade de argumentos da linha de comando.
 * @param argv Argumentos: [1] canal, [2] intervalo em ms, [3] leituras, [4] caminho IIO.
 * @return 0 em caso de sucesso; 1 se alguma leitura falhar.
 */
int main(int argc, char* argv[]) {
    int canal = (argc > 1) ? std::atoi(argv[1]) : 6;
    int intervaloMs = (argc > 2) ? std::atoi(argv[2]) : 100;
    int leituras = (argc > 3) ? std::atoi(argv[3]) : 0;
    std::string caminho = (argc > 4) ? argv[4] : "/sys/bus/iio/devices/iio:device0";

    SensorVibracao sensor(canal, caminho);
    MonitorSensor monitor(sensor, intervaloMs, leituras);
    return monitor.executar(std::cout);
}
