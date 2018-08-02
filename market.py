import datetime as dt
import random
import pandas as pd

def generate_timeseries(start, time):

    time_step = 1 * 60 # seconds
    dt_start = dt.datetime.strptime(start, '%d/%m/%Y - %H:%M:%S')
    delta = dt.timedelta(0, time)

    delta_sec = delta.days * (24 * 60 * 60) + delta.seconds

    res = [dt_start + dt.timedelta(0, t) for t in range(0, delta_sec, time_step)]
    res_pp = [i.strftime('%D - %T') for i in res]
    return res


class Market(object):

    def __init__(self,
                 energy,
                 max_kwh,
                 grid_from_buy_value,
                 grid_to_sell_value,
                 start_datetime):
        self.id = 0
        self.energy = energy
        self.max_kwh = max_kwh
        self.grid_from_buy_value = grid_from_buy_value
        self.grid_to_sell_value = grid_to_sell_value
        self.before_auction_orders = pd.DataFrame(list())
        self.after_auction_orders = pd.DataFrame(list())
        self.start_datetime = start_datetime


    def auction(self, orders, datetime):
        '''
        orders é uma lista de dicionários de orders de compra em com a seguinte estrutura:
        order['id'] = identificação do comprador
        order['quantidade'] = quantidade de energy a ser comprada em kWh

        Neste método é implementada uma lógica para estabelecer limites de tempo e de quantidade
        de energy solicitada pelo comprador.
        '''
        
        # TRANSFORMA A LISTA DE ORDENS EM DATAFRAME E LIMPA AS POSIÇOES VAZIAS
        orders = pd.DataFrame(orders).dropna()
        if orders.size == 0:
            return False

        # DEFINE O DATAFRAME DE ORDENS RECEBIDAS
        self.before_auction_orders = orders
        self.after_auction_orders = pd.DataFrame(list())

        # SEPARA ORDENS DE COMPRA E ORDENS DE VENDA
        self.sell_orders = orders[orders.type == 'sell']
        self.buy_orders = orders[orders.type == 'buy']

        # ORDENA OS DATAFRAMES DE ORDENS DE COMPRA E DE VENDA
        self.sell_orders = self.sell_orders.sort_values(by='value_kwh', ascending=True)
        self.buy_orders = self.buy_orders.sort_values(by='value_kwh', ascending=False)

        # VERIFICA SE EXISTEM NO MÍNIMO 10 ORDENS EM CADA DATAFRAME PARA INICIAR 
        # O PROCESSO DE AUCTION. CASO CONTRÁRIO ENCERRA O MÉTODO
        # O VALOR 10 FOI ATRIBUÍDO DE MANEIRA EMPÍRICA
        if self.sell_orders.size < 15 or self.buy_orders.size < 15:
            return False

        # DEFINE A LISTA ARAMAZENA O REGISTRO DE TRANSAÇÕES REALIZADAS 
        self.transactions = list()

        # SELECIONA A ORDEM DE COMPRA DE MAIOR VALOR E A ORDEM DE VENDA
        # DE MENOR VALOR 
        oa = dict(self.sell_orders.ix[self.sell_orders.first_valid_index()])
        ob = dict(self.buy_orders.ix[self.buy_orders.first_valid_index()])

        c = 0
        while True:
            # O NÚMERO DE TRANSAÇÕES POR RODADA FOI LIMITADO EM 10
            # O VALOR 10 FOI ATRIBUÍDO DE MANEIRA EMPÍRICA 
            if c == 15:
                break
            else:
                c += 1
            current_type_transaction = None

            if oa['value_kwh'] <= ob['value_kwh']:

                # DEFINE O PREÇO DA TRANSAÇÃO NO VALOR MÉDIO DAS ORDENS DE COMPRA E VENDA
                value = oa['value_kwh'] + (ob['value_kwh'] - oa['value_kwh']) * 0.5

                qtd_to_sell = oa['qtd_kwh_bid'] - oa['qtd_kwh_exec']
                qtd_to_buy = ob['qtd_kwh_bid'] - ob['qtd_kwh_exec']
                
                # VERIFICA SE A QUANTIDADE DE ENERGIA DISPONIBILIZADA PELO VENDEDOR
                # É MAIOR QUE A QUANTIDADE DEFINIDA PELO COMPRADOR
                if qtd_to_sell >= qtd_to_buy:
                    # CASO A QUANTIDADE DE ENERGIA VENDIDA SEJA MAIOR QUE A COMPRADA
                    # A ORDEM DO COMPRADOR É TOTALMENTE ZERADA E A DIFERENÇA É
                    # RETIRADA DA ORDEM DE VENDA PARA SER ZERADA COM O PRÓXIMO
                    # COMPRADOR

                    current_type_transaction = 0

                    oa['qtd_kwh_exec'] += qtd_to_buy

                    ob['qtd_kwh_exec'] += qtd_to_buy

                    transaction = {'value_kwh': value,
                                   'qtd_kwh': qtd_to_buy,
                                   'seller': oa['customer_id'],
                                   'buyer': ob['customer_id']}

                    # ARMAZENA A TRANSAÇÃO NO REGISTRO DE TRANSAÇÕES EFETIVADAS
                    self.transactions.append(transaction)

                    # RETIRA A ORDEM DE COMPRA DO DATAFRAME DE ORDENS DE COMPRA
                    self.buy_orders = self.buy_orders.drop(self.buy_orders.first_valid_index())
                    self.after_auction_orders.append(ob, ignore_index=True)

                    # VERIFICA SE AINDA EXISTEM ORDENS DE COMPRA
                    if self.buy_orders.size != 0:
                        # OBTÉM A NOVA ORDEM DE COMPRA COM VALOR MÁXIMO
                        ob = dict(self.buy_orders.ix[self.buy_orders.first_valid_index()])
                    else:
                        self.after_auction_orders.append(oa, ignore_index=True)
                        self.sell_orders.drop(self.sell_orders.first_valid_index())
                        break
                else:
                    # CASO A QUANTIDADE DE ENERGIA COMPRADA SEJA MAIOR QUE A VENDIDA
                    # A ORDEM DO VENDEDOR É TOTALMENTE ZERADA E A DIFERENÇA É
                    # RETIRADA DA ORDEM DE COMPRA PARA SER ZERADA COM O PRÓXIMO
                    # VENDEDOR  

                    current_type_transaction = 1

                    oa['qtd_kwh_exec'] += qtd_to_sell

                    ob['qtd_kwh_exec'] += qtd_to_sell

                    transaction = {'datetime': datetime,
                                   'value_kwh': value,
                                   'qtd_kwh': qtd_to_sell,
                                   'seller': oa['customer_id'],
                                   'buyer': ob['customer_id']}

                    # ARMAZENA A TRANSAÇÃO NO REGISTRO DE TRANSAÇÕES EFETIVADAS
                    self.transactions.append(transaction)

                    # RETIRA A ORDEM DE VENDA DO DATAFRAME DE ORDENS DE VENDA
                    self.sell_orders = self.sell_orders.drop(self.sell_orders.first_valid_index())
                    self.after_auction_orders.append(oa, ignore_index=True)

                    # VERIFICA SE AINDA EXISTEM ORDENS DE VENDA
                    if self.sell_orders.size != 0:
                        # OBTÉM A NOVA ORDEM DE VENDA COM VALOR MÍNIMO
                        oa = dict(self.sell_orders.ix[self.sell_orders.first_valid_index()])
                    else:
                        self.after_auction_orders.append(ob, ignore_index=True)
                        self.buy_orders.drop(self.buy_orders.first_valid_index())
                        break
            else:
                break

        # REGISTRA A ULTIMA OPERAÇÃO QUE FICOU PENDENTE NA LISTA DE 
        # OPERAÇÕES REALIZADAS
        if current_type_transaction is not None:
            if current_type_transaction == 0:
                self.after_auction_orders.append(oa, ignore_index=True)
                self.sell_orders.drop(self.sell_orders.first_valid_index())
            else:
                self.after_auction_orders.append(ob, ignore_index=True)
                self.buy_orders.drop(self.buy_orders.first_valid_index())

        self.transactions = pd.DataFrame(self.transactions)

        # REALIZA A JUNÇÃO DAS ORDENS NEGOCIADAS E DAS ORDENS QUE NÃO FORAM NEGOCIADAS
        self.after_auction_orders = self.after_auction_orders.append(self.sell_orders, ignore_index=True)
        self.after_auction_orders = self.after_auction_orders.append(self.buy_orders, ignore_index=True)
        
        # print(self.after_auction_orders)
        return True

