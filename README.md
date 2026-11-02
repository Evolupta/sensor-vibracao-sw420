# Sensor de Vibração SW-420 — Monitoramento Inteligente de Carga

Projeto de Programação Aplicada 2026 (IME) — grupo do sensor digital de vibração **SW-420**.  
Integrantes: **Ferraiollo, Brasil Barreto e Oppelt**.

## Estado: Entrega 2 — programa executado no kit físico

O sistema monitora a movimentação de uma carga sensível. Esta etapa implementa e documenta a leitura contínua do sensor SW-420 no kit **STM32MP1-DK1**, com Linux embarcado, registro de cada leitura e alerta ao detectar vibração. O envio por UDP e a interface gráfica são previstos para etapas futuras e **não fazem parte desta entrega**.

**Validação real realizada em 02/11/2026:** compilação cruzada ARM preparada na VM Ubuntu e execução no kit STM32MP1-DK1, com o sensor ligado à alimentação de 3,3 V. No ensaio registrado, o ADC **canal 13** foi utilizado explicitamente, com **0/30 detecções em repouso** e **13/50 detecções durante a vibração** (26% das amostras). O programa registrou pulsos altos de até 3,300 V e apresentou alertas. O log integral está em [`resultado_teste_kit.txt`](resultado_teste_kit.txt).

> **Interpretação:** 26% é a fração de amostras que capturaram nível alto durante a janela; não é a taxa de acerto nem a eficiência do sensor. Os pulsos do SW-420 são breves. O relógio do kit mostrava o ano 2000 durante a coleta, portanto as datas do log não representam a data civil do ensaio.

## Hardware e leitura

- **Sensor:** SW-420 com saída digital pelo comparador LM393.
- **Alimentação:** VCC em **3V3** (**nunca 5 V**), GND em GND.
- **Sinal DO:** conectado a uma entrada analógica da placa; o canal IIO **13** foi o que mostrou resposta clara ao movimento na montagem ensaiada. Confirme a correspondência entre pino físico e canal ADC no seu kit antes de reproduzir a montagem; as instruções antigas divergiam nesse mapeamento.
- **Interface:** `/sys/bus/iio/devices/iio:device0/in_voltageX_raw`, onde `X` é o canal numérico exposto pelo Linux.
- **Conversão:** `tensao = bruto * 3,3 / 65535` (referência e resolução usados no ensaio).
- **Detecção:** `VIBRANDO` quando a tensão da amostra é maior ou igual a **1,65 V** (nível alto).

A classe `SensorVibracao::lerAmostra` calcula valor bruto, tensão e estado a partir **da mesma leitura** do ADC, evitando inconsistência por múltiplas leituras sucessivas.

## Arquivos principais

| Arquivo | Descrição |
|---|---|
| `src/SensorVibracao.h/.cpp` | Classe de acesso ao ADC e interpretação de vibração; comentários Doxygen |
| `src/MonitorSensor.h/.cpp` | Laço de monitoramento, timestamp, alertas e resumo estatístico |
| `src/main.cpp` | Recebe os argumentos e instancia as classes |
| `Makefile` | Compilação nativa ou cruzada |
| `Doxyfile` | Configuração do Doxygen |
| `compilar_arm.sh` | Auxiliar de compilação usado na VM do projeto (ambiente e caminhos específicos) |
| `teste_sensor_arm` | Executável ARM pré-compilado fornecido com a Entrega 2 |
| `teste_no_kit.sh` | Teste de bancada em repouso (30) e vibração (50) |
| `resultado_teste_kit.txt` | Log integral da execução física validada, canal 13 |
| `resultado_compilacao_arm.txt` | Registro da compilação/testes em VM fornecido com a entrega |
| `INSTRUCOES_TESTE_KIT.md` | Guia de ligação, execução e diagnóstico no kit |

## Dependências

- Para compilar no PC Linux: `make` e compilador C++11 (`g++`).
- Para compilar para o kit: toolchain **`arm-buildroot-linux-gnueabihf-g++`** compatível com a imagem Linux instalada (SDK indicado pelo professor).
- Doxygen é opcional, usado para gerar documentação HTML.
- Para **executar** o binário ARM pré-compilado no kit não é necessário instalar a VM no PC que está conectado à placa, desde que o binário seja compatível com o Linux do kit.

## Compilação

### Compilação nativa (PC Linux)

```bash
make clean
make
```

Exemplo de teste sem hardware, com arquivo IIO simulado:

```bash
mkdir -p /tmp/iio_sim
echo 52000 > /tmp/iio_sim/in_voltage13_raw
./build/teste_sensor 13 100 5 /tmp/iio_sim
```

