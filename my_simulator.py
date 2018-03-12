from random import uniform


class Load(object):
    def __init__(self):
        self.demand = 0.0

    def step(self):
        self.demand = round(uniform(2.0, 6.0), 3)


class Generation(object):
    def __init__(self):
        self.power = 0.0

    def step(self):
        self.power = -1.0 * round(uniform(0.0, 3.0), 3)


class Prosumer(object):
    def __init__(self):
        self.load = Load()
        self.generation = Generation()
        self.power = 0.0

    def step(self):
        self.load.step()
        self.generation.step()
        self.power = round(self.load.demand + self.generation.power, 3)

class Simulator(object):
    def __init__(self):
        self.prosumers = []
        self.data = []

    def add_prosumer(self):
        prosumer = Prosumer()
        self.prosumers.append(prosumer)
        self.data.append([])

    def step(self):
        for i, prosumer in enumerate(self.prosumers):
            prosumer.step()
            self.data[i].append(prosumer.power)

def main():
    sim = Simulator()
    for i in range(5):
        sim.add_prosumer()

    for i in range(10):
        sim.step()

    for i, inst in enumerate(sim.data):
        print('%d: %s' % (i, inst))


if __name__ == '__main__':
    main()
