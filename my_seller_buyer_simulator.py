import datetime as dt
import random


def generate_timeseries(start, time):

    time_step = 1 * 60 # seconds
    dt_start = dt.datetime.strptime(start, '%d/%m/%Y - %H:%M:%S')
    delta = dt.timedelta(0, time)

    delta_sec = delta.days * (24 * 60 * 60) + delta.seconds

    res = [dt_start + dt.timedelta(0, t) for t in range(0, delta_sec, time_step)]
    res_pp = [i.strftime('%D - %T') for i in res]
    return res


class Vendedor(object):

    def __init__(self, energia, max_kwh, preco_base, start_datetime):
        self.id = 0
        self.energia = energia
        self.max_kwh = max_kwh
        self.preco_base = preco_base
        self.registro = list()
        self.start_datetime = start_datetime


    def vender(self, ordens, datetime):
        '''
        ordens é uma lista de dicionários de ordens de compra em com a seguinte estrutura:
        ordem['id'] = identificação do comprador
        ordem['quantidade'] = quantidade de energia a ser comprada em kWh

        Neste método é implementada uma lógica para estabelecer limites de tempo e de quantidade
        de energia solicitada pelo comprador.
        '''
        transacoes = list()
        for ordem in ordens:
            if ordem != {}:
                transacao = {'consumidor_id': ordem['consumidor_id'],
                             'ordem_id': self.id,
                             'datetime': datetime,}
                if ordem['kwh'] > self.max_kwh:
                    transacao['resultado'] = 'Falha: valor de energia acima do permitido'
                    transacao['valor'] = 0.0
                    transacao['kwh'] = 0.0
                else:
                    # caacterizacao do aumento da tarifa no horário de ponta
                    if datetime.hour >= 18 and datetime < 21:
                        transacao['valor (R$)'] = 1.3 * round(self.preco_base * ordem['kwh'], 2)
                    else:
                        transacao['valor (R$)'] = round(self.preco_base * ordem['kwh'], 2)
                    transacao['kwh'] = ordem['kwh']
                    self.energia -= ordem['kwh']
                    transacao['resultado'] = 'Sucesso: venda de energia realizada com sucesso'
                transacoes.append(transacao)
                self.id += 1
        return transacoes


    def comprar(self):
        pass


class Consumidor(object):

    def __init__(self, id, start_datetime, energia_disponivel_kwh):
        self.id = str(id)
        self.start_datetime = start_datetime
        self.ultimo_datetime = self.start_datetime
        self.energia_disponivel_kwh = energia_disponivel_kwh
        self.energia_consumida_kwh = 0.0

    def atualizar_consumo(self, datetime):
        delta_de_tempo = datetime - self.ultimo_datetime
        delta_em_horas = delta_de_tempo.seconds / (60.0 * 60.0)
        
        consumo_medio_por_hora = (0.5 - 0.3) * random.random() + 0.3
        
        valor_de_consumo_kwh = consumo_medio_por_hora * delta_em_horas
        self.energia_consumida_kwh += valor_de_consumo_kwh
        self.energia_disponivel_kwh -= valor_de_consumo_kwh
        
        if self.energia_disponivel_kwh <= 1.0:
            ordem = {'consumidor_id': self.id,
                     'kwh': (4.0 - 1.0) * random.random() + 1.0}
            return ordem
        else:
            return None

    def atualizar_energia(self, energia_kwh):
        self.energia_disponivel_kwh += energia_kwh

    def __repr__(self):
        return self.id


class Simulador(object):

    def __init__(self, start_datetime):
        self.consumidores = dict()
        self.transacoes = list()
        self.start_datetime = start_datetime
        self.vendedor = None

    def add_vendedor(self):
        if self.vendedor == None:
            self.vendedor = Vendedor(energia=1e3,
                                     max_kwh=3.5,
                                     preco_base=0.71504,
                                     start_datetime=self.start_datetime)

    def add_consumidor(self):
        i = len(self.consumidores)
        self.consumidores[i] = Consumidor(id=i,
                                          start_datetime=self.start_datetime,
                                          energia_disponivel_kwh=3.0)

    def step(self, datetime):

        ordens = list()

        # gera as ordens a serem solicitadas pelos compradores ao vendedor
        for consumidor in self.consumidores.values():
            ordem = consumidor.atualizar_consumo(datetime)
            if ordem is not None:
                ordens.append(ordem)

        # efetiva as transacoes entre os compradores e o vendedor
        transacoes = self.vendedor.vender(ordens=ordens, datetime=datetime)
        self.transacoes += transacoes
        
        # atualiza os valores de energia comprada pelos
        # compradores pelas ordens enviadas ao vendedor
        for transacao in transacoes:
            consumidor_id = transacao['consumidor_id']
            consumidor = self.consumidores[consumidor_id]
            consumidor.atualizar_energia(energia_kwh=transacao['kwh'])



# class Medidor(object):

#     def __init__(self, start_datetime):
#         pass

#     def energia_consumida(self):
#         pass


def main():
    '''Este método simula a requisição de alguns consumidores de ordens de compra
    enviadas para um agente comercializador durante um certo período de tempo
    a uma certa frequência definidas nas variáveis abaixo.
    A classe Vendedor é utilizada para simular o agente comercializador
    de energia, enquanto os consumidores são amostrados aleatoriamente e também
    suas requisições por compra de energia são geradas aleatoriamente dentro de uma
    faixa pré-determinada.
    '''

    # gera os datetimes para a compra de energia a uma taxa de 1 minuto
    datetimes = generate_timeseries('15/05/2018 - 00:00:00', 60 * 120)

    sim = Simulador(start_datetime=datetimes[0])

    sim.add_vendedor()

    for i in range(10):
        sim.add_consumidor()


    # loop que percorre cada um dos datetimes realizando requisições
    # ao vendedor
    for datetime in datetimes:
        # realiza a simulação
        sim.step(datetime)

    return sim

if __name__ == '__main__':
    sim = main()
