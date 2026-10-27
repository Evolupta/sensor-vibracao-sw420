param(
    [int]$Canal = 13,
    [string]$Porta = "COM3"
)

$port = New-Object System.IO.Ports.SerialPort $Porta, 115200, 'None', 8, 'One'
$port.ReadTimeout = 1000
$port.WriteTimeout = 1000
$port.Open()

Write-Host "=== MONITOR EM TEMPO REAL - STM32MP1-DK1 ($Porta | Canal $Canal) ===" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para encerrar.`n" -ForegroundColor Yellow

try {
    $port.Write("`r`n")
    Start-Sleep -Milliseconds 300
    $init = $port.ReadExisting()
    if ($init -match "login:") {
        $port.Write("root`r`n")
        Start-Sleep -Milliseconds 500
        $port.Write("root`r`n")
        Start-Sleep -Milliseconds 600
        $port.ReadExisting() | Out-Null
    }

    # Inicia loop continuo na placa executando o binario C++ /root/teste_sensor
    $port.Write("while true; do /root/teste_sensor $Canal; done`r`n")

    while ($true) {
        $texto = $port.ReadExisting()
        if ($texto) {
            Write-Host -NoNewline $texto
        }
        Start-Sleep -Milliseconds 50
    }
} finally {
    if ($port.IsOpen) {
        # Envia Ctrl+C (0x03) para parar o loop na placa antes de fechar a porta
        $port.Write([char]3)
        Start-Sleep -Milliseconds 200
        $port.Close()
    }
}
