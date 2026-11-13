# Relatório de validação da Entrega 4 — SW-420

**Data civil dos ensaios:** 13/11/2026, segundo o relógio do computador receptor.  
**Plataforma:** STM32MP1-DK1 / sensor SW-420; comunicação UDP IPv4 por LAN, porta 5005, receptor gráfico em Python/Tkinter.  
**Origem UDP registrada:** 10.0.1.101.  
**Limiar:** 1,65 V; canal utilizado na validação física anterior: IIO 13.

## Resultados efetivamente documentados

| Indicador | Ensaio 10h26 | Ensaio 10h31 |
|---|---:|---:|
| Datagramas válidos gravados na GUI | 80 | 80 |
| Vibrações registradas em repouso | 0/30 | 0/30 |
| Vibrações registradas com movimento | 15/50 | 7/50 |
| Pacotes perdidos | 0 | 0 |
| Pacotes inválidos | 0 | 0 |
| Pacotes fora de ordem | 0 | 0 |
| Tensão mínima (V) | 0,115 | 0,102 |
| Tensão média (V) | 0,729 | 0,409 |
| Tensão máxima (V) | 3,300 | 3,300 |
| Intervalo entre as duas fases | 5,10 s | 5,05 s |

Cada um dos CSVs contém 80 linhas de dados mais cabeçalho, origem `10.0.1.101`, sequência de 1 a 30 seguida por 1 a 50, correspondência da tensão com o bruto ADC (`bruto * 3,3/65535`) e alerta coerente com limiar de 1,65 V. As estatísticas coincidem com os dois relatórios textuais gerados pela GUI.

**Verificações adicionais (ambiente local):** código C++ da Entrega 4 compilado com `-std=c++11 -Wall -Wextra -Wpedantic -Werror -O2` sem erros; compilação sintática do Python aprovada; teste automatizado da GUI em display virtual com UDP por loopback aprovado, incluindo alerta, sinal interrompido, registro CSV e preservação de arquivo preexistente. Esse teste local é distinto dos ensaios físicos de 13/11.

## Evidências

- [`evidencia_interface_kit.png`](evidencia_interface_kit.png): captura original feita com a GUI recebendo o kit; mostra 30 pacotes em repouso e pausa entre as fases.
- [`grafico_ensaios_fisicos.png`](grafico_ensaios_fisicos.png): visualização derivada dos dois CSVs de origem física; **não** representa uma captura ao vivo.
- [`log_sensor_20261113_102602.csv`](log_sensor_20261113_102602.csv) e [`log_sensor_20261113_103150.csv`](log_sensor_20261113_103150.csv): registros integrais do servidor gráfico.
- [`relatorio_monitoramento_20261113_102602.txt`](relatorio_monitoramento_20261113_102602.txt) e [`relatorio_monitoramento_20261113_103150.txt`](relatorio_monitoramento_20261113_103150.txt): resumos e eventos de alerta emitidos pela GUI.

## Interpretação e limitações

- O aviso “SEM SINAL” surge após 3 segundos sem dados. A interrupção observada de cerca de 5 segundos correspondeu à pausa programada do script de bancada, **não** demonstra perda de pacotes.
- Os timestamps gerados pelo kit estão desalinhados da data civil. Os horários dos ensaios e a duração da pausa foram obtidos no PC (`recebido_em`).
- 15/50 e 7/50 significam amostras com nível alto durante movimento; **não** são índices de acurácia do sensor.
- Não foi disponibilizado print do banner vermelho capturado ao vivo nem log do console do kit específico dessas duas sessões; os alertas aparecem nos CSVs e relatórios. Não reivindicar tais documentos como existentes.
- A foto da fiação com o kit desligado, exigida nas instruções gerais, não foi incluída nos arquivos deste pacote; confirme se foi entregue anteriormente.

**Conclusão:** os dois registros físicos confirmam que a GUI recebeu e salvou dados do kit, identificou vibrações, manteve a sequência esperada e não registrou perdas ou inválidos nos ensaios observados. O sistema atendeu aos itens funcionais da Entrega 4 no escopo demonstrado.
