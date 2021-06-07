import random
import csv
from gridworld import ask
from gridworld import Agent,GridWorld
from gridworld import GridWorldGUI
from gridworld import Patch
from gridworld import maximizers
from gridworld import RectangularGrid
params = dict(world_shape=(100,100), n_agents=100, maxiter=100)
params.update(cell_data_file='Cell.Data')
params.update(agent_initial_size=0.0, extraction_rate=0.1)
params.update(cell_initial_supply=0.0, cell_max_produce=0.01)
params.update(agent_max_extract=1.0)
params.update(agent_exit_probability=0)
params.update(agent_size_mean=0.1, agent_size_sd=0.03)
params.update(logfile='sizes.csv')
import pandas as pd
data1 = pd.read_csv("size.txt", sep='\t')
siz1 = map(float, data1)
siz2 = tuple(siz1)
def read_celldata(filename): #define how python read the initilization data for patches where X Y are coordinations.
    location2value = dict()
    maxx, maxy = 0, 0
    fh = open(filename, 'r')
    for _ in range(3): #discard 3 lines
        trash = next(fh)
    for line in fh:#format for the patch data: (x,y),produce rate
        x, y, prodrate = line.split()
        x, y, prodrate = int(x), int(y), float(prodrate)
        location2value[(x,y)] = prodrate
        maxx, maxy = max(x,maxx), max(y,maxy)
    location2value['shape'] = (maxx+1, maxy+1)
    return location2value
def askrandomly(agents, methodname, prng=None, *args, **kwargs):
    """Return list. Calls method `methodname`
    on each agent, where `agents` is any iterable
    of objects supporting this method call.
    A copy of `agents` is shuffled before the method calls.
    :note: `prng` must support `shuffle`
    """
    agents = list(agents)
    if prng is None:
        random.shuffle(agents)
    else:
        prng.shuffle(agents)
    ask(agents, methodname, *args, **kwargs)
    return agents
class Cell15(Patch):
    max_produce = params['cell_max_produce']
    supply = params['cell_initial_supply']
    def initialize(self):
        self.change_color()
    def produce(self):
        self.supply += self.max_produce #the supply of the patches update by adding max_produce
        self.change_color()
    def change_color(self):
        if self.max_produce<= 1.7:#define the centre of the wrold
            r = b = 0
            g = min(2*self.supply, 1.0)
        else:
            r=g=0
            b=1
        self.display(fillcolor=(r, g, b))
    def provide(self, amount):
        amount = min(self.supply, amount)
        self.supply -= amount
        return amount

class Agent12(Agent):
    def move(self):  # defined the move stage for agents
        choice = self.choose_location()
        self.position = choice
    def sortkey11(self, cell):
        return cell.supply
    def choose_location(self):  # choose a empty location from a radius=4 retangle area
        MyType = self.__class__
        hood = self.neighborhood('moore', 4)  # get the neighboring cells
        available = [cell for cell in hood if not cell.get_agents(MyType)]
        available.append(self.patch)  # agent can always stay put
        best_cells = maximizers(self.sortkey11, available)
        if self.patch in best_cells:
            return self.position
        else:
            return random.choice(best_cells).position
    def initialize(self):  # initialize agents' size(wealth)
        self.size = params['agent_initial_size']
        self.display(shape='circle', shapesize=(0.25, 0.25))
        self.change_color()
        self.max_extract = self.world.agent_max_extract

    def change_size(self):  # define the rules for agent to update their size
        self.size += self.extract()
        self.change_color()

    def change_color(self):  # define the color of agent show in a GUI
        g = b = max(0.0, 1.0 - self.size / 10)
        self.display(fillcolor=(1.0, g, b))

    max_extract = params['agent_max_extract']

    def extract(self):  # define the rate for agent get resource from a patch's supply
        mytake = self.patch.provide(self.max_extract)
        return mytake
    def split_if_ready(self):#module that control for new agents add to the model(Unavailable now)
        if self.size > 100000:
            self.propagate()
            self.die()
    def propagate(self):#(Unavailable now)
        MyType = self.__class__ #splits share agent class
        hood4split = self.neighborhood('moore', radius=3)
        cells4split = list()
        for i in range(5): #5 propagation attempts
            for cell in random.sample(hood4split, 5): #5 tries per attempt
                if cell not in cells4split and not cell.get_agents(MyType):
                    cells4split.append(cell)
                    break
        splitlocs = list(cell.position for cell in cells4split)
        splits = self.world.create_agents(MyType, locations=splitlocs)
        return splits
    def venture(self):#control for the quit of agents (Unavailable now)
        if random.uniform(0,1) < params['agent_exit_probability']:
            self.die()