Esse teste simulado **não** substitui a validação com o SW-420 físico.

### Compilação cruzada ARM (VM Ubuntu com SDK configurado)

```bash
make clean
make CXX=arm-buildroot-linux-gnueabihf-g++
file build/teste_sensor
```

O comando `file` deverá identificar um executável ARM de 32 bits compatível com a ABI e o sistema da placa. Se a toolchain não estiver no `PATH`, use seu caminho absoluto com `make CXX=/caminho/para/arm-buildroot-linux-gnueabihf-g++`.

O script `compilar_arm.sh` faz a compilação e testes no ambiente específico da VM utilizada pelo grupo; ele utiliza a pasta compartilhada `projeto` e pode exigir adaptação dos caminhos em outros computadores.

## Transferência e execução no kit

**Com Ethernet**, usando os endereços da bancada, se estiverem configurados:

```bash
scp build/teste_sensor root@192.168.42.2:/home/root/teste_sensor
scp teste_no_kit.sh root@192.168.42.2:/home/root/teste_no_kit.sh
ssh root@192.168.42.2
```

Alternativamente, transfira `teste_sensor_arm` como `/home/root/teste_sensor` e o script usando outro método já verificado para a configuração do kit (por exemplo, porta serial com Tera Term). A transferência serial depende da interface disponível; **a mera mensagem de conclusão de um script não comprova que os arquivos foram recebidos**. Confirme os arquivos e seu hash antes de executar.

No terminal Linux do kit:

```sh
mkdir -p /home/root
cd /home/root
chmod +x teste_sensor
sh teste_no_kit.sh 13
```

O script realiza **30 leituras com o sensor em repouso**, conta 5 segundos e então realiza **50 leituras durante o movimento**, com intervalo de 100 ms. O resultado é escrito em `/home/root/resultado_teste_kit.txt` e também exibido no terminal.

### Execução direta / monitoramento contínuo

```sh
cd /home/root
./teste_sensor 13 100 0    # canal 13, intervalo de 100 ms, contínuo até Ctrl+C
./teste_sensor 13 100 50   # canal 13, 50 amostras
```

Uso: `./teste_sensor [canal] [intervalo_ms] [leituras] [caminho_iio]`.
O executável aceita qualquer canal exposto pelo IIO; se nenhum for informado, **o padrão original do programa é 6**, mas **o ensaio validado nesta entrega utilizou explicitamente o canal 13**. Por isso, para reproduzir os dados abaixo, forneça `13` como argumento.

## Testes realizados e resultados

| Condição | Amostras | Alertas | Resultado |
|---|---:|---:|---|
| Sensor parado, canal 13 | 30 | 0 | **0,0%** de amostras com vibração |
| Sensor movimentado, canal 13 | 50 | 13 | **26,0%** de amostras com vibração |

- **Repouso:** ADC bruto de **2522 a 2875**, aproximadamente **0,127 a 0,145 V**, sem alertas.
- **Com movimento:** ADC bruto de **2510 a 65535**; amostras altas atingiram **3,300 V**, gerando `VIBRANDO <<< ALERTA`.
- O log registra o ambiente **Linux STM32MP1 6.9.8 armv7l**, confirmando execução na plataforma embarcada. Não foi registrada uma medição de desempenho ou uma taxa de acerto em eventos físicos independentes.

Trecho da leitura real:

```text
2000-01-01 00:09:41.369 | #   8 | bruto = 65535 | tensao = 3.300 V | VIBRANDO  <<< ALERTA
2000-01-01 00:09:41.470 | #   9 | bruto =  2583 | tensao = 0.130 V | repouso
...
Leituras: 50 | com vibracao: 13 (26.0 %) | bruto minimo: 2510 | bruto maximo: 65535
```

Documentos de evidência:

- [`resultado_teste_kit.txt`](resultado_teste_kit.txt): log integral do ensaio de 80 amostras no canal 13.
- [`resultado_compilacao_arm.txt`](resultado_compilacao_arm.txt): saída registrada da compilação em VM.
- [`evidencia_compilacao_vm.png`](evidencia_compilacao_vm.png): imagem de compilação da etapa anterior já mantida no repositório.

Não foi anexada uma fotografia física da ligação do sensor; caso seja exigida pelo professor, é necessário adicioná-la como evidência complementar.

## Documentação e próximos passos

```bash
make doc
# abrir doc/html/index.html
```

As classes estão documentadas com comentários Doxygen. A integração UDP, o servidor central e a interface gráfica permanecem **fora do escopo desta Entrega 2**.
