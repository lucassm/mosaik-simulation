"""Este arquivo contém as classes que implementam os comportamentos
fundamentais dos principais componentes elétricos de uma unidade
consumidora/produtora de energia, tais como:
- Load;
- Generation;
- Storage;
- Prosumer.
"""

from random import uniform
import datetime as dt


def generate_timeseries(start, time):

    time_step = 15 * 60 # seconds
    dt_start = dt.datetime.strptime(start, '%d/%m/%Y - %H:%M:%S')
    delta = dt.timedelta(0, time)

    delta_sec = delta.days * (24 * 60 * 60) + delta.seconds

    res = [dt_start + dt.timedelta(0, t) for t in range(0, delta_sec, time_step)]
    # res_pp = [i.strftime('%D - %T') for i in res]
    return res


class Load(object):
    """Representa uma classe que a cada passo
    de tempo retorna a demanda média de energia 
    para um determinado período de tempo.
    """
    def __init__(self):
        self.demand = 0.0

    def step(self, datetime):
        self.demand = round(uniform(6.0, 8.0), 3)
        return self.demand

    def __repr__(self):
        return 'Load'


class Generation(object):
    """Representa uma classe que a cada passo
    de tempo retorna a produção média de energia 
    para um determinado período de tempo.
    """
    def __init__(self):
        self.power = 0.0

    def step(self, datetime):
        if datetime.hour >= 18 or datetime.hour < 6:
            self.power = 0.0
        else:
            self.power = round(uniform(0.0, 4.0), 3)
        return self.power

    def __repr__(self):
        return 'Generation'


class Storage(object):
    """Representa uma classe que a cada passo
    de tempo retorna a quantidade de energia
    consumida/armazenada no sistema de armazenamento
    dependendo do modo de operação loading/unloading.
    """
    LOADING = 1
    UNLOADING = 0

    def __init__(self):
        self.energy = 0.0
        self.max_storage = 10.0
        self.state = self.LOADING

    def step(self, energy_rate):
        self.energy += round(energy_rate, 3)
        excess = 0.0
        if self.energy > self.max_storage:
            self.energy = self.max_storage
            excess = self.max_storage - self.energy
        else:
            pass
        return excess

    def __repr__(self):
        return 'Storage'


class Prosumer(object):
    """Esta classe implementa a lógica de consumo/produção
    de energia para cada passo de tempo de um prosumidor
    utilizando para isso instâncias das demais classes
    deste módulo, tais como Load, Generation e Storage
    """
    def __init__(self):
        self.load = Load()
        self.generation = Generation()
        self.storage = Storage()
        self.datetime = None

        # mosaik simulation controller params
        self.power_input = 0.0
        self.load_demand = 0.0
        self.generation_power = 0.0
        self._storage_energy = 0.0

    def step(self):
        self.load_demand = self.load.step(self.datetime)
        self.generation_power = self.generation.step(self.datetime)

        # ---------------------------------------
        # ----------- PROSUMER LOGIC ------------
        # ---------------------------------------

        self.power_input = 0.0

        # No estado de descarga do sistema de armazenamento
        # a carga é dividida pela metade entre a rede e
        # o sistema de armazenamento até o limite de 40% de
        # carga do sistema de armazenamento.
        if  self.storage.state == 0: # unloading
                power_from_storage = self.load.demand / 2.0
                self.power_input += self.load.demand / 2.0
                
                energy_from_storage = power_from_storage * 0.25
                # verifica se o sistema de armazenamento é capaz de
                # suprir a energia solicitada pela carga
                if self.storage.energy - energy_from_storage > 0.0:
                    self.storage.energy -= energy_from_storage
                # caso o sistema de aramazenamento tenha menos energia
                # armazenada que o suficiente para suprir a solicitacao da carga
                # a energia na bateria é zerada e o restante de energia necessaria
                # para suprir a carga é fornecida pela rede
                else:
                    self.power_input += self.load.demand - (self.storage.energy) / 0.25
                    self.storage.energy = 0.0
        # no estado de carga do sistema de armazenamento
        # a energia gerada é utilizada totalmente para carregar
        # o sistema de armazenamento. Caso este já esteja com
        # 100% de carga, a energia gerada é utilizada para
        # suprir a carga e diminuir o consumo da rede. Caso
        # a geracao exceda a carga, o excedente é injetado na
        # rede elétrica. 
        elif self.storage.state == 1: # loading
            generation_energy = self.generation.power * 0.25
            # verifica se o armazenamento esta 100% carregado.
            if self.storage.energy < self.storage.max_storage:
                # verifica se a energia gerada no periodo ira
                # carregar o sistema de armazenameto e gerar excedente. 
                if self.storage.max_storage - self.storage.energy > generation_energy:
                    self.storage.energy += generation_energy
                    self.power_input += self.load.demand
                # caso haja excedente este excedente é utilizado para dividir
                # a carga com a rede elétrica.
                else:
                    excess = generation_energy - (self.storage.max_storage - self.storage.energy) 
                    self.storage.energy = self.storage.max_storage

                    self.power_input += self.load.demand - (excess / 0.25)
            # caso o sistema de armazenamento esteja 100% carregado
            # toda a energia produzida pela geracao sera utilizada para
            # alimentar as cargas do prosumidor, com possibilidade de 
            # geracao de excedente de energia.
            else:
                self.power_input += self.load.demand - self.generation.power

    @property
    def storage_energy(self):
        return self.storage.energy

    @storage_energy.setter
    def storage_energy(self, value):
        self.storage.energy = value
        self._storage_energy = value

    def __repr__(self):
        return 'Prosumer'

class Simulator(object):
    """Esta classe cria instâncias da classe
    Prosumer e faz a chamada de seu método step
    para cada passo de tempo de simulação.
    """
    def __init__(self, start_datetime):
        self.prosumers = []
        self.data = []
        self.start_datetime = dt.datetime.strptime(start_datetime, '%d/%m/%Y - %H:%M:%S')

    def add_prosumer(self):
        prosumer = Prosumer()
        self.prosumers.append(prosumer)
        self.data.append([])

    def step(self, time, storages):
        delta = dt.timedelta(0, time)
        datetime = self.start_datetime + delta

        if storages:
            for idx, storage in storages.items():
                self.prosumers[idx].storage = storage

        for i, prosumer in enumerate(self.prosumers):
            prosumer.datetime = datetime
            prosumer.step()
            data = {'datetime': datetime.strftime('%D - %T'),
                    'load_demand': prosumer.load_demand,
                    'generation_power': prosumer.generation_power,
                    'storage_energy': prosumer.storage_energy}
            self.data[i].append(data)

def main():
    start = '14/03/2018 - 00:00:00'
    sim = Simulator(start_datetime=start)
    for i in range(5):
        sim.add_prosumer()

    time_step = 15 * 60 # seconds
    time = 10 * 60 * 60
    delta = dt.timedelta(0, time)
    delta_sec = delta.days * (24 * 60 * 60) + delta.seconds
    
    for i in range(0, delta_sec, time_step):
        sim.step(i)

    for i, inst in enumerate(sim.data):
        print('%d: %s' % (i, inst))


if __name__ == '__main__':
    main()
