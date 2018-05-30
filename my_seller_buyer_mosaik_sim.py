import mosaik_api
import my_seller_buyer_simulator as my_sbs

import datetime as dt

VENDEDOR_META = {
    'models': {
        'Vendedor': {
            'public': True,
            'params': [],
            'attrs': ['transacoes', 'ordem']
        },
    }
}

CONSUMIDOR_META = {
    'models': {
        'Consumidor': {
            'public': True,
            'params': [],
            'attrs': ['ordem', 'transacoes']
        },
    }
}

class VendedorSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(VENDEDOR_META)
        self.eid_prefix = 'Vededor_'
        self.entities = {}

    def init(self, sid, eid_prefix, start):
        if start is not None:
            self.start_datetime = dt.datetime.strptime(start, '%d/%m/%Y - %H:%M:%S')
            self.vendedor = my_sbs.Vendedor(energia=1e3,
                                            max_kwh=5.0,
                                            preco_base=0.71504,
                                            start_datetime=self.start_datetime)
            self.transacoes_realizadas = list()
        if eid_prefix is not None:
            self.eid_prefix = eid_prefix
        return self.meta

    def create(self, num, model):
        next_eid = len(self.entities)
        entities = []

        for i in range(next_eid, next_eid + num):
            eid = '%s%d' % (self.eid_prefix, i)
            self.entities[eid] = i
            entities.append({'eid': eid, 'type': model})

        return entities

    def step(self, time, inputs):
        '''O dicionário inputs tem a seguinte estrutura:
        {
            'Vendedor_1': {
                'ordem': {
                    {'Consumidor_1': ordem_dict}
                }
            },
            'Vendedor_1': {
                'ordem': {
                    {'Consumidor_2': ordem_dict}
                }
            }
        }
        '''
        commands = {}
        delta = dt.timedelta(0, time)
        datetime = self.start_datetime + delta

        # Get inputs
        ordens = list()
        for eid, attrs in inputs.items():
            for attr, values in attrs.items():
                ordem = list(values.values())
                if ordem != []:
                    ordens += ordem
        print('--->> Ordens recebidas dos consumidores:')
        print(ordens)
        self.transacoes = self.vendedor.vender(ordens, datetime)
        self.transacoes_realizadas += self.transacoes

        for vendedor_eid, attrs in inputs.items():
            for attr, values in attrs.items():
                for consumidor_eid, value in values.items():
                    if vendedor_eid not in commands:
                        commands[vendedor_eid] = {}
                    if consumidor_eid not in commands[vendedor_eid]:
                        commands[vendedor_eid][consumidor_eid] = {}
                    
                    for transacao in self.transacoes:
                        if transacao['consumidor_id'] in consumidor_eid:
                            commands[vendedor_eid][consumidor_eid]['transacao'] = transacao

        '''O dicionário commands tem a seguinte estrutura:
        {
            'Vendedor_1':
            {
                'Consumidor_1': {'transacao': transacao_dict},
                'Consumidor_2': {'transacao': transacao_dict},
                'Consumidor_3': {'transacao': transacao_dict},
            }
        }
        '''
        yield self.mosaik.set_data(commands)

        return time + 60  # Step size is 1 minute

    # def get_data(self):
    #     '''O dicionário outputs tem a seguinte estrutura:
    #     {
    #         'Vendedor_1': ['transacoes']
    #     }
    #     '''
    #     # models = self.simulator.models
    #     data = {}
        
    #     for eid, attrs in outputs.items():
    #         model_idx = self.entities[eid]
    #         data[eid] = {}
    #         for attr in attrs:
    #             if attr not in self.meta['models']['Vendedor']['attrs']:
    #                 raise ValueError('Unknown output attribute: %s' % attr)

    #             # Get model.val or model.delta:
    #             # data[eid][attr] = getattr(models[model_idx], attr)
    #             data[eid][attr] = self.transacoes

    #     '''O dicionário retornado por este método tem a seguinte estrutura:
    #     {
    #         'Vendedor_1': {'transacoes': transactions_dict}
    #     }
    #     '''
    #     return data

    def finalize(self):
        print(self.vendedor.energia)

class ConsumidorSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(CONSUMIDOR_META)
        self.eid_prefix = 'Consumidor_'
        self.entities = {}

    def init(self, sid, eid_prefix, start):
        if start is not None:
            self.start_datetime = dt.datetime.strptime(start, '%d/%m/%Y - %H:%M:%S')
            self.ultimo_datetime = self.start_datetime
            self.consumidores = dict()
        if eid_prefix is not None:
            self.eid_prefix = eid_prefix
        return self.meta

    def create(self, num, model):
        next_eid = len(self.entities)
        entities = []

        for i in range(next_eid, next_eid + num):
            eid = '%s%d' % (self.eid_prefix, i)
            consumidor = my_sbs.Consumidor(id=self.eid_prefix + str(i),
                                           start_datetime=self.start_datetime,
                                           energia_disponivel_kwh=3.0)
            print('+ Consumidor {id} criado.'.format(id=consumidor.id))
            self.consumidores[consumidor.id] = consumidor
            self.entities[eid] = i
            entities.append({'eid': eid, 'type': model})

        return entities

    def step(self, time, inputs):
        '''O dicionário inputs tem a seguinte estrutura:
        {
            'Consumidor_1': {
                'transacao': {
                    {'Vendedor_1': transacao_dict},
                }
            },
            'Consumidor_2': {
                'transacao': {
                    {'Vendedor_1': transacao_dict},
                }
            },
        }
        '''
        delta = dt.timedelta(0, time)
        datetime = self.start_datetime + delta

        transacoes = list()
        for eid, attrs in inputs.items():
            for attr, values in attrs.items():
                transacao = list(values.values())
                if transacao != []:
                    transacao = transacao[0]
                    transacoes.append(transacao)
        
        # atualiza os valores de energia comprada pelos
        # compradores pelas ordens enviadas ao vendedor
        for transacao in transacoes:
            print('--->> Consolidando transacao..................')
            print(transacao)
            consumidor_id = transacao['consumidor_id']
            consumidor = self.consumidores[consumidor_id]
            consumidor.atualizar_energia(energia_kwh=transacao['kwh'])


        self.ordens = dict()
        # gera as ordens a serem solicitadas pelos compradores ao vendedor
        for eid, consumidor in zip(self.entities.keys(), self.consumidores.values()):
            ordem = consumidor.atualizar_consumo(datetime)
            print('Consumo do consumidor {id} atualizado.'.format(id=consumidor.id))
            if ordem is not None:
                self.ordens[eid] = ordem
                print('>> Ordem de compra gerada por: {id}'.format(id=consumidor.id))
                print(ordem)

        return time + 60  # Step size is 1 minute

    def get_data(self, outputs):
        '''O dicionário outputs tem a seguinte estrutura:
        {
            'Consumidor_1': ['ordem'],
            'Consumidor_2': ['ordem'],
            'Consumidor_3': ['ordem']
        }
        '''
        # models = self.simulator.models
        data = {}
        
        for eid, attrs in outputs.items():
            model_idx = self.entities[eid]
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['Consumidor']['attrs']:
                    raise ValueError('Unknown output attribute: %s' % attr)

                # Get model.val or model.delta:
                # data[eid][attr] = getattr(models[model_idx], attr)
                if eid in self.ordens.keys():
                    data[eid][attr] = self.ordens[eid]
                else:
                    data[eid][attr] = {}
        '''O dicionário montado neste método tem a seguinte estrutura:
        {
            'Consumidor_1': {
                'ordem': ordem_dict
            },
            'Consumidor_2': {
                'ordem': ordem_dict
            },
            'Consumidor_3': {
                'ordem': ordem_dict
            },
        }
        '''
        print('--->> Envio de dados para o vendedor:')
        print(data)
        return data


def main():
    return mosaik_api.start_simulator(ComercializadorSim())

if __name__ == '__main__':
    main()


