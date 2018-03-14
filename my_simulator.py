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
    def __init__(self):
        self.demand = 0.0

    def step(self, datetime):
        self.demand = round(uniform(2.0, 6.0), 3)


class Generation(object):
    def __init__(self):
        self.power = 0.0

    def step(self, datetime):
        self.power = -1.0 * round(uniform(0.0, 4.0), 3)


class Storage(object):
    LOADING = 1
    UNLOADING = 0

    def __init__(self):
        self.energy = 0.0
        self.max_storage = 100.0
        self.state = self.LOADING

    def step(self, energy_rate):
        self.energy += energy_rate
        excess = 0.0
        if self.energy > self.max_storage:
            self.energy = self.max_storage
            excess = self.max_storage - self.energy
        else:
            pass
        return excess


class Prosumer(object):
    def __init__(self):
        self.load = Load()
        self.generation = Generation()
        self.storage = Storage()
        self.datetime = None
        self.power = 0.0

    def step(self):
        self.load.step(self.datetime)
        self.generation.step(self.datetime)
        self.power = round(self.load.demand + self.generation.power, 3)
        if self.power < 0.0:
            excess = self.storage.step(energy_rate=-1.0 * self.power)
            if excess > 0.0:
                self.power = -1.0 * excess
            else:
                self.power = 0.0


class Simulator(object):
    def __init__(self, start_datetime):
        self.prosumers = []
        self.data = []
        self.start_datetime = dt.datetime.strptime(start_datetime, '%d/%m/%Y - %H:%M:%S')

    def add_prosumer(self):
        prosumer = Prosumer()
        self.prosumers.append(prosumer)
        self.data.append([])

    def step(self, time):
        delta = dt.timedelta(0, time)
        datetime = self.start_datetime + delta
        
        for p in self.prosumers:
            p.datetime = datetime

        for i, prosumer in enumerate(self.prosumers):
            prosumer.step()
            data = {'datetime': datetime.strftime('%D - %T'),
                    'power': prosumer.power}
            self.data[i].append(data)

def main():
    start = '14/03/2018 - 00:00:00'
    sim = Simulator(start_datetime=start)
    for i in range(5):
        sim.add_prosumer()

    time_step = 15 * 60 # seconds
    time = 2 * 60 * 60
    delta = dt.timedelta(0, time)
    delta_sec = delta.days * (24 * 60 * 60) + delta.seconds
    
    for i in range(0, delta_sec, time_step):
        sim.step(i)

    for i, inst in enumerate(sim.data):
        print('%d: %s' % (i, inst))


if __name__ == '__main__':
    main()
