import collections
import pprint
import json

import mosaik_api

META = {
    'models': {
        'Monitor': {
            'public': True,
            'any_inputs': True,
            'params': [],
            'attrs': [],
        },
    },
}


class Collector(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.eid = None
        self.data = collections.defaultdict(lambda:
                                            collections.defaultdict(list))
        self.step_size = None

    def init(self, sid, step_size):
        self.step_size = step_size
        return self.meta

    def create(self, num, model):
        if num > 1 or self.eid is not None:
            raise RuntimeError('Can only create one instance of Monitor')
        self.eid = 'Monitor'
        return [{'eid': self.eid, 'type': model}]

    def step(self, time, inputs):
        data = inputs[self.eid]
        for attr, values in data.items():
            for src, value in values.items():
                self.data[src][attr].append(round(value, 3))
        return time + self.step_size

    def finalize(self):
        data = dict()
        print('Collected data')
        for sim, sim_data in sorted(self.data.items()): 
            print('- %s:' % sim)
            data_attr = dict()
            for attr, values in sorted(sim_data.items()):
                data_attr[attr] = values
                print('  - %s: %s' % (attr, values))
            data['%s' % sim] = data_attr
        json.dump(data, open('data.json','w'))

if __name__ == '__main__':
    mosaik_api.start_simulation(Collector())
