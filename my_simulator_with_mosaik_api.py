import mosaik_api
import my_simulator

META = {
    'models': {
        'Prosumer': {
            'public': True,
            'params': [],
            'attrs': ['power'],
        }
    }
}


class MosaikSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.simulator = my_simulator.Simulator()
        self.eid_prefix = 'Prosumer_'
        self.entities = {}

    def init(self, sid, eid_prefix):
        if eid_prefix is not None:
            self.eid_prefix = eid_prefix
        return self.meta

    def create(self, num, model):
        next_eid = len(self.entities)
        entities = []

        for i in range(next_eid, next_eid + num):
            eid = '%s%d' % (self.eid_prefix, i)
            self.simulator.add_prosumer()
            self.entities[eid] = i
            entities.append({'eid': eid, 'type': model})

        return entities

    def step(self, time, inputs):
        self.simulator.step()
        return time + 60

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
