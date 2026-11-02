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

#include "SensorVibracao.h"

/**
 * @class MonitorSensor
 * @brief Lê o sensor periodicamente e imprime cada amostra em um fluxo de saída.
 *
 * Cada linha impressa contém: data/hora local, número da leitura, valor bruto
 * do ADC, tensão em volts, estado (VIBRANDO / repouso) e um marcador de alerta.
 * A classe também acumula estatísticas (mínimo, máximo e total de amostras com
 * vibração) exibidas ao final da execução.
 *
 * Exemplo de uso:
 * @code
 * SensorVibracao sensor(13);
 * MonitorSensor monitor(sensor, 100, 0);   // a cada 100 ms, sem limite de leituras
 * monitor.executar(std::cout);
 * @endcode
 */
class MonitorSensor {
private:
    const SensorVibracao& sensor;   ///< Sensor monitorado.
    int intervaloMs;                ///< Pausa entre leituras, em milissegundos.
    int totalLeituras;              ///< Quantidade de leituras (0 = contínuo).

    /**
     * @brief Monta o texto de data/hora local no formato AAAA-MM-DD HH:MM:SS.mmm.
     * @return Texto com o instante atual.
     */
    std::string horaAtual() const;

public:
    /**
     * @brief Constrói o monitor.
     * @param sensor Sensor a ser lido (deve existir enquanto o monitor existir).
     * @param intervaloMs Pausa entre leituras em ms (valores negativos viram 0).
     * @param totalLeituras Quantidade de leituras; 0 ou negativo = até ser interrompido (Ctrl+C).
     */
    MonitorSensor(const SensorVibracao& sensor, int intervaloMs, int totalLeituras);

    /**
     * @brief Executa o laço de monitoramento.
     * @param saida Fluxo onde cada leitura é impressa.
     * @return 0 se terminou normalmente; 1 se uma leitura falhou (ex.: canal inexistente).
     */
    int executar(std::ostream& saida) const;
};

#endif // MONITOR_SENSOR_H
