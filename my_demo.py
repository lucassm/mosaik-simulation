"""Simulation demo."""

import mosaik
import mosaik.util

SIM_CONFIG = {
    'MosaikSim': {
        'python': 'my_simulator_with_mosaik_api:MosaikSim',
    },
    'Collector': {
        'cmd': 'python collector.py %(addr)s',
    }
}

END = 10 * 60

world = mosaik.World(SIM_CONFIG)

mosaiksim = world.start('MosaikSim', eid_prefix='Load_')
collector = world.start('Collector', step_size=60)

prosumer = mosaiksim.Prosumer()
monitor = collector.Monitor()

world.connect(prosumer, monitor, 'power')

more_prosumers = mosaiksim.Prosumer.create(2)
mosaik.util.connect_many_to_one(world, more_prosumers, monitor, 'power')

world.run(END)
