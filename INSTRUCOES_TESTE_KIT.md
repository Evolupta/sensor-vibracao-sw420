# Instruções de teste no kit STM32MP1-DK1 — Entrega 3 (SW-420)

## Montagem e segurança

Antes de energizar, fotografe as conexões. Alimente o SW-420 somente com **3,3 V**
(VCC → 3V3; GND → GND; DO → entrada do ADC). Mantenha o cartão SD no kit.
O ensaio documentado usou **canal IIO 13**. Confirme qual pino físico da montagem
corresponde a esse canal; não pressuponha o mapeamento A4/A5 sem conferir.

## Topologia de rede testada em 07/11/2026

- Kit STM32 → **cabo RJ45 na porta LAN do roteador**.
- PC Windows → Wi-Fi do mesmo roteador (não precisa de Ethernet no PC).
- Micro-USB do kit → PC para acesso serial via Tera Term (115200, 8N1).
- Kit: `10.0.1.101`; PC: `10.0.1.100`; UDP: `5005`.

Os IPs são apenas exemplos **registrados no ensaio**: use `ip addr show eth0`
no kit e `ipconfig` no Windows para descobrir IPs atuais.

## 1. Servidor UDP no Windows

No PowerShell, dentro da pasta da Entrega 3:

```powershell
python -u servidor_udp.py --porta 5005 --log log_sensor.csv --max 80
```

Se o firewall bloquear pacotes de entrada, libere UDP/5005 para a rede local.
Mantenha o processo aberto antes de iniciar o kit.

## 2. Transferir executável ARM e script

Na pasta onde estão os arquivos, substitua o endereço do kit se necessário:

```powershell
scp -O .\teste_sensor_arm root@10.0.1.101:/home/root/teste_sensor
scp -O .\teste_no_kit.sh root@10.0.1.101:/home/root/teste_no_kit.sh
```

## 3. Teste no kit (Tera Term, login root)

```sh
mkdir -p /home/root
cd /home/root
chmod +x teste_sensor
sh teste_no_kit.sh 10.0.1.100 13 5005
```

Deixe o SW-420 parado nas **30 primeiras leituras**. Após a contagem de 5 s,
movimente-o durante as **50 leituras seguintes**. O resultado é gravado em
`/home/root/resultado_teste_kit.txt`.

## 4. Critérios de aceitação do ensaio

- 30 + 50 linhas de leitura; o kit relata `Pacotes UDP enviados: 30` e `50` e zero falhas.
- Servidor: `validos: 80 | invalidos: 0 | perdidos: 0 | fora de ordem: 0`.
- CSV com 80 registros e sequência `1..30`, seguida de `1..50` (reinício esperado).
- Alertas coerentes: repouso sem detecções e pelo menos um alerta durante a movimentação.
- `python verificar_udp_entrega3.py` retorna aprovação do CSV.

**Resultado efetivo de 07/11/2026:** 0/30 alertas em repouso; 15/50 durante
vibração; 80/80 datagramas recebidos no PC sem perdas/erros.

## Problemas comuns

- **Ping sem resposta, UDP recebendo:** foi observado no ensaio; ICMP não é pré-requisito para UDP.
- **UDP não chega:** confira IP do PC, Wi-Fi na mesma rede, porta 5005 e firewall.
- **Arquivo não executa:** confira transferência, permissões (`chmod +x`) e arquitetura ARM.
- **Sem alertas:** confirme canal IIO e ligação física; não mude fios com a placa energizada.
- **Data 2000 no kit:** relógio não sincronizado; não usar timestamp da placa como hora civil.

Ao publicar, anexe os logs do kit e do servidor, o CSV, o README e a foto da montagem (quando disponível).
