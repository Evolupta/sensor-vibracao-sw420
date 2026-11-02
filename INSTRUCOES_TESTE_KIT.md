# Guia de teste — SW-420 / Entrega 2 / STM32MP1-DK1

## 1. Segurança e montagem

1. **Desligue a alimentação do kit.** Conecte **VCC no 3V3 (nunca 5 V)**, **GND no GND** e **DO na entrada analógica utilizada no ensaio**.
2. Tire uma fotografia da ligação e verifique a identificação do pino no manual da placa. A versão antiga deste guia associava A4 ao canal 6, porém o resultado físico conclusivo desta entrega foi obtido no **canal IIO 13**. Não presuma a correspondência pino/canal sem conferi-la.
3. Energize o kit apenas após conferir as ligações e mantenha o cartão SD instalado.

## 2. Pré-requisitos

- Kit com Linux em execução e acesso ao terminal, por serial (115200, 8N1) ou SSH.
- Arquivos `teste_sensor_arm` e `teste_no_kit.sh` desta entrega.
- Binário ARM compatível com o Linux do kit. A ferramenta `file` identifica seu formato em um PC Linux.

## 3. Transferência (Ethernet)

Se a rede da bancada usar kit `192.168.42.2` e PC `192.168.42.10`:

```bash
scp teste_sensor_arm root@192.168.42.2:/home/root/teste_sensor
scp teste_no_kit.sh root@192.168.42.2:/home/root/
ssh root@192.168.42.2
```

Se não houver Ethernet, os arquivos podem ser transferidos por serial com uma solução adequada ao terminal disponível. A rota serial exige verificação de integridade; tentativas iniciais de envio direto por PowerShell falharam nesta bancada, portanto **não considere transferência bem-sucedida sem confirmar o arquivo no Linux**.

## 4. Testar no kit

```sh
mkdir -p /home/root
cd /home/root
ls -l teste_sensor teste_no_kit.sh
chmod +x teste_sensor
sh teste_no_kit.sh 13
```

- Primeiro ciclo: **30 amostras em repouso** (não toque no sensor).
- Depois de uma contagem de **5 segundos**, movimente o sensor por **50 amostras**.
- Intervalo entre amostras: **100 ms**.
- Saída: `/home/root/resultado_teste_kit.txt`.

Para monitoramento contínuo:

```sh
cd /home/root
./teste_sensor 13 100 0
# parar com Ctrl+C
```

## 5. Validar a evidência

Confira no resultado:

- O canal utilizado (`canal 13`).
- Ausência de alertas em repouso.
- Algumas linhas com `VIBRANDO <<< ALERTA` durante a vibração.
- Resumo de ambas as partes.

No ensaio documentado, houve **0/30** amostras ativas em repouso e **13/50** durante o movimento. O arquivo [`resultado_teste_kit.txt`](resultado_teste_kit.txt) contém o log completo. A data interna apresentada pelo kit era 2000 por falta de sincronização do relógio.

## 6. Diagnóstico rápido

| Sintoma | Ação |
|---|---|
| `No such file or directory` | Verifique os nomes, o diretório e a transferência do binário/script |
| `Permission denied` | Execute `chmod +x teste_sensor` |
| `Erro: nao foi possivel ler o canal ADC` | Verifique `ls /sys/bus/iio/devices/iio:device0/in_voltage*_raw` e a numeração real do canal |
| Nenhum alerta durante movimentos | Confira a ligação DO, a escolha do canal e o ajuste de sensibilidade do módulo |
| Serial não responde | Configure 115200, 8N1, sem controle de fluxo; não abra a mesma COM em dois programas |
| Data do log aparece como 2000 | Relógio Linux não sincronizado; não modifica a leitura bruta do ADC |

Ao finalizar, encaminhe o `resultado_teste_kit.txt` e, se disponível, a foto da montagem. Publique um commit Git com código, instruções e evidências, e **entregue no Classroom o link para o commit final**.
