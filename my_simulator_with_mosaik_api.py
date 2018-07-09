import mosaik_api
import my_simulator

META = {
    'models': {
        'Prosumer': {
            'public': True,
            'params': ['prosumers_id'],
            'attrs': ['datetime', 'storage','storage_energy', 'power_input'],
        }
    }
}


class MosaikSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.eid_prefix = 'Prosumer_'
        self.entities = {}

    def init(self, sid, eid_prefix, start, step_size, debug=False):
        self.simulator = my_simulator.Simulator(start)
        self.step_size = step_size
        self.debug = debug
        self.eid_prefix = eid_prefix
        return self.meta

    def create(self, num, model, prosumers_id):
        '''O parametro prosumers_id é uma tupla em que a posição 0 contém
        o nome do nó considerado e a posição 1 contém um valor booleano
        para indicar ou não a presença de DER no consumidor
        '''
        next_eid = len(self.entities)
        entities = []

        for i, j in zip(range(next_eid, next_eid + num), prosumers_id):
            eid = '%s%d' % (self.eid_prefix, j[0])
            self.simulator.add_prosumer(j[1])
            self.entities[eid] = i
            entities.append({'eid': eid, 'type': model})

        return entities

    def step(self, time, inputs):
        storages = {}
        for eid, attrs in inputs.items():
            for attr, values in attrs.items():
                model_idx = self.entities[eid]
                storage = [i for i in values.values()][0]  # analisar esse ponto
                storages[model_idx] = storage
        self.simulator.step(time, storages)
        return time + self.step_size

    def get_data(self, outputs):
        models = self.simulator.prosumers
        data = {}
        for eid, attrs in outputs.items():
            model_idx = self.entities[eid]
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['Prosumer']['attrs']:
                    raise ValueError('Unknown output attribute: %s' % attr)
                data[eid][attr] = getattr(models[model_idx], attr)
        return data


def main():
    return mosaik_api.start_simulation(MosaikSim())

if __name__ == '__main__':
    main()
