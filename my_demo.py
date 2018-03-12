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

load = mosaiksim.Load()
monitor = collector.Monitor()

world.connect(load, monitor, 'demand')

more_loads = mosaiksim.Load.create(2)
mosaik.util.connect_many_to_one(world, more_loads, monitor, 'demand')

world.run(END)