class Customer(object):

    def __init__(self, id, start_datetime, available_energy_kwh):
        self.id = str(id)
        self.start_datetime = start_datetime
        self.last_datetime = self.start_datetime
        self.available_energy_kwh = available_energy_kwh
        self.consumed_energy_kwh = 0.0

    def update_power_consumption(self, datetime, power_kw):
        time_delta = datetime - self.last_datetime
        delta_in_hours = time_delta.seconds / (60.0 * 60.0)
        
        # consumo_medio_por_hora = (0.5 - 0.3) * random.random() + 0.3
        # consumption_value_kwh = consumo_medio_por_hora * delta_in_hours

        consumption_value_kwh = power_kw * delta_in_hours

        # print('valor de energy consumida em kwh: %4.4f' % consumption_value_kwh)
        
        self.consumed_energy_kwh += consumption_value_kwh
        self.available_energy_kwh -= consumption_value_kwh
        
        # VALOR ATRIBUÍDO EMPIRICAMENTE
        if self.available_energy_kwh <= 1.0:
            order = {'datetime': datetime,
                     'customer_id': self.id,
                     'type': 'buy',
                     'qtd_kwh_bid': random.uniform(1.0, 4.0),
                     'qtd_kwh_exec': 0.0,
                     'value_kwh': None}
            return order
        elif self.available_energy_kwh >= 4.0: # VALOR ATRIBUÍDO EMPIRICAMENTE
            value_to_sell = 0.3 * self.available_energy_kwh # VALOR ATRIBUÍDO EMPIRICAMENTE
            order = {'datetime': datetime,
                     'customer_id': self.id,
                     'type': 'sell',
                     'qtd_kwh_bid': value_to_sell,
                     'qtd_kwh_exec': 0.0,
                     'value_kwh': None} 
            self.available_energy_kwh -= value_to_sell
            return order
        else:
            return None

    def update_energy(self, order, datetime):
        if order['qtd_kwh_bid'] == order['qtd_kwh_exec']:
            self.available_energy_kwh += order['qtd_kwh_exec']
            return None
        elif order['qtd_kwh_bid'] > order['qtd_kwh_exec']:
            self.available_energy_kwh += order['qtd_kwh_exec']
            order['qtd_kwh_bid'] = order['qtd_kwh_exec']
            order['qtd_kwh_exec'] = 0.0
            order['datetime'] = datetime
        elif order['qtd_kwh_exec'] == 0.0:
            if order['type'] == 'sell':
                order['value_kwh'] -= 0.1
            elif order['type'] == 'buy':
                order['value_kwh'] += 0.1
        
        return order

    def __repr__(self):
        return self.id

