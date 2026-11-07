/**
 * @file MonitorSensor.h
 * @brief Declaração da classe que executa o monitoramento contínuo do SW-420.
 *
 * Projeto de Programação Aplicada 2026 - Monitoramento Inteligente de Carga.
 */

#ifndef MONITOR_SENSOR_H
#define MONITOR_SENSOR_H

#include <iosfwd>
#include <string>

#include "EmissorUdp.h"
#include "SensorVibracao.h"

/**
 * @class MonitorSensor
 * @brief Lê o sensor periodicamente, imprime cada amostra e (opcionalmente) a envia por UDP.
 *
 * Cada linha impressa contém: data/hora local, número da leitura, valor bruto
 * do ADC, tensão em volts, estado (VIBRANDO / repouso) e, se houver emissor
 * UDP, o resultado do envio. Ao final é exibido um resumo.
 *
 * Mensagem UDP (texto CSV, uma por leitura, sem quebra de linha):
 * @code
 * id_sensor,sequencia,timestamp_ms,valor,unidade,vibracao,bruto
 * VIBRACAO_SW420,12,1762345678123,2.618,V,1,52000
 * @endcode
 *
 * | Campo | Descrição |
 * |---|---|
 * | id_sensor | Identificador do sensor/grupo (padrão `VIBRACAO_SW420`) |
 * | sequencia | Contador de pacotes, começa em 1 (detecta perdas/ordem) |
 * | timestamp_ms | Instante da leitura: milissegundos desde 01/01/1970 UTC |
 * | valor | Tensão no pino do sensor, com 3 casas decimais |
 * | unidade | Unidade do valor: `V` |
 * | vibracao | `1` = vibração detectada, `0` = repouso |
 * | bruto | Valor bruto do ADC (0 a 65535) |
 *
 * Exemplo de uso:
 * @code
 * SensorVibracao sensor(6);
 * EmissorUdp emissor("192.168.42.10", 5005);
 * MonitorSensor monitor(sensor, 100, 0, &emissor);   // a cada 100 ms, contínuo
 * monitor.executar(std::cout);
 * @endcode
 */
class MonitorSensor {
private:
    const SensorVibracao& sensor;   ///< Sensor monitorado.
    int intervaloMs;                ///< Pausa entre leituras, em milissegundos.
    int totalLeituras;              ///< Quantidade de leituras (0 = contínuo).
    const EmissorUdp* emissor;      ///< Emissor UDP (nullptr = não envia).
    std::string idSensor;           ///< Identificador do sensor no protocolo.

    /**
     * @brief Instante atual em milissegundos desde 01/01/1970 UTC.
     * @return Timestamp em milissegundos.
     */
    long long timestampMs() const;

    /**
     * @brief Converte um timestamp em texto local AAAA-MM-DD HH:MM:SS.mmm.
     * @param ms Milissegundos desde 01/01/1970 UTC.
     * @return Texto com a data/hora local.
     */
    std::string formatarHora(long long ms) const;

    /**
     * @brief Monta a mensagem CSV do protocolo UDP.
     * @param sequencia Número de sequência do pacote.
     * @param ms Timestamp da leitura em milissegundos.
     * @param tensao Tensão em volts.
     * @param vibrando true se há vibração.
     * @param bruto Valor bruto do ADC.
     * @return Texto da mensagem (sem quebra de linha).
     */
    std::string montarMensagem(int sequencia, long long ms, double tensao,
                               bool vibrando, int bruto) const;

public:
    /**
     * @brief Constrói o monitor.
     * @param sensor Sensor a ser lido (deve existir enquanto o monitor existir).
     * @param intervaloMs Pausa entre leituras em ms (valores negativos viram 0).
     * @param totalLeituras Quantidade de leituras; 0 ou negativo = até ser interrompido (Ctrl+C).
     * @param emissor Emissor UDP já configurado; nullptr desliga o envio.
     * @param idSensor Identificador do sensor no protocolo (sem vírgulas).
     */
    MonitorSensor(const SensorVibracao& sensor, int intervaloMs, int totalLeituras,
                  const EmissorUdp* emissor = 0,
                  const std::string& idSensor = "VIBRACAO_SW420");

    /**
     * @brief Executa o laço de monitoramento.
     * @param saida Fluxo onde cada leitura é impressa.
     * @return 0 se terminou normalmente; 1 se uma leitura falhou (ex.: canal inexistente).
     */
    int executar(std::ostream& saida) const;
};

#endif // MONITOR_SENSOR_H
