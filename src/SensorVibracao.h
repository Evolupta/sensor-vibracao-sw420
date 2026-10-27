/**
 * @file SensorVibracao.h
 * @brief Declaração da classe de leitura do sensor de vibração SW-420.
 *
 * Projeto de Programação Aplicada 2026 - Monitoramento Inteligente de Carga.
 */

#ifndef SENSOR_VIBRACAO_H
#define SENSOR_VIBRACAO_H

#include <string>

/**
 * @class SensorVibracao
 * @brief Lê e interpreta o módulo sensor de vibração digital SW-420.
 *
 * O módulo SW-420 possui um comparador (LM393) que entrega uma saída digital:
 * em repouso a saída fica em um nível lógico e, ao detectar vibração, passa
 * para o nível oposto. A sensibilidade é ajustada no potenciômetro do módulo.
 *
 * No kit STM32MP1-DK1 o pino de sinal é ligado a uma entrada do ADC, portanto
 * a leitura é feita pelo subsistema IIO do Linux, no arquivo
 * `/sys/bus/iio/devices/iio:device0/in_voltageX_raw`. A classe converte o
 * valor bruto do ADC em tensão e decide se há vibração comparando essa tensão
 * com metade da tensão de referência.
 *
 * Exemplo de uso:
 * @code
 * SensorVibracao sensor(4);   // sensor ligado ao canal in_voltage4_raw
 * bool vibrando;
 * if (sensor.vibracaoDetectada(vibrando)) {
 *     // usa o resultado
 * }
 * @endcode
 *
 * @note O número do canal depende da ligação física e é descoberto na bancada
 *       (conectar o pino ao GND e ver qual `in_voltageX_raw` retorna zero).
 */
class SensorVibracao {
private:
    int canal;                  ///< Número X do arquivo in_voltageX_raw.
    std::string caminhoIio;     ///< Diretório do dispositivo IIO.
    bool nivelAtivoAlto;        ///< true se o sensor vai a nível alto ao vibrar.
    double tensaoReferencia;    ///< Tensão de fundo de escala do ADC, em volts.
    int valorMaximoAdc;         ///< Maior valor bruto possível do ADC.

    /**
     * @brief Monta o caminho completo do arquivo bruto do canal.
     * @return Texto no formato "<caminhoIio>/in_voltage<canal>_raw".
     */
    std::string caminhoDoCanal() const;

public:
    /**
     * @brief Constrói o sensor.
     * @param canal Número X do canal ADC (arquivo in_voltageX_raw, padrão 6 no pino A4).
     * @param caminhoIio Diretório IIO. O padrão é o do kit STM32MP1.
     * @param nivelAtivoAlto true se a saída do módulo vai a nível alto ao
     *        detectar vibração; false se vai a nível baixo.
     * @param tensaoReferencia Tensão de fundo de escala do ADC, em volts.
     * @param valorMaximoAdc Maior valor bruto do ADC (65535 para 16 bits no STM32MP1).
     *
     * Valores inválidos (canal negativo, tensão ou valor máximo não positivos)
     * são substituídos pelos valores padrão.
     */
    SensorVibracao(int canal = 6,
                   const std::string& caminhoIio = "/sys/bus/iio/devices/iio:device0",
                   bool nivelAtivoAlto = true,
                   double tensaoReferencia = 3.3,
                   int valorMaximoAdc = 65535);

    /**
     * @brief Lê o valor bruto do ADC.
     * @param[out] valorBruto Recebe o valor lido (só é alterado em caso de sucesso).
     * @return true se a leitura foi bem-sucedida; false se o arquivo não pôde
     *         ser aberto ou não continha um número.
     */
    bool lerBruto(int& valorBruto) const;

    /**
     * @brief Lê o sinal do sensor já convertido para volts.
     * @param[out] tensao Recebe a tensão em volts (só é alterada em caso de sucesso).
     * @return true se a leitura foi bem-sucedida; false caso contrário.
     */
    bool lerTensao(double& tensao) const;

    /**
     * @brief Verifica se, neste instante, o sensor indica vibração.
     * @param[out] detectada true se há vibração (só é alterada em caso de sucesso).
     * @return true se a leitura foi bem-sucedida; false caso contrário.
     */
    bool vibracaoDetectada(bool& detectada) const;

    /**
     * @brief Mede a intensidade de vibração em uma janela de várias amostras.
     *
     * A vibração gera pulsos curtos na saída do sensor, e uma única leitura
     * pode perdê-los. Por isso esta função lê várias vezes e informa em que
     * porcentagem das leituras houve vibração.
     *
     * @param amostras Quantidade de leituras (deve ser maior que zero).
     * @param intervaloMs Pausa entre leituras, em milissegundos.
     * @param[out] intensidade Percentual (0 a 100) de amostras com vibração.
     * @return true se todas as leituras foram bem-sucedidas; false se alguma
     *         falhou ou se @p amostras não é positivo.
     */
    bool medirIntensidade(int amostras, int intervaloMs, double& intensidade) const;

    /**
     * @brief Informa o canal ADC usado.
     * @return Número X do arquivo in_voltageX_raw.
     */
    int getCanal() const;

    /**
     * @brief Informa o diretório IIO usado.
     * @return Caminho do diretório do dispositivo IIO.
     */
    std::string getCaminhoIio() const;
};

#endif // SENSOR_VIBRACAO_H
