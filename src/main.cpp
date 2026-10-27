/**
 * @file main.cpp
 * @brief Programa de teste da classe SensorVibracao.
 *
 * Uso: teste_sensor [canal] [caminho_iio]
 *  - canal:       número X do arquivo in_voltageX_raw (padrão 0)
 *  - caminho_iio: diretório IIO (padrão /sys/bus/iio/devices/iio:device0)
 *
 * Caso o diretório IIO real do kit STM32MP1-DK1 não esteja presente (por
 * exemplo, em testes no PC ou na máquina virtual Ubuntu), cria automaticamente
 * um arquivo IIO simulado no diretório atual para validar todos os métodos da
 * classe SensorVibracao e retorna 0 ao final da execução.
 */

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>

#include "SensorVibracao.h"

/**
 * @brief Ponto de entrada do programa de teste.
 * @param argc Quantidade de argumentos da linha de comando.
 * @param argv Argumentos: [1] canal ADC, [2] caminho do diretório IIO.
 * @return 0 em caso de sucesso; 1 se alguma leitura falhar.
 */
int main(int argc, char* argv[]) {
    int canal = 6;
    if (argc > 1) {
        canal = std::atoi(argv[1]);
    }

    std::string caminho = "/sys/bus/iio/devices/iio:device0";
    if (argc > 2) {
        caminho = argv[2];
    }

    // Verifica se o arquivo IIO existe; caso nao exista (ex.: PC/VM), ativa modo de simulacao local
    bool modoSimulado = false;
    std::string arquivoSimulado;
    std::string arquivoAlvo = caminho + "/in_voltage" + std::to_string(canal) + "_raw";
    {
        std::ifstream testeExistencia(arquivoAlvo.c_str());
        if (!testeExistencia.is_open() && argc <= 2) {
            caminho = ".";
            arquivoSimulado = "./in_voltage" + std::to_string(canal) + "_raw";
            std::ofstream sim(arquivoSimulado.c_str());
            if (sim.is_open()) {
                sim << "52000\n";
                sim.close();
                modoSimulado = true;
                std::cout << "[Aviso] Hardware IIO (/sys/bus/iio/...) nao detectado neste ambiente.\n"
                          << "[Aviso] Executando em modo de simulacao local (" << arquivoSimulado << ").\n"
                          << std::endl;
            }
        }
    }

    SensorVibracao sensor(canal, caminho);
    std::cout << "Sensor SW-420 | canal " << sensor.getCanal()
              << " | " << sensor.getCaminhoIio() << std::endl;

    std::cout << "\n--- Leituras instantaneas ---" << std::endl;
    for (int i = 1; i <= 20; i++) {
        if (modoSimulado) {
            std::ofstream sim(arquivoSimulado.c_str());
            // Alterna valores simulados (ADC 16 bits: 0..65535) entre vibracao (52000 -> ~2.62 V) e repouso (4000 -> ~0.20 V)
            sim << ((i % 2 != 0) ? 52000 : 4000) << "\n";
            sim.close();
        }

        int bruto = 0;
        double tensao = 0.0;
        bool vibrando = false;

        if (!sensor.lerBruto(bruto) || !sensor.lerTensao(tensao) || !sensor.vibracaoDetectada(vibrando)) {
            std::cout << "Erro: nao foi possivel ler o canal ADC. Verifique o canal e o caminho IIO." << std::endl;
            if (modoSimulado) std::remove(arquivoSimulado.c_str());
            return 1;
        }

        std::cout << "Leitura " << i
                  << " | bruto = " << bruto
                  << " | tensao = " << tensao << " V"
                  << " | vibracao = " << (vibrando ? "SIM" : "nao") << std::endl;
    }

    if (modoSimulado) {
        std::ofstream sim(arquivoSimulado.c_str());
        sim << "52000\n";
        sim.close();
    }

    std::cout << "\n--- Intensidade em janela de 20 amostras (100 ms) ---" << std::endl;
    double intensidade = 0.0;
    if (!sensor.medirIntensidade(20, 5, intensidade)) {
        std::cout << "Erro ao medir a intensidade." << std::endl;
        if (modoSimulado) std::remove(arquivoSimulado.c_str());
        return 1;
    }
    std::cout << "Intensidade de vibracao: " << intensidade << " %" << std::endl;

    if (modoSimulado) {
        std::remove(arquivoSimulado.c_str());
    }

    return 0;
}
