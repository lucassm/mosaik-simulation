from random import uniform


class Load(object):
    def __init__(self):
        self.demand = 0.0

    def step(self):
        self.demand = round(uniform(2, 6), 3)


class Simulator(object):
    def __init__(self):
        self.loads = []
        self.data = []

    def add_load(self):
        load = Load()
        self.loads.append(load)
        self.data.append([])

    def step(self):
        for i, load in enumerate(self.loads):
            load.step()
            self.data[i].append(load.demand)

def main():
    sim = Simulator()
    for i in range(2):
        sim.add_load()

    for i in range(10):
        sim.step()

    for i, inst in enumerate(sim.data):
        print('%d: %s' % (i, inst))


if __name__ == '__main__':
    main()
