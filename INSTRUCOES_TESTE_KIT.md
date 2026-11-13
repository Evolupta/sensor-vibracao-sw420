> **Validação da Entrega 4 já realizada em 13/11/2026:** dois ensaios de 80 registros, arquivados no README e em `VALIDACAO_ENTREGA4.md`. Repetir os passos abaixo somente se for necessária uma nova evidência; não é obrigatório repetir apenas para publicar o código.

# Entrega 4 — Validação física da interface SW-420 (STM32MP1-DK1)

**Objetivo:** demonstrar no computador (Windows) a leitura atual, a curva histórica de 30/60 segundos, o alerta visual e o salvamento em CSV **recebendo UDP real do kit**, não apenas do simulador.

## Montagem

- Sensor SW-420 em **3V3** e GND. Com o kit desligado, fotografe a ligação do sinal e confira o pino; no teste validado da Entrega 3, a leitura correta foi `in_voltage13_raw` (canal **13**). Nunca alimente o sensor com 5 V.
- Conecte kit STM32 por **RJ45 a uma porta LAN do roteador**; computador ao Wi-Fi da **mesma rede**; mantenha Micro-USB para o Tera Term (115200 8N1), e USB-C para alimentação.
- No teste anterior, os IPs foram **kit 10.0.1.101** e **PC 10.0.1.100**, mas podem mudar. Descubra os endereços atuais: no PowerShell `ipconfig`; no Tera Term `ip addr show eth0`. Não reutilize IPs se tiverem mudado.

## 1. Testar a conectividade (PowerShell)

```powershell
ping IP_DO_KIT
```

Se o ping não responder, confira a LAN. Lembre que o ping pode ser bloqueado mesmo quando UDP funciona.

## 2. Iniciar a interface gráfica (PowerShell, pasta Entrega 4)

```powershell
python --version
python interface_grafica.py --porta 5005 --log log_sensor.csv --relatorio relatorio_monitoramento.txt
```

**Não use `--demo` na validação física** e não abra `servidor_udp.py` ao mesmo tempo na porta 5005, pois ambos recebem UDP e podem competir pelos datagramas. Verifique que a janela esteja aguardando o kit. A interface salva CSV automaticamente e cria arquivo com sufixo se o anterior já existir.

Se o Firewall do Windows bloquear UDP, abra PowerShell **como administrador** e crie uma regra limitada à rede privada:

```powershell
New-NetFirewallRule -DisplayName "Sensor SW420 UDP 5005" -Direction Inbound -Protocol UDP -LocalPort 5005 -Profile Private -Action Allow
```

## 3. Executar o kit (Tera Term ou SSH)

Se a Entrega 3 já deixou `/home/root/teste_sensor` e `teste_no_kit.sh`, **não transfira arquivos novamente**: use os mesmos executáveis comprovados. Caso precise transferir, no PC:

```powershell
scp -O teste_sensor_arm root@IP_DO_KIT:/home/root/teste_sensor
scp -O teste_no_kit.sh root@IP_DO_KIT:/home/root/teste_no_kit.sh
```

No terminal do kit (preserve o log anterior antes que o script o sobrescreva):

```sh
cd /home/root
[ -f resultado_teste_kit.txt ] && cp resultado_teste_kit.txt resultado_teste_kit_backup_entrega3.txt
chmod +x teste_sensor
sh teste_no_kit.sh IP_DO_PC 13 5005
```

O teste registra 30 amostras em repouso, espera 5 s e registra 50 com vibração. Mantenha o sensor parado na primeira fase; chacoalhe na segunda. Observe o valor na GUI, a curva, o banner vermelho, a contagem de 80 pacotes e o tempo desde a última atualização.

## 4. Guardar evidências da Entrega 4

1. Capture **um print verdadeiro da interface em repouso** e **outro quando ocorrerem alertas reais** (Windows: `Win + Shift + S`). A interface tem botão de captura que depende opcionalmente da biblioteca Pillow.
2. Feche a interface para gerar `relatorio_monitoramento.txt` (ou arquivo com sufixo) e confira os contadores de pacotes recebidos.
3. Guarde `log_sensor.csv` (ou o nome com sufixo) e confira a sequência `1..30`, depois `1..50`, e 80 amostras totais. A perda registrada deve ser zero se nenhuma sequência faltar. A reinicialização entre as fases é esperada.
4. Recupere o log do kit `resultado_teste_kit.txt` via `scp root@IP_DO_KIT:/home/root/resultado_teste_kit.txt .` e compare os valores/alertas com o CSV da GUI.
5. Rode `python verificar_gui_entrega4.py log_sensor.csv --ip-kit IP_DO_KIT` no PC (ajuste o nome do CSV, se tiver sufixo).
6. Envie um **commit final** com README atualizado, dados verdadeiros, prints da execução real e fontes na pasta `src`. Só então copie o link do commit para o Google Classroom.

**Separação essencial:** `evidencia_interface_*_SIMULACAO.png`, `log_gui_simulacao.csv` e `relatorio_gui_simulacao.txt` demonstram apenas o simulador. Não apresente esses arquivos como prova de recepção do kit físico.
