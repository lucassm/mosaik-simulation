# utility.py
"""
Mosaik interface for utility simulator.

"""
import mosaik_api

META = {
    'models': {
        'UtilityModel': {
            'public': True,
            'params': ['base_price'],
            'attrs': ['order',],
        },
    },
}


class UtilitySim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.eid_prefix = 'Utility_'
        self.entities = {}  # Maps EIDs to model indices

    def init(self, sid, eid_prefix, start, step_size, debug=False):
        if eid_prefix is not None:
            self.eid_prefix = eid_prefix
            self.start = start
            self.step_size = step_size
            self.debug.debug = debug
        return self.meta

    def create(self, num, model, base_price):
        next_eid = len(self.entities)
        entities = []

        self.base_price = base_price
        for i in range(next_eid, next_eid + num):
            eid = '%s%d' % (self.eid_prefix, i)
            self.entities[eid] = i
            entities.append({'eid': eid, 'type': model})

        return entities

    def step(self, time, inputs):
        '''Inputs are dictionaries witha form like that:
        {
            'Utility_0': {
                'order': {'customer_eid_0': order_dict,
                          'customer_eid_1': order_dict,
                          'customer_eid_2': order_dict},
            },
        }
        '''
        orders = {}
        # PERCORRE O DICIONÁRIO DE MODELOS
        for eid, attrs in inputs.items():

            # SELECIONA A INPUT DESEJADA
            order = attrs.get('order', {})

            # PERCORRE AS INPUTS DO TIPO 'ORDER'
            for customer_eid, order_ in order.items():
                orders[customer_eid] = order

        return time + self.step_size

    def get_data(self, outputs):
        models = self.simulator.models
        data = {}
        for eid, attrs in outputs.items():
            model_idx = self.entities[eid]
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['ExampleModel']['attrs']:
                    raise ValueError('Unknown output attribute: %s' % attr)

                # Get model.val or model.delta:
                data[eid][attr] = getattr(models[model_idx], attr)

        return data

class Utility(object):
    def __init__(self, total_energy_amount):
        self.total_energy_amount = total_energy_amount

def main():
    return mosaik_api.start_simulation(UtilitySim())


if __name__ == '__main__':
    main()