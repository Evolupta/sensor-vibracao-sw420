# Relatório de validação — Entrega 3 (07/11/2026)

## Escopo

Verificar o envio de cada leitura real do SW-420 via socket UDP a um servidor Windows,
com kit STM32MP1-DK1 conectado por Ethernet à LAN do roteador e PC conectado por Wi-Fi.
Este relatório registra somente o que os arquivos de evidência permitem concluir.

## Evidências e ambiente

- Sistema do kit: Linux STM32MP1 6.9.8 armv7l.
- Canal ADC do ensaio: 13; fundo de escala assumido pelo programa: 3,3 V e 65535.
- IP de origem observado no servidor: `10.0.1.101`.
- Destino configurado no kit: `10.0.1.100:5005`.
- Protocolo CSV: `id_sensor,sequencia,timestamp_ms,valor,unidade,vibracao,bruto`.
- Arquivos: `resultado_teste_kit.txt`, `log_sensor.csv`, `log_servidor_console.txt`.

## Verificação cruzada

| Teste | Resultado |
|---|---:|
| Leituras no kit (30 repouso + 50 movimento) | 80 |
| Datagramas recebidos registrados em CSV | 80 |
| Mensagens no console do servidor | 80 |
| Divergências kit × CSV (sequência, bruto, tensão, estado) | 0 |
| Sequência do CSV | 1–30 e 1–50, sem lacunas |
| Alertas durante repouso | 0/30 |
| Alertas durante movimento | 15/50 (30%) |
| Servidor: mensagens inválidas | 0 |
| Servidor: perdas detectadas | 0 |
| Servidor: fora de ordem | 0 |
| Compilação de fontes C++11 no ambiente de revisão (`-Wall -Wextra -Wpedantic -Werror`) | Aprovada |

Os arquivos `log_sensor.csv` e `resultado_teste_kit.txt` correspondem em todos
os 80 registros. O script `verificar_udp_entrega3.py` também devolveu
`RESULTADO: CONSISTENCIA DO CSV APROVADA`.

O script de bancada faz **duas execuções** do emissor UDP, uma para cada fase,
por isso a contagem de sequência volta a 1 antes da fase de vibração.

## Limitações documentadas

1. O `ping` executado no kit não recebeu resposta (2/2), mas a comunicação UDP
   foi confirmada pelo receptor. O motivo da ausência de ICMP não foi identificado.
2. O relógio do kit indicava o ano 2000; os timestamps emitidos não estão
   sincronizados com a data civil. O PC gravou seu próprio campo `recebido_em`.
3. A detecção de 30% corresponde a 15 amostras altas em uma janela de 50, não
   a taxa de reconhecimento de impactos independentes nem à confiabilidade geral.
4. Não foi fornecida neste conjunto uma foto da montagem física com o kit desligado;
   ela deve ser acrescentada, se ainda não foi apresentada ao professor.
5. A compilação cruzada ARM é evidenciada no arquivo da VM e o binário foi executado
   no kit. O relatório não atesta conformidade com testes não realizados.

## Conclusão

**Aprovado no escopo da Entrega 3:** geração das leituras, envio UDP pela rede
local, recepção, validação de protocolo e persistência em CSV. O servidor
recebeu todos os 80 datagramas desta sessão sem perdas detectadas.
A interface gráfica permanece para a etapa seguinte do projeto.
