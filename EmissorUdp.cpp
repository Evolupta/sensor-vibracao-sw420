/**
 * @file EmissorUdp.cpp
 * @brief Implementação da classe de envio de mensagens por UDP.
 */

#include "EmissorUdp.h"

#include <cstring>

#ifndef _WIN32
#include <unistd.h>
#endif

EmissorUdp::EmissorUdp(const std::string& ip, int porta)
    : pronto(false), ip(ip), porta(porta) {
    std::memset(&destino, 0, sizeof(destino));

    if (porta < 1 || porta > 65535) {
        return;
    }

#ifdef _WIN32
    WSADATA dados;
    if (WSAStartup(MAKEWORD(2, 2), &dados) != 0) {
        return;
    }
    descritor = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (descritor == INVALID_SOCKET) {
        WSACleanup();
        return;
    }
#else
    descritor = socket(AF_INET, SOCK_DGRAM, 0);
    if (descritor < 0) {
        return;
    }
#endif

    destino.sin_family = AF_INET;
    destino.sin_port = htons((unsigned short)porta);
    if (inet_pton(AF_INET, ip.c_str(), &destino.sin_addr) != 1) {
#ifdef _WIN32
        closesocket(descritor);
        WSACleanup();
#else
        close(descritor);
#endif
        return;
    }

    pronto = true;
}

EmissorUdp::~EmissorUdp() {
    if (!pronto) {
        return;
    }
#ifdef _WIN32
    closesocket(descritor);
    WSACleanup();
#else
    close(descritor);
#endif
}

bool EmissorUdp::estaPronto() const {
    return pronto;
}

bool EmissorUdp::enviar(const std::string& mensagem) const {
    if (!pronto) {
        return false;
    }
    int enviados = (int)sendto(descritor, mensagem.c_str(), (int)mensagem.size(), 0,
                               (const sockaddr*)&destino, sizeof(destino));
    return enviados == (int)mensagem.size();
}

std::string EmissorUdp::getIp() const {
    return ip;
}

int EmissorUdp::getPorta() const {
    return porta;
}