# ################################################################# #
#                           ATENÇÃO!                                #
# É PRECISO REFAZER ESTA CLASSE PARA ADEQUALA A NOVA CLASSE MARKET  #
# ################################################################# #
class Simulator(object):

    def __init__(self, start_datetime):
        self.customers = dict()
        self.transactions = list()
        self.start_datetime = start_datetime
        self.market = None

    def add_market(self):
        if self.market == None:
            self.market = Market(energy=1e3,
                                     max_kwh=3.5,
                                     grid_from_buy_value=0.71504,
                                     grid_to_sell_value=0.5 * 0.71504,
                                     start_datetime=self.start_datetime)

    def add_consumidor(self):
        i = len(self.customers)
        self.customers[i] = Consumidor(id=i,
                                          start_datetime=self.start_datetime,
                                          available_energy_kwh=3.0)

    def step(self, datetime):

        orders = list()

        # gera as orders a serem solicitadas pelos compradores ao market
        for consumidor in self.customers.values():
            order = consumidor.update_power_consumption(datetime)
            if order is not None:
                orders.append(order)

        # efetiva as transactions entre os compradores e o market
        transactions = self.market.auction(orders=orders, datetime=datetime)
        self.transactions += transactions
        
        # atualiza os valores de energy comprada pelos
        # compradores pelas orders enviadas ao market
        for transaction in transactions:
            customer_id = transaction['customer_id']
            consumidor = self.customers[customer_id]
            consumidor.update_energy(energy_kwh=transaction['kwh'])


def main():
    '''Este método simula a requisição de alguns customers de orders de compra
    enviadas para um agente comercializador durante um certo período de tempo
    a uma certa frequência definidas nas variáveis abaixo.
    A classe Market é utilizada para simular o agente comercializador
    de energy, enquanto os customers são amostrados aleatoriamente e também
    suas requisições por compra de energy são geradas aleatoriamente dentro de uma
    faixa pré-determinada.
    '''

    # gera os datetimes para a compra de energy a uma taxa de 1 minuto
    datetimes = generate_timeseries('15/05/2018 - 00:00:00', 60 * 120)

    sim = Simulator(start_datetime=datetimes[0])

    sim.add_market()

    for i in range(10):
        sim.add_consumidor()


    # loop que percorre cada um dos datetimes realizando requisições
    # ao market
    for datetime in datetimes:
        # realiza a simulação
        sim.step(datetime)

    return sim

if __name__ == '__main__':
    sim = main()
