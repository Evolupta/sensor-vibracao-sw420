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

MonitorSensor::MonitorSensor(const SensorVibracao& sensor, int intervaloMs, int totalLeituras,
                             const EmissorUdp* emissor, const std::string& idSensor)
    : sensor(sensor) {
    this->intervaloMs = (intervaloMs >= 0) ? intervaloMs : 0;
    this->totalLeituras = (totalLeituras > 0) ? totalLeituras : 0;
    this->emissor = emissor;
    this->idSensor = idSensor.empty() ? "VIBRACAO_SW420" : idSensor;
}

long long MonitorSensor::timestampMs() const {
    return std::chrono::duration_cast<std::chrono::milliseconds>(
               std::chrono::system_clock::now().time_since_epoch()).count();
}

std::string MonitorSensor::formatarHora(long long ms) const {
    std::time_t segundos = (std::time_t)(ms / 1000);
    int resto = (int)(ms % 1000);

    std::tm local = *std::localtime(&segundos);
    char data[32];
    std::strftime(data, sizeof(data), "%Y-%m-%d %H:%M:%S", &local);

    std::ostringstream texto;
    texto << data << '.' << std::setfill('0') << std::setw(3) << resto;
    return texto.str();
}

std::string MonitorSensor::montarMensagem(int sequencia, long long ms, double tensao,
                                          bool vibrando, int bruto) const {
    std::ostringstream texto;
    texto << idSensor << ','
          << sequencia << ','
          << ms << ','
          << std::fixed << std::setprecision(3) << tensao << ','
          << "V" << ','
          << (vibrando ? 1 : 0) << ','
          << bruto;
    return texto.str();
}

int MonitorSensor::executar(std::ostream& saida) const {
    int lidas = 0;
    int comVibracao = 0;
    int enviados = 0;
    int falhasEnvio = 0;
    int minimo = 0;
    int maximo = 0;

    saida << "Sensor SW-420 | canal " << sensor.getCanal()
          << " | " << sensor.getCaminhoIio() << "\n"
          << "Intervalo: " << intervaloMs << " ms | Leituras: "
          << (totalLeituras > 0 ? std::to_string(totalLeituras) : std::string("continuo (Ctrl+C para parar)"))
          << "\n";
    if (emissor != 0 && emissor->estaPronto()) {
        saida << "UDP: enviando para " << emissor->getIp() << ":" << emissor->getPorta()
              << " | id = " << idSensor << "\n";
    } else if (emissor != 0) {
        saida << "UDP: IP/porta invalidos - NAO sera enviado nada.\n";
    } else {
        saida << "UDP: desligado (informe ip_servidor para enviar).\n";
    }
    saida << std::endl;

    while (totalLeituras == 0 || lidas < totalLeituras) {
        int bruto = 0;
        double tensao = 0.0;
        bool vibrando = false;

        if (!sensor.lerAmostra(bruto, tensao, vibrando)) {
            saida << "Erro: nao foi possivel ler o canal ADC. Verifique o canal e o caminho IIO." << std::endl;
            return 1;
        }
        long long agora = timestampMs();

        lidas++;
        if (lidas == 1 || bruto < minimo) minimo = bruto;
        if (lidas == 1 || bruto > maximo) maximo = bruto;
        if (vibrando) comVibracao++;

        std::string situacaoUdp;
        if (emissor != 0 && emissor->estaPronto()) {
            if (emissor->enviar(montarMensagem(lidas, agora, tensao, vibrando, bruto))) {
                enviados++;
                situacaoUdp = " | UDP: enviado";
            } else {
                falhasEnvio++;
                situacaoUdp = " | UDP: FALHOU";
            }
        }

        saida << formatarHora(agora)
              << " | #" << std::setw(4) << lidas
              << " | bruto = " << std::setw(5) << bruto
              << " | tensao = " << std::fixed << std::setprecision(3) << tensao << " V"
              << " | " << (vibrando ? "VIBRANDO  <<< ALERTA" : "repouso")
              << situacaoUdp
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
          << " | bruto maximo: " << maximo << "\n"
          << "Pacotes UDP enviados: " << enviados
          << " | falhas: " << falhasEnvio << std::endl;
    return 0;
}
