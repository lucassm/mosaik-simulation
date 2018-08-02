# """Simulation demo."""

import mosaik
import mosaik.util

from prosumer import generate_timeseries
import random

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import json

# ---------------------------------------
# configura os simuladores que serão 
# utilizados
# ---------------------------------------

SIM_CONFIG = {
    'ProsumerSim': {
        'python': 'prosumer_sim_with_mosaik_api:ProsumerSim',
    },
    'AgentContoller': {
        'python': 'agent_storage_control:AgentStorageControl',
    },
    'MyGridSim': {
        'python': 'mygrid_sim_with_mosaik_api:MyGrid',
    },
    'MarketSim': {
        'python': 'market_sim_with_mosaik_api:MarketSim',
    },
    'CustomerSim': {
        'python': 'market_sim_with_mosaik_api:CustomerSim',
    },
    'Collector': {
        'cmd': 'python collector.py %(addr)s',
    },
}

DEBUG = False

# ---------------------------------------
# define inicio e tempo de execução 
# da simulação
# ---------------------------------------

verifications = 60 * 12

STEP = 1 # step dos simuladores em minutos
START = '12/03/2018 - 00:00:00'
END = verifications * STEP * 60

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

prosumersim = world.start('ProsumerSim', eid_prefix='Prosumer_', start=START, step_size=STEP * 60, debug=DEBUG)
agent_controller = world.start('AgentContoller', eid_prefix='Agent_', start=START, step_size=STEP * 60, debug=DEBUG)
mygridsim = world.start('MyGridSim', step_size=STEP * 60 * 15, debug=DEBUG)
marketsim = world.start('MarketSim', eid_prefix='Market_', start=START, step_size=STEP * 60, debug=DEBUG)
customersim = world.start('CustomerSim', eid_prefix='Customer_', start=START, step_size=STEP * 60, debug=DEBUG)

collector = world.start('Collector', step_size=STEP * 60)

# ---------------------------------------
# cria as instâncias de cada um dos 
# simuladores acoplados ao ambiente de
# simulação 
# ---------------------------------------

# logica para criacao de prosumers somente na baixa tensao

data = json.load(open('force.json', 'r'))

# define o grau de penetração de DER na rede
der_penetration = 0.5

# definie a quantidade de consumidores que posssuem DER
prosumers_number = int(der_penetration * len(data['nodes']))

# amostra randomicamente os consumidores que possuem DER, deacordo com
# a quantidade especificada na variável prosumers_number
# TODO:
# existe uma pendência neste tópico, pois só pode haver prosumidor na baixa tensão
# e caso um dos nós escolhidos seja da média então este nó será excluído e o grau de
# de penetração de gd definido não será atendido. 
prosumers_with_der =  random.sample(range(len(data['nodes'])), prosumers_number)

prosumers_id = []
for i in data['nodes']:
    if i['voltage_level'] == 'low voltage':
        if i['name'] in prosumers_with_der:
            prosumers_id.append((i['name'], True))
        else:
            prosumers_id.append((i['name'], False))

prosumers = prosumersim.Prosumer.create(len(prosumers_id), prosumers_id=prosumers_id)
agents = agent_controller.AgentStorageControl.create(len(prosumers), prosumers_id=prosumers_id)
customers = customersim.Customer.create(len(prosumers_id), prosumers_id=prosumers_id)

grid = mygridsim.Grid(gridfile=open('force.json', 'r'))
market = marketsim.Market()
monitor = collector.Monitor()

# ---------------------------------------
# realiza as conexões existentes entre 
# os simuladores
# ---------------------------------------


# ---------------------------------------
# conecta os prosumers aos agentes de 
# controle
# ---------------------------------------
for prosumer, agent in zip(prosumers, agents):
    world.connect(prosumer,
                  agent,
                  'datetime',
                  'storage',
                  async_requests=True)


# ---------------------------------------
# conecta os prosumers aos customers 
# e os customers ao market de energia
# ---------------------------------------

for prosumer, customer in zip(prosumers, customers):
    world.connect(customer, market, 'order', async_requests=True)
    world.connect(prosumer, customer, 'power_input', 'power_forecast')

# ---------------------------------------
# conecta os agentes ao agente grid
# ---------------------------------------
for agent in agents:
    world.connect(grid, agent, 'load_nodes', async_requests=True)



# ---------------------------------------
# conecta os prosumers ao agente grid
# ---------------------------------------
mosaik.util.connect_many_to_one(world, prosumers, grid, 'power_input')

# ---------------------------------------
# conecta os prosumers ao agente de monitoramento
# ---------------------------------------
mosaik.util.connect_many_to_one(world, prosumers, monitor, 'power_input', 'storage_energy')

world.run(END)

# ---------------------------------------
# carrega os dados gerados pela simulação
# organiza em gráficos e exibe-os na tela.
# ---------------------------------------

# data = json.load(open('data.json', 'r'))

# datetime_serie = generate_timeseries(START, END, STEP)

# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y - %H:%M'))
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# for i, j in data.items():
#     #if i == 'MosaikSim-0.Prosumer_10' or i == 'MosaikSim-0.Prosumer_12':
#     plt.plot(datetime_serie, j['power_input'], '-')

# plt.gcf().autofmt_xdate()
# plt.legend(data.keys())
# plt.show()
