"""controller.py

    Este controlador irá implementar algumas ações de controle básicas, 
    atuando nos elementos do prosumidor
"""

import mosaik_api

import numpy as np
from mygrid.util import r2p, disp_vect

META = {
    'models': {
        'Agent': {
            'public': True,
            'params': ['prosumers_id'],
            'attrs': ['datetime', 'storage', 'load_nodes'],
        },
    },
}

class Controller(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.agents = []
        self.prosumers_id = []

    def create(self, num, model, prosumers_id):
        self.prosumers_id += prosumers_id
        n_agents = num
        entities = []
        for i, j in zip(range(n_agents, n_agents + num), prosumers_id):
            eid = 'Agent_%d' % j
            self.agents.append(eid)
            entities.append({'eid': eid, 'type': model})
        return entities

    def step(self, time, inputs):

        # dictionary to send commands to prosumer model 
        commands = {}
        for agent_eid, attrs in inputs.items():
            datetimes = attrs.get('datetime', {})
            storages = attrs.get('storage', {})
            load_nodes = attrs.get('load_nodes', {})

            prosumers_voltages = dict()
            for grid_eid, load_nodes_ in load_nodes.items():
                prosumer_eid = agent_eid.split('_')[1]
                vp = load_nodes_[prosumer_eid].vp
                vp_mean = np.mean(np.absolute(vp))
                prosumers_voltages[prosumer_eid] = vp_mean
                # disp_vect(load_nodes_[prosumer_eid].vp)
                
            print(prosumers_voltages)

            for model_eid, storage in storages.items():
                datetime = datetimes[model_eid]

                # -----------------------------
                # agent logic in each prosumer
                # -----------------------------
                # verifica o horario e ajusta o sistema de 
                # armazenamento de energia em uma das 
                # seguintes possibilidades:
                # Em carga: horario entre 06:00 e 18:00
                # em descarga: horario entre 18:00 e 06:00
                if datetime.hour >= 18 or datetime.hour < 6:
                    # se a bateria esta com carregamento acima de 40%.
                    if storage.energy >= 0.4 * storage.max_storage:
                        state = 0 # unloading
                    # caso o sistema de armazenamento esteja com
                    # menos de 40% a bateria sai do sistema até
                    # que possa ser carregada e novamente
                    # o horario de descarregamento seja alcançado.
                    else:
                        state = 1  # loading
                else:
                    state = 1  # loading

                if state != storage.state:
                    storage.state = state
                    if agent_eid not in commands:
                        commands[agent_eid] = {}
                    if model_eid not in commands[agent_eid]:
                        commands[agent_eid][model_eid] = {}
                    commands[agent_eid][model_eid]['storage'] = storage

        yield self.mosaik.set_data(commands)

        return time + 15 * 60

def main():
    return mosaik_api.start_simulation(Controller())

if __name__ == '__main__':
    main()
