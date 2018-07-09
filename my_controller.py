"""controller.py

    Este controlador irá implementar algumas ações de controle básicas, 
    atuando nos elementos do prosumidor
"""

import mosaik_api

import my_seller_buyer_simulator as my_sbs

import numpy as np
import datetime as dt
import json

from mygrid.util import r2p, disp_vect

META = {
    'models': {
        'Agent': {
            'public': True,
            'params': ['prosumers_id'],
            'attrs': ['datetime', 'storage', 'load_nodes', 'ordem', 'transacoes'],
        },
    },
}

class Controller(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.agents = []
        self.prosumers_id = []
        self.data_transactions = []
        self.VALOR_KWH = None

    def init(self, sid, eid_prefix, start, step_size, debug=False):
        self.start_datetime = dt.datetime.strptime(start, '%d/%m/%Y - %H:%M:%S')
        self.step_size = step_size
        self.debug = debug
        self.datetime = self.start_datetime
        self.consumidores = dict()
        self.entities = dict()
        self.eid_prefix = eid_prefix
        
        return self.meta

    def create(self, num, model, prosumers_id):
        self.prosumers_id += prosumers_id
        n_agents = len(self.agents)
        entities = []
        for i, j in zip(range(n_agents, n_agents + num), prosumers_id):
            eid = '%s%d' % (self.eid_prefix, j[0])
            self.agents.append(eid)

            self.entities[eid] = i, j[1]

            entities.append({'eid': eid, 'type': model})

            consumidor = my_sbs.Consumidor(id=self.eid_prefix + str(i),
                                           start_datetime=self.start_datetime,
                                           energia_disponivel_kwh=3.0)
            if self.debug:
                print('+ Consumidor {id} criado.'.format(id=consumidor.id))
            self.consumidores[consumidor.id] = consumidor
        return entities

    def step(self, time, inputs):
        '''O dicionário inputs tem a seguinte estrutura:
        {
            'Agente_1': {
                'transacao': {
                    {'Vendedor_1': transacao_dict},
                },
                'datetime':{
                    {'Prosumer_1': datetime},
                },
                'storage': {
                    {'Prosumer_1': storage_object}
                },
                'load_nodes': {
                    {'Prosumer_1': load_nodes}
                },
            },
            'Agente_2': {
                'transacao': {
                    {'Vendedor_1': transacao_dict},
                },
                'datetime':{
                    {'Prosumer_2': datetime},
                },
                'storage': {
                    {'Prosumer_2': storage_object}
                },
                'load_nodes': {
                    {'Prosumer_2': load_nodes}
                },
            },
        '''

        # -------------------------------------
        # LÓGICA DE CONSUMO
        # -------------------------------------
        '''A logica de consumo implementada aqui é bem simples
        e consiste no seguinte comportamento bem definido:

        1- É definido um preço base;
        
        2- É definido uma faixa de variação admissível na demanda do consumidor;
        ESTADO 1
        3- Caso o preço da energia se matenha dentro de um patamar estável +/- 10%
        do preço base, o consumo de energia se mantem constante e caso 
        o sistema de armazenamento esteja descarregado, este será totalmente carregado;
        ESTADO 2
        4- Caso o preço da energia ultrapasse em 10% o valor do preço base
        a demanda é reduzida ao máximo e se houver energia no sistema de armazenamento
        essa energia será utilizada pelo consumidor;
        ESTADO 3
        5 - Caso o preço da energia caia a um valor de 10% do preço base, a demanda será
        elevada ao máximo permitido e o sistema de armazenamento será carregado. 

        '''

        delta = dt.timedelta(0, time)
        datetime = self.start_datetime + delta
 
        commands = dict()
        transacoes = list()
        self.prosumers_voltages = dict()
        self.prosumers_powers = dict()
        
        for agent_eid, attrs in inputs.items():
            # datetime = attrs.get('datetime', {})
            storages = attrs.get('storage', {})
            load_nodes = attrs.get('load_nodes', {})
            transacao = attrs.get('transacao', {})
            valor_kwh = attrs.get('valor_kwh', {})

            
            for vendedor_eid, transacao_ in transacao.items():
                transacoes.append(transacao_)


            valores_kwh = list()
            for vendedor_eid, valor_kwh_ in valor_kwh.items():
                valores_kwh.append(valor_kwh_)
            self.VALOR_KWH = np.mean(valores_kwh)

            # dados da rede
            for grid_eid, load_nodes_ in load_nodes.items():
                prosumer_eid = agent_eid.split('_')[1]
                self.prosumers_voltages[agent_eid] = load_nodes_[prosumer_eid].vp
                self.prosumers_powers[agent_eid] = load_nodes_[prosumer_eid].pp

            if self.entities[agent_eid][1] == True:
                commands = self.set_storage_status_command(agent_eid, storages, datetime, commands)

        # atualiza os valores de energia comprada pelos
        # compradores pelas ordens enviadas ao vendedor
        self.atualizar_valores_de_energia_comprada(transacoes)
        self.gerar_ordens_de_compra_de_energia(datetime)

        yield self.mosaik.set_data(commands)

        return time + self.step_size

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
            model_idx = self.entities[eid][0]
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['Agent']['attrs']:
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
        if self.debug:
            print('--->> Envio de dados para o vendedor:')
            print(data)
        return data

    def atualizar_valores_de_energia_comprada(self, transacoes):

        for transacao in transacoes:
            if self.debug:
                print('--->> Consolidando transacao..................')
                print(transacao)
            consumidor_id = transacao['consumidor_id']
            consumidor = self.consumidores[consumidor_id]
            consumidor.atualizar_energia(energia_kwh=transacao['kwh'])
            if isinstance(transacao['datetime'], dt.datetime):
                transacao['datetime'] = transacao['datetime'].strftime('%m/%d/%Y - %H:%M')
        self.data_transactions += transacoes

    def gerar_ordens_de_compra_de_energia(self, datetime):
        self.ordens = dict()
        # gera as ordens a serem solicitadas pelos compradores ao vendedor
        for eid, consumidor in zip(self.entities.keys(), self.consumidores.values()):
            power = np.sum(np.real(self.prosumers_powers[eid])) / 1e3
            ordem = consumidor.atualizar_consumo(datetime, power_kw=power)
            if self.debug:
                print('Consumo do consumidor {id} atualizado.'.format(id=consumidor.id))
            if ordem is not None:
                self.ordens[eid] = ordem
                if self.debug:
                    print('>> Ordem de compra gerada por: {id}'.format(id=consumidor.id))
                    print(ordem)

    def set_storage_status_command(self, agent_eid, storages, datetime, commands):

        for model_eid, storage in storages.items():

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
        return commands

    def finalize(self):
        json.dump(self.data_transactions, open('data_transactions.json','w'))

def main():
    return mosaik_api.start_simulation(Controller())

if __name__ == '__main__':
    main()
