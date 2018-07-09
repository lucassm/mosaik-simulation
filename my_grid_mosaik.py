"""Integration between MyGrid module 
and the mosaik interface to simulation
"""

import mosaik_api

import my_grid_simulator
import json

meta = {
    'models': {
        'Grid': {
            'public': True,
            'any_inputs': True,
            'params': [
                'gridfile'
            ],
            'attrs': [
                'demand', 'load_nodes'
            ],
        }
    }
}

class MyGrid(mosaik_api.Simulator):
    def __init__(self):
        super(MyGrid, self).__init__(meta)
        self.step_size = None

        self.entities = {}
        self.relations = []  # List of pair-wise related entities (IDs)
        self.grids = []  # The MyGrid cases
        self.cache = {}  # Cache for load flow outputs
        self.grid_data = None

    def init(self, sid, step_size, debug=False):
        self.step_size = step_size
        self.debug = debug
        return self.meta

    def create(self, num, modelname, gridfile):
        next_eid = len(self.entities)
        entities = []

        # Processo de criação do modelo da rede elétrica
        # por meio do software MyGrid que gera objetos 
        # utilizando os dados contidos no arquivo force.json
        # apontado pela variável gridfile

        # Esse processo de criação está dentro de um laço for
        # mas até aqui só teremos uma entitie para descrição 
        # de toda a rede 

        for i in range(next_eid, next_eid + num):
            eid = '%s%d' % ('Grid_', i)
            grid = my_grid_simulator.create_mygrid_model(gridfile)
            self.grids.append(grid)
            self.entities[eid] = i
            entities.append({'eid': eid, 'type': modelname})

        return entities

        # grids = []
        # for i in range(num):
        #     grid_idx = len(self.grids)
        #     grid = my_grid_simulator.create_mygrid_model(gridfile)
        #     self.grids.append(grid)

        #     grids.append({
        #         'eid': 'Grid_%s' % grid_idx ,
        #         'type': 'Grid',
        #         })
        # return grids

    def step(self, time, inputs):
        for grid in self.grids:
            my_grid_simulator.reset_inputs(grid)

            # Este loop verifica os valores de entrada que
            # provém das entities prosumers e utiliza estes
            # dados para atualizar os valores de potencia
            # demandada pelos nos correspondentes
            for eid, attrs in inputs.items():
                for attr, values in attrs.items():
                    # model_idx = self.entities[eid]
                    powers = dict()
                    for eid_name, value in values.items():
                        node_name = eid_name.split('.')[1]
                        node_name = node_name.split('_')[1]
                        powers[node_name] = value
                    
                    if self.debug:
                        print(powers)

                    my_grid_simulator.reset_inputs(grid)
                    my_grid_simulator.set_inputs(grid, powers)
            
            for grid in self.grids:
                self.grid_data = my_grid_simulator.run_power_flow(grid)
 
        return time + self.step_size
        
    def get_data(self, outputs):
        models = self.grids
        data = {}
        for eid, attrs in outputs.items():
            model_idx = self.entities[eid]
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['Grid']['attrs']:
                    raise ValueError('Unknown output attribute: %s' % attr)
                data[eid][attr] = getattr(models[model_idx], attr)
        return data

    def finalize(self):
        json.dump(self.grid_data, open('grid_data.json','w'))

def main():
    mosaik_api.start_simulation(MyGrid(), 'The mosaik-MyGrid adapter')


if __name__ == '__main__':
    main()