class GUI14(GridWorldGUI):#control for GUI
    def gui(self):
        self.add_clickmonitor('Agent', Agent12, 'size')
        self.add_clickmonitor('Cell', Cell15, 'supply')
        self.add_slider('Initial Number of Bugs', 'n_agents', 10, 500, 10)
        self.add_slider('Agent Max Extract', 'agent_max_extract', 0.0, 2.0, 0.1)
        self.add_button('Set Up', 'setup')
        self.add_button('Run', 'run')
        self.add_button('Stop', 'stop')
        def number_living():
            world = self.subject
            return len(world.get_agents(world.AgentType))
        self.add_plot('Number of Agents', number_living)
        def get_agent_sizes():
            agents = self.subject.get_agents(self.subject.AgentType)
            return list(agent.size for agent in agents)
        self.add_histogram('Agent Sizes', get_agent_sizes, bins=range(11))
        self.add_slider('Init. Size Mean', 'agent_size_mean', 0.0, 1.0, 0.1)
        self.add_slider('Init. Size SD', 'agent_size_sd', 0.0, 0.1, 0.01)
class World15(GridWorld):
    AgentType = Agent12
    PatchType = Cell15
    n_agents = params['n_agents']
    agent_max_extract = params['agent_max_extract']
    agent_size_mean = params['agent_size_mean']
    agent_size_sd = params['agent_size_sd']
    def setup_patches(self):
        celldata = read_celldata(params['cell_data_file'])
        shape = celldata.pop('shape')
        self.set_topology(RectangularGrid(shape=shape))
        patches = self.create_patches(self.PatchType)
        for (x, y), prodrate in celldata.items():
            patches[x][y].max_produce = prodrate
    def setup_agents(self): # setup for the size of initial agents according to the size.txt
        myagents = self.create_agents(self.AgentType, number=self.n_agents)
        i = 0
        for agent in myagents:
            agent.size = siz2[i]
            i = i + 1
    def setup(self):
        self.setup_patches()
        self.setup_agents()
        self.header2logfile() # write header to logfile
    def header2logfile(self):#generate the header of the sizes.csv file
        headers = list(range(100))
        with open('sizes.csv', 'w') as fout:
            fout_csv = csv.writer(fout)
            fout_csv.writerow(headers)
    def log2logfile(self):#write the csv file
        agents = self.get_agents(self.AgentType)
        sizes = list(agent.size for agent in agents)
        NewList = [[x] for x in sizes]
        with open('sizes.csv', 'a',newline='') as fout:
                writer = csv.writer(fout)
                writer.writerow(NewList)
    def sortkey10(self, agent):
        return agent.size
    def schedule(self):
        self.log2logfile()
        ask(self.patches, 'produce')
        agents = self.get_agents(self.AgentType)
        agents.sort(key=self.sortkey10, reverse=True)
        ask(agents, 'move')
        ask(agents, 'change_size')
        if max(agent.size for agent in agents) >= 100: #model stop condition
            self.log2logfile()
            self.stop(exit=True)
        agents = self.get_agents(self.AgentType)#Unavailable
        askrandomly(agents, 'split_if_ready')  # creates new entrants (Unavailable)
        agents = self.get_agents(self.AgentType)  # include new entrants (Unavailable)
        ask(agents, 'venture')#Unavailable
        if (self.iteration == 200) or (len(agents) == 0):  #stop conditions for the whole model  in which iteration = ticks
            self.log2logfile()
            self.stop()
if __name__ == '__main__':
    myworld = World15(topology=None)
    myobserver = GUI14(myworld)
    myobserver.mainloop()