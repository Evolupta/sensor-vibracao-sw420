/**
 * @file SensorVibracao.cpp
 * @brief Implementação da classe de leitura do sensor de vibração SW-420.
 */

#include "SensorVibracao.h"

#include <chrono>
#include <fstream>
#include <thread>

SensorVibracao::SensorVibracao(int canal,
                               const std::string& caminhoIio,
                               bool nivelAtivoAlto,
                               double tensaoReferencia,
                               int valorMaximoAdc) {
    this->canal = (canal >= 0) ? canal : 6;
    this->caminhoIio = caminhoIio;
    this->nivelAtivoAlto = nivelAtivoAlto;
    this->tensaoReferencia = (tensaoReferencia > 0.0) ? tensaoReferencia : 3.3;
    this->valorMaximoAdc = (valorMaximoAdc > 0) ? valorMaximoAdc : 65535;
}

std::string SensorVibracao::caminhoDoCanal() const {
    return caminhoIio + "/in_voltage" + std::to_string(canal) + "_raw";
}

bool SensorVibracao::lerBruto(int& valorBruto) const {
    std::ifstream arquivo(caminhoDoCanal().c_str());
    if (!arquivo.is_open()) {
        return false;
    }

    int lido = 0;
    if (!(arquivo >> lido)) {
        return false;
    }

    valorBruto = lido;
    return true;
}

bool SensorVibracao::lerTensao(double& tensao) const {
    int bruto = 0;
    if (!lerBruto(bruto)) {
        return false;
    }

    tensao = (double)bruto * tensaoReferencia / valorMaximoAdc;
    return true;
}

bool SensorVibracao::vibracaoDetectada(bool& detectada) const {
    double tensao = 0.0;
    if (!lerTensao(tensao)) {
        return false;
    }

    // Sinal digital: acima da metade da referência é nível alto, senão baixo.
    bool nivelAlto = (tensao >= tensaoReferencia / 2.0);
    detectada = (nivelAlto == nivelAtivoAlto);
    return true;
}

bool SensorVibracao::medirIntensidade(int amostras, int intervaloMs, double& intensidade) const {
    if (amostras <= 0) {
        return false;
    }

    int comVibracao = 0;
    for (int i = 0; i < amostras; i++) {
        bool detectada = false;
        if (!vibracaoDetectada(detectada)) {
            return false;
        }
        if (detectada) {
            comVibracao++;
        }

        // Não espera depois da última amostra.
        if (i < amostras - 1 && intervaloMs > 0) {
            std::this_thread::sleep_for(std::chrono::milliseconds(intervaloMs));
        }
    }

    intensidade = 100.0 * comVibracao / amostras;
    return true;
}

int SensorVibracao::getCanal() const {
    return canal;
}

std::string SensorVibracao::getCaminhoIio() const {
    return caminhoIio;
}
