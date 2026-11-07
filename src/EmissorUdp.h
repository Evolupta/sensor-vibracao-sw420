/**
 * @file EmissorUdp.h
 * @brief Declaração da classe que envia mensagens de texto por UDP a um servidor.
 *
 * Projeto de Programação Aplicada 2026 - Monitoramento Inteligente de Carga.
 */

#ifndef EMISSOR_UDP_H
#define EMISSOR_UDP_H

#include <string>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#endif

/**
 * @class EmissorUdp
 * @brief Encapsula um socket UDP (datagrama) configurado para um servidor fixo.
 *
 * O socket é criado no construtor e fechado no destrutor (RAII). Funciona em
 * Linux (kit STM32MP1 e Ubuntu) e em Windows (Winsock), o que permite testar o
 * envio no próprio PC.
 *
 * Exemplo de uso:
 * @code
 * EmissorUdp emissor("192.168.42.10", 5005);
 * if (emissor.estaPronto()) {
 *     emissor.enviar("VIBRACAO_SW420,1,1762345678123,2.618,V,1,52000");
 * }
 * @endcode
 *
 * @note UDP não garante entrega nem ordem; por isso o protocolo inclui um
 *       número de sequência (ver README.md).
 */
class EmissorUdp {
private:
#ifdef _WIN32
    SOCKET descritor;           ///< Socket UDP (Winsock).
#else
    int descritor;              ///< Descritor do socket UDP.
#endif
    sockaddr_in destino;        ///< Endereço IP/porta do servidor.
    bool pronto;                ///< true se o socket e o endereço são válidos.
    std::string ip;             ///< Endereço IP do servidor (texto).
    int porta;                  ///< Porta UDP do servidor.

    /** @brief Cópia desabilitada (o objeto é dono do socket). */
    EmissorUdp(const EmissorUdp&);
    /**
     * @brief Atribuição desabilitada (o objeto é dono do socket).
     * @return Não utilizado (declarada apenas para impedir a atribuição).
     */
    EmissorUdp& operator=(const EmissorUdp&);

public:
    /**
     * @brief Cria o socket e prepara o endereço do servidor.
     * @param ip Endereço IPv4 do servidor em texto (ex.: "192.168.42.10").
     * @param porta Porta UDP do servidor (1 a 65535).
     *
     * Se o IP ou a porta forem inválidos, ou o socket não puder ser criado,
     * o objeto fica "não pronto" (estaPronto() retorna false).
     */
    EmissorUdp(const std::string& ip, int porta);

    /** @brief Fecha o socket. */
    ~EmissorUdp();

    /**
     * @brief Informa se o emissor está apto a enviar.
     * @return true se o socket foi criado e o endereço é válido.
     */
    bool estaPronto() const;

    /**
     * @brief Envia uma mensagem de texto como um único datagrama UDP.
     * @param mensagem Texto a enviar (sem o caractere terminador).
     * @return true se o sistema operacional aceitou o envio; false caso contrário.
     */
    bool enviar(const std::string& mensagem) const;

    /**
     * @brief Informa o IP do servidor.
     * @return Endereço IPv4 em texto.
     */
    std::string getIp() const;

    /**
     * @brief Informa a porta do servidor.
     * @return Porta UDP.
     */
    int getPorta() const;
};

#endif // EMISSOR_UDP_H
