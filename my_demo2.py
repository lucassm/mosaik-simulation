"""Simulation demo."""

import mosaik
import mosaik.util
import my_seller_buyer_mosaik_sim

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import json

# ---------------------------------------
# configura os simuladores que serão 
# utilizados
# ---------------------------------------

SIM_CONFIG = {
    'VendedorSim': {
        'python': 'my_seller_buyer_mosaik_sim:VendedorSim',
    },
    'ConsumidorSim': {
        'python': 'my_seller_buyer_mosaik_sim:ConsumidorSim',
    },
}

# ---------------------------------------
# define inicio e tempo de execução 
# da simulação
# ---------------------------------------

verificacoes = 30

START = '12/03/2018 - 00:00:00'
END = verificacoes * 60

# ---------------------------------------
# define variavel com os dados de todos 
# os simuladores
# ---------------------------------------

world = mosaik.World(SIM_CONFIG)

# ---------------------------------------
# define as instancias de cada um dos 
# simuladores acoplados ao ambiente de
# simulação
# ---------------------------------------

vendedorsim = world.start('VendedorSim', eid_prefix='Vendedor_', start=START)
consumidorsim = world.start('ConsumidorSim', eid_prefix='Consumidor_', start=START)
# collector = world.start('Collector', step_size=60 * 15)

# ---------------------------------------
# cria as instâncias de cada um dos 
# simuladores acoplados ao ambiente de
# simulação 
# ---------------------------------------

# logica para criacao de prosumers somente na baixa tensao

consumidores = consumidorsim.Consumidor.create(5)
vendedor = vendedorsim.Vendedor()
#monitor = collector.Monitor()

# ---------------------------------------
# realiza as conexões existentes entre 
# os simuladores
# ---------------------------------------

# ---------------------------------------
# conecta os consumidores ao vendedor
# ---------------------------------------

# consumidores enviam ordens para o vendedor: 
#            ------------------------------------
#           | from consumidores --> to vendedor |
#           -------------------------------------
for consumidor in consumidores:
    world.connect(consumidor, vendedor, 'ordem', async_requests=True)

world.run(END)
