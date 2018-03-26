"""Simulation demo."""

import mosaik
import mosaik.util
import my_simulator

SIM_CONFIG = {
    'MosaikSim': {
        'python': 'my_simulator_with_mosaik_api:MosaikSim',
    },
    'AgentContoller': {
        'python': 'my_controller:Controller',
    },
    'Collector': {
        'cmd': 'python collector.py %(addr)s',
    }
}

START = '12/03/2018 - 00:00:00'
END = 10 * 24 * 60 * 60  # 1 day in seconds

world = mosaik.World(SIM_CONFIG)

mosaiksim = world.start('MosaikSim', eid_prefix='Prosumer_', start=START)
agent_controller = world.start('AgentContoller')
collector = world.start('Collector', step_size=60 * 15)

prosumers = mosaiksim.Prosumer.create(5)
agents = agent_controller.Agent.create(len(prosumers))
monitor = collector.Monitor()

for prosumer, agent in zip(prosumers, agents):
    world.connect(prosumer,
                  agent,
                  'datetime',
                  'storage',
                  async_requests=True)


mosaik.util.connect_many_to_one(world, prosumers, monitor, 'power_input')

world.run(END)
