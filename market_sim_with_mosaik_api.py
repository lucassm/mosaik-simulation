import mosaik_api
import market

import datetime as dt
import numpy as np
import json
import random

MARKET_META = {
    'models': {
        'Market': {
            'public': True,
            'params': [],
            'attrs': ['order']
        },
    }
}

CUSTOMER_META = {
    'models': {
        'Customer': {
            'public': True,
            'params': ['prosumers_id'],
            'attrs': ['power_input', 'power_forecast', 'order']
        },
    }
}

class MarketSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(MARKET_META)
        self.eid_prefix = 'Mercado_'
        self.entities = {}

    def init(self, sid, eid_prefix, start, step_size, debug=False):
        if start is not None:
            self.start_datetime = dt.datetime.strptime(start, '%d/%m/%Y - %H:%M:%S')
            self.step_size = step_size
            self.debug = debug
            self.market = market.Market(energy=1.0e3,
                                        max_kwh=5.0,
                                        grid_from_buy_value=0.71504,
                                        grid_to_sell_value=0.5 * 0.71504,
                                        start_datetime=self.start_datetime)
            self.completed_transactions = list()
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
            'Mercado_1': {
                'order': {
                    {'Prosumidor_1': order_dict}
                }
            },
            'Mercado_1': {
                'order': {
                    {'Prosumidor_2': order_dict}
                }
            }
        }
        '''

        commands = {}
        delta = dt.timedelta(0, time)
        datetime = self.start_datetime + delta

        # Get inputs
        orders = list()
        for eid, attrs in inputs.items():
            for attr, values in attrs.items():
                order = list(values.values())
                if order != []:
                    orders += order

        if self.debug:
            print('--->> Ordens recebidas dos customers:')
            print(orders)

        # REALIZAÇÃO DO PROCESSO DE AUCTION DAS ORDENS DE COMPRA E VENDA DE ENERGIA
        status = self.market.auction(orders, datetime)

        for market_eid, attrs in inputs.items():
            for attr, values in attrs.items():
                for customer_eid, value in values.items():
                    if market_eid not in commands:
                        commands[market_eid] = {}
                    if customer_eid not in commands[market_eid]:
                        commands[market_eid][customer_eid] = {}
                    
                    commands[market_eid][customer_eid]['grid_kwh_values'] = [self.market.grid_from_buy_value, self.market.grid_to_sell_value]
                    
                    if self.market.after_auction_orders.size != 0:
                        order = self.market.after_auction_orders[self.market.after_auction_orders['customer_id'] == customer_eid.split('.')[1]]
                        if order.size != 0:
                            order = self.market.after_auction_orders[self.market.after_auction_orders['customer_id'] == customer_eid.split('.')[1]].iloc[0] 
                        else:
                            order = {}
                    else:
                        order = {}   
                    commands[market_eid][customer_eid]['order'] = order
        '''O dicionário commands tem a seguinte estrutura:
        {
            'Market_1':
            {
                'Customer_1': {'transaction': transaction_dict, 'grid_kwh_values': values},
                'Customer_2': {'transaction': transaction_dict, 'grid_kwh_values': values},
                'Customer_3': {'transaction': transaction_dict, 'grid_kwh_values': values},
            }
        }
        '''
        yield self.mosaik.set_data(commands)
        return time + self.step_size

    # def get_data(self):
    #     '''O dicionário outputs tem a seguinte estrutura:
    #     {
    #         'Vendedor_1': ['transactions']
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
    #             data[eid][attr] = self.transactions

    #     '''O dicionário retornado por este método tem a seguinte estrutura:
    #     {
    #         'Vendedor_1': {'transactions': transactions_dict}
    #     }
    #     '''
    #     return data

    def finalize(self):
        pass
        #print(self.vendedor.energia)

class CustomerSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(CUSTOMER_META)
        self.eid_prefix = 'Customer_'
        self.entities = {}
        self.GRID_FROM_BUY_VALUE = None
        self.GRID_TO_SELL_VALUE = None

    def init(self, sid, eid_prefix, start, step_size, debug=False):
        if start is not None:
            self.start_datetime = dt.datetime.strptime(start, '%d/%m/%Y - %H:%M:%S')
            self.step_size = step_size
            self.debug = debug
            self.last_datetime = self.start_datetime
            self.customers = dict()
            self.prosumers_id = list()
            self.orders = dict()
            self.data_orders = list()
            self.power_consumed = dict()
        if eid_prefix is not None:
            self.eid_prefix = eid_prefix
        return self.meta

    def create(self, num, model, prosumers_id):
        self.prosumers_id += prosumers_id
        next_eid = len(self.entities)
        entities = []

        for i, j in zip(range(next_eid, next_eid + num), prosumers_id):
            eid = '%s%d' % (self.eid_prefix, j[0])
            # self.agents.append(eid)

            self.entities[eid] = i, j[1]
            customer = market.Customer(id=self.eid_prefix + str(i),
                                       start_datetime=self.start_datetime,
                                       available_energy_kwh=3.0)
            if self.debug:
                print('+ Customer {id} created.'.format(id=customer.id))
            
            self.customers[customer.id] = customer

            entities.append({'eid': eid, 'type': model})

        return entities

    def step(self, time, inputs):
        '''O dicionário inputs tem a seguinte estrutura:
        {
            'Customer_1': {
                'transaction': {
                    'Market_1': transaction_dict,
                },
                'grid_kwh_values': {
                    'Market_1': grid_values_list,
                },
                'power_input': {
                    'Prosumer_1': power_input,
                }
            },
            'Customer_2': {
                'transaction': {
                    'Market_1': transaction_dict,
                },
                'grid_kwh_values': {
                    'Market_1': grid_values_list,
                },
                'power_input': {
                    'Prosumer_1': power_input,
                }
        }
        '''

        delta = dt.timedelta(0, time)
        datetime = self.start_datetime + delta
 
        commands = dict()

        # #######################################################
        # ATIVAÇÃO DO COMPORTAMENTO DE PREVISÃO A CADA 15 MINUTOS
        # OU SEJA ESSE COMPORTAMENTO SERÁ EXECUTADOS NOS TEMPOS:
        # 0, 15, 30, 45, 60, ....
        if time % (15 * 60) == 0:
            self.prosumers_powers_forecast = dict()
            # PERCORRE OS DADOS DAS INPUTS
            for customer_eid, attrs in inputs.items():
                # OBTÉM OS DADOS DAS INPUTS
                power_forecast = attrs.get('power_forecast', {})
                # ARAMAZENA OS DADOS DAS INPUTS
                self.prosumers_powers_forecast[customer_eid] = sum(power_forecast.values())


        # #######################################################
        # ATIVAÇÃO DO COMPORTAMENTO DE PRÉ-LEILÃO A CADA 15 MINUTOS
        # INICIANDO DOS 4 MINUTOS INICIAIS, OU SEJA ESSE 
        # COMPORTAMENTO SERÁ EXECUTADO NOS TEMPOS:
        # 4, 19, 34, 59, 64, ...
        if (time-(5 * 60) + 60) % (15 * 60) == 0:
            self.generate_orders_to_energy_market(datetime)
        
        # #######################################################
        # ATIVAÇÃO DO COMPORTAMENTO DE PÓS-LEILÃO A CADA 15 MINUTOS
        # INICIANDO DOS 5 MINUTOS INICIAIS, OU SEJA ESSE 
        # COMPORTAMENTO SERÁ EXECUTADO NOS TEMPOS:
        # 5, 20, 35, 50, 65, ...
        if (time-(5 * 60)) % (15 * 60) == 0:
            orders = list()
            # PERCORRE OS DADOS DAS INPUTS
            for customer_eid, attrs in inputs.items():
                # OBTÉM OS DADOS DAS INPUTS            
                order = attrs.get('order', {})
                values_kwh = attrs.get('grid_kwh_values', {})
                if values_kwh == {}:
                    values_kwh = {'Market_1': [0.71504, 0.5 * 0.71504]}

                # ARAMAZENA OS DADOS DAS INPUTS 
                for market_eid, order_ in order.items():
                    orders.append(order_)

                for market_eid, values_kwh_ in values_kwh.items():
                    self.GRID_FROM_BUY_VALUE = values_kwh_[1]
                    self.GRID_TO_SELL_VALUE = values_kwh_[0]

            # ATUALIZA OS VALORES DE ENERGIA OBTIDOS PELOS CUSTOMERS
            # POR MEIO DAS ORDENS ENVIADAS AO MARKET
            self.update_energy_values_after_auction(orders, datetime)

        # #######################################################
        # ATIVAÇÃO DO COMPORTAMENTO DE VERIFICAÇÃO DE CARGA/GERAÇÃO
        # INICIANDO DOS 15 MINUTOS INICIAIS, OU SEJA ESSE
        # COMPORTAMENTO SERÁ EXECUTADO NOS TEMPOS:
        # 16, 17, 18, 19, 20, ... 
        if time > 15 * 60:
            # PERCORRE OS DADOS DAS INPUTS
            for customer_eid, attrs in inputs.items():
                # OBTÉM OS DADOS DAS INPUTS
                power_input = attrs.get('power_input', {})
                # ARAMAZENA OS DADOS DAS INPUTS
                if customer_eid not in self.power_consumed.keys():
                    self.power_consumed[customer_eid] = sum(power_input.values())
                else:
                    self.power_consumed[customer_eid] += sum(power_input.values())

        # #######################################################
        # ATIVAÇÃO DO COMPORTAMENTO DE VERIFICAÇÃO ENTRE O VALOR
        # NEGOCIADO NO LEILÃO E O VALOR EFETIVAMENTE GERADO/CONSUMIDO
        # INICIANDO DOS 30 MINUTOS INICIAIS, OU SEJA ESSE
        # COMPORTAMENTO SERÁ EXECUTADO NOS TEMPOS:
        # 30, 45, 60, 75, 90, ...
        if time >= 30 * 60 and time % (15 * 60) == 0:
            print(self.power_consumed)
            self.power_consumed = dict()

        return time + self.step_size

    def get_data(self, outputs):
        '''O dicionário outputs tem a seguinte estrutura:
        {
            'Customer_1': ['order'],
            'Customer_2': ['order'],
            'Customer_3': ['order']
        }
        '''
        # models = self.simulator.models
        data = {}
        
        for eid, attrs in outputs.items():
            model_idx = self.entities[eid][0]
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['Customer']['attrs']:
                    raise ValueError('Unknown output attribute: %s' % attr)

                # Get model.val or model.delta:
                # data[eid][attr] = getattr(models[model_idx], attr)
                if eid in self.orders.keys():
                    data[eid][attr] = self.orders[eid]
                else:
                    data[eid][attr] = {}
        '''O dicionário montado neste método tem a seguinte estrutura:
        {
            'Consumidor_1': {
                'order': order_dict
            },
            'Consumidor_2': {
                'order': order_dict
            },
            'Consumidor_3': {
                'order': order_dict
            },
        }
        '''
        if self.debug:
            print('--->> Sending data to the market:')
            print(data)
        return data

    def finalize(self):
        pass
        # json.dump(self.data_orders, open('data_orders.json','w'))

    def update_energy_values_after_auction(self, orders, datetime):
        # DECLARA O DICIONÁRIO DE ORDENS A SEREM ENVIADAS PARA O MERCADO
        self.orders = dict()
        
        # VERIFICA AS ORDENS QUE FORAM RETORNADAS DO MERCADO
        for eid, order in zip(self.entities.keys(), orders):
            # VERIFICA SE A ORDEM NÃO É UM DICIONÁRIO VAZIO
            if type(order) != dict:

                # REALIZA A TUALIZAÇÃO DA ENERGIA DISPONÍVEL
                # DE ACORDO COM O RESULTADO DO MERCADO
                # SE ORDEM NÃO TIVER SIDO NEGOCIADA
                # ENTÃO ESTA É ATUALIZADA
                customer_id = order['customer_id']
                customer = self.customers[customer_id]
                new_order = customer.update_energy(order, datetime)

                if new_order is not None:
                    self.orders[eid] = dict(new_order)

                # ARMAZENA AS ORDENS EM UM HISTÓRICO
                if isinstance(order['datetime'], dt.datetime):
                    order['datetime'] = order['datetime'].strftime('%m/%d/%Y - %H:%M')
                self.data_orders.append(order)

    def generate_orders_to_energy_market(self, datetime):
        # VERIFICA A NECESSIDADE DE ENVIO DE ORDENS DE COMPRA OU VENDA
        # PARA CADA UM DOS CUSTOMERS
        for eid, customer in zip(self.entities.keys(), self.customers.values()):
            # VERIFICA SE O CUSTOMER JÁ TEM UMA ORDEM PRONTA PARA ENVIO
            if eid not in self.orders.keys():
                # ATUALIZA O VALOR DE CONSUMO DE ENERGIA E CASO SEJA NECESSÁRIO UMA
                # ORDEM DE COMPRA OU DE VENDA É GERADA
                power = np.sum(np.real(self.prosumers_powers_forecast[eid]))
                order = customer.update_power_consumption(datetime, power_kw=power)
                if self.debug:
                    print('Customer consumption {id} updated.'.format(id=customer.id))
                if order is not None:
                    # ATRIBUIÇÃO DOS PREÇOS DE COMPRA OU DE VENDA DA ENERGIA
                    # ESTES VALORES FORAM ATRIBUÍDOS EMPIRICAMENTE
                    if order['type'] == 'sell':
                        order['value_kwh'] = random.uniform(0.7 * self.GRID_FROM_BUY_VALUE, self.GRID_FROM_BUY_VALUE)
                    elif order['type'] == 'buy':
                        order['value_kwh'] = random.uniform(self.GRID_TO_SELL_VALUE, 1.2 * self.GRID_TO_SELL_VALUE)

                    self.orders[eid] = order
                    if self.debug:
                        print('>> Order created by: {id}'.format(id=customer.id))
                        print(order)


def main():
    return mosaik_api.start_simulator(ComercializadorSim())

if __name__ == '__main__':
    main()


