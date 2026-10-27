# Makefile - Sensor de Vibracao SW-420
#
# Compilacao nativa (PC):
#     make
# Compilacao cruzada para o kit STM32MP1-DK1 (apos carregar o ambiente da toolchain):
#     make CXX=arm-buildroot-linux-gnueabihf-g++

CXX      ?= g++
CXXFLAGS += -std=c++11 -Wall -Wextra -O2
BUILD    = build
SRC      = src/main.cpp src/SensorVibracao.cpp
ALVO     = $(BUILD)/teste_sensor

all: $(ALVO)

$(ALVO): $(SRC) src/SensorVibracao.h
	mkdir -p $(BUILD)
	$(CXX) $(CXXFLAGS) $(SRC) -o $(ALVO)

doc:
	doxygen Doxyfile

clean:
	rm -rf $(BUILD) doc

.PHONY: all doc clean