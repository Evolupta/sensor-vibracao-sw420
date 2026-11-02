/**
 * @file MonitorSensor.cpp
 * @brief Implementação da classe de monitoramento contínuo do sensor SW-420.
 */

#include "MonitorSensor.h"

#include <chrono>
#include <ctime>
#include <iomanip>
#include <ostream>
#include <sstream>
#include <thread>

MonitorSensor::MonitorSensor(const SensorVibracao& sensor, int intervaloMs, int totalLeituras)
    : sensor(sensor) {
    this->intervaloMs = (intervaloMs >= 0) ? intervaloMs : 0;
    this->totalLeituras = (totalLeituras > 0) ? totalLeituras : 0;
}

std::string MonitorSensor::horaAtual() const {
    std::chrono::system_clock::time_point agora = std::chrono::system_clock::now();
    std::time_t segundos = std::chrono::system_clock::to_time_t(agora);
    long long ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                       agora.time_since_epoch()).count() % 1000;

    std::tm local = *std::localtime(&segundos);
    char data[32];
    std::strftime(data, sizeof(data), "%Y-%m-%d %H:%M:%S", &local);

    std::ostringstream texto;
    texto << data << '.' << std::setfill('0') << std::setw(3) << ms;
    return texto.str();
}

int MonitorSensor::executar(std::ostream& saida) const {
    int lidas = 0;
    int comVibracao = 0;
    int minimo = 0;
    int maximo = 0;

    saida << "Sensor SW-420 | canal " << sensor.getCanal()
          << " | " << sensor.getCaminhoIio() << "\n"
          << "Intervalo: " << intervaloMs << " ms | Leituras: "
          << (totalLeituras > 0 ? std::to_string(totalLeituras) : std::string("continuo (Ctrl+C para parar)"))
          << "\n" << std::endl;

    while (totalLeituras == 0 || lidas < totalLeituras) {
        int bruto = 0;
        double tensao = 0.0;
        bool vibrando = false;

        if (!sensor.lerAmostra(bruto, tensao, vibrando)) {
            saida << "Erro: nao foi possivel ler o canal ADC. Verifique o canal e o caminho IIO." << std::endl;
            return 1;
        }

        lidas++;
        if (lidas == 1 || bruto < minimo) minimo = bruto;
        if (lidas == 1 || bruto > maximo) maximo = bruto;
        if (vibrando) comVibracao++;

        saida << horaAtual()
              << " | #" << std::setw(4) << lidas
              << " | bruto = " << std::setw(5) << bruto
              << " | tensao = " << std::fixed << std::setprecision(3) << tensao << " V"
              << " | " << (vibrando ? "VIBRANDO  <<< ALERTA" : "repouso")
              << std::endl;

        if (intervaloMs > 0 && (totalLeituras == 0 || lidas < totalLeituras)) {
            std::this_thread::sleep_for(std::chrono::milliseconds(intervaloMs));
        }
    }

    saida << "\n--- Resumo ---\n"
          << "Leituras: " << lidas
          << " | com vibracao: " << comVibracao
          << " (" << std::fixed << std::setprecision(1) << (100.0 * comVibracao / lidas) << " %)"
          << " | bruto minimo: " << minimo
          << " | bruto maximo: " << maximo << std::endl;
    return 0;
}
