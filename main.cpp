/**
 * @file main.cpp
 * @brief Programa funcional: lê o sensor SW-420 no kit STM32MP1-DK1 e envia por UDP.
 *
 * Uso: teste_sensor [canal] [intervalo_ms] [leituras] [ip_servidor] [porta] [id_sensor] [caminho_iio]
 *  - canal:        número X do arquivo in_voltageX_raw (padrão 6, pino A4)
 *  - intervalo_ms: pausa entre leituras em milissegundos (padrão 100)
 *  - leituras:     quantidade de leituras; 0 = contínuo até Ctrl+C (padrão 0)
 *  - ip_servidor:  IPv4 do servidor; se omitido, NÃO envia por UDP
 *  - porta:        porta UDP do servidor (padrão 5005)
 *  - id_sensor:    identificador no protocolo (padrão VIBRACAO_SW420)
 *  - caminho_iio:  diretório IIO (padrão /sys/bus/iio/devices/iio:device0)
 *
 * O programa apenas instancia as classes SensorVibracao, EmissorUdp e MonitorSensor.
 */

#include <cstdlib>
#include <iostream>
#include <string>

#include "EmissorUdp.h"
#include "MonitorSensor.h"
#include "SensorVibracao.h"

/**
 * @brief Ponto de entrada do programa.
 * @param argc Quantidade de argumentos da linha de comando.
 * @param argv Argumentos: [1] canal, [2] intervalo ms, [3] leituras, [4] IP, [5] porta,
 *             [6] id do sensor, [7] caminho IIO.
 * @return 0 em caso de sucesso; 1 se alguma leitura falhar.
 */
int main(int argc, char* argv[]) {
    int canal = (argc > 1) ? std::atoi(argv[1]) : 6;
    int intervaloMs = (argc > 2) ? std::atoi(argv[2]) : 100;
    int leituras = (argc > 3) ? std::atoi(argv[3]) : 0;
    std::string ipServidor = (argc > 4) ? argv[4] : "";
    int porta = (argc > 5) ? std::atoi(argv[5]) : 5005;
    std::string idSensor = (argc > 6) ? argv[6] : "VIBRACAO_SW420";
    std::string caminho = (argc > 7) ? argv[7] : "/sys/bus/iio/devices/iio:device0";

    SensorVibracao sensor(canal, caminho);

    if (ipServidor.empty()) {
        MonitorSensor monitor(sensor, intervaloMs, leituras, 0, idSensor);
        return monitor.executar(std::cout);
    }

    EmissorUdp emissor(ipServidor, porta);
    MonitorSensor monitor(sensor, intervaloMs, leituras, &emissor, idSensor);
    return monitor.executar(std::cout);
}
