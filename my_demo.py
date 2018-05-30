"""Simulation demo."""

import mosaik
import mosaik.util

from my_simulator import generate_timeseries

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import json

# ---------------------------------------
# configura os simuladores que serão 
# utilizados
# ---------------------------------------

SIM_CONFIG = {
    'MosaikSim': {
        'python': 'my_simulator_with_mosaik_api:MosaikSim',
    },
    'AgentContoller': {
        'python': 'my_controller:Controller',
    },
    'MyGridSim':{
        'python': 'my_grid_mosaik:MyGrid'
    },
    'Collector': {
        'cmd': 'python collector.py %(addr)s',
    },
}

# ---------------------------------------
# define inicio e tempo de execução 
# da simulação
# ---------------------------------------

START = '12/03/2018 - 00:00:00'
END = 1 * 60 * 60 

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

mosaiksim = world.start('MosaikSim', eid_prefix='Prosumer_', start=START)
agent_controller = world.start('AgentContoller')
mygridsim = world.start('MyGridSim', step_size=60 * 15)
collector = world.start('Collector', step_size=60 * 15)

# ---------------------------------------
# cria as instâncias de cada um dos 
# simuladores acoplados ao ambiente de
# simulação 
# ---------------------------------------

# logica para criacao de prosumers somente na baixa tensao

data = json.load(open('force.json', 'r'))
prosumers_id = []
for i in data['nodes']:
    if i['voltage_level'] == 'low voltage':
        prosumers_id.append(i['name'])

prosumers = mosaiksim.Prosumer.create(len(prosumers_id), prosumers_id=prosumers_id)
agents = agent_controller.Agent.create(len(prosumers), prosumers_id=prosumers_id)
grid = mygridsim.Grid(gridfile=open('force.json', 'r'))
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

data = json.load(open('data.json', 'r'))

datetime_serie = generate_timeseries(START, END)

plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y - %H:%M'))
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
for i, j in data.items():
    plt.plot(datetime_serie, j['power_input'], 'o-')

plt.gcf().autofmt_xdate()
plt.legend(data.keys())
plt.show()
