import random
from time import sleep
from gridworld import ask
from gridworld import Agent, TorusGrid, GridWorld
from gridworld import moore_neighborhood, GridWorldGUI
from gridworld import Patch
from gridworld import describe
from gridworld import maximizers
from gridworld import RectangularGrid
params = dict(world_shape=(100,100), n_agents=100, maxiter=100)
params.update(cell_data_file='Cell.Data')
params.update(agent_initial_size=0.0, extraction_rate=0.1)
params.update(cell_initial_supply=0.0, cell_max_produce=0.01)
params.update(agent_max_extract=1.0)
params.update(agent_exit_probability=0)
params.update(agent_size_mean=0.1, agent_size_sd=0.03)
params.update(logfile='sizes.csv', logformat='\n{min}, {mean}, {max}')
def read_celldata(filename):
    location2value = dict()
    maxx, maxy = 0, 0
    fh = open(filename, 'r')
    for _ in range(3): #discard 3 lines
        trash = next(fh)
    for line in fh:
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
class Agent01(Agent):
    def move(self):
        choice = self.choose_location()
        self.position = choice
    def choose_location(self):
        old_position = self.position
        hood = moore_neighborhood(radius=4, center=old_position)
        random.shuffle(hood)
        for location in hood:
            if self.world.is_empty(location):
                return location
        return old_position
class Agent02(Agent01):
    def initialize(self):
        self.size = params['agent_initial_size']
        self.display(shape='circle', shapesize=(0.25,0.25))
        self.change_color()
    def change_size(self):
        self.size += self.extract()
        self.change_color()
    def extract(self):
        return params['extraction_rate']
    def change_color(self):
        g = b = max(0.0, 1.0 - self.size/10)
        self.display(fillcolor=(1.0, g, b))
class Cell03(Patch):
    max_produce = params['cell_max_produce']
    supply = params['cell_initial_supply']
    def produce(self):
        self.supply += random.uniform(0, self.max_produce)
    def provide(self, amount):
        amount = min(self.supply, amount)
        self.supply -= amount
        return amount
class Agent03(Agent02):
    max_extract = params['agent_max_extract']
    def extract(self):
        mytake = self.patch.provide(self.max_extract)
        return mytake
class World03(GridWorld):
    def schedule(self):
        ask(self.patches, 'produce')
        ask(self.agents, 'move')
        ask(self.agents, 'change_size')
class GUI04(GridWorldGUI):
    def gui(self):
        self.add_clickmonitor('Agent', Agent03, 'size')
        self.add_clickmonitor('Cell', Cell03, 'supply')
class Agent05(Agent03):
    def initialize(self):
        Agent03.initialize(self)
        self.max_extract = self.world.agent_max_extract
class World05(World03):
    AgentType = Agent05
    PatchType = Cell03
    n_agents = params['n_agents']
    agent_max_extract = params['agent_max_extract']
    def setup(self):
        self.setup_patches()
        self.setup_agents()
    def setup_patches(self):
        self.create_patches(self.PatchType)
    def setup_agents(self):
        self.create_agents(self.AgentType, number=self.n_agents)
class GUI05(GUI04):
    def gui(self):
        GUI04.gui(self)
        self.add_slider('Initial Number of Bugs', 'n_agents', 10, 500, 10)
        self.add_slider('Agent Max Extract', 'agent_max_extract', 0.0, 2.0, 0.1)
        self.add_button('Set Up', 'setup')
        self.add_button('Run', 'run')
        self.add_button('Stop', 'stop')
class GUI06(GUI05):
    def gui(self):
        GUI05.gui(self)
        def get_agent_sizes():
            agents = self.subject.get_agents(self.subject.AgentType)
            return list(agent.size for agent in agents)
        self.add_histogram('Agent Sizes', get_agent_sizes, bins=range(11))
class World07(World05):
    def schedule(self):
        World05.schedule(self)
        if max(agent.size for agent in self.agents) >= 100:
            self.stop(exit=True)
class World08(World05):
    def setup(self):
        World05.setup(self)
        self.header2logfile() # write header to logfile
    def header2logfile(self):
        with open(params['logfile'], 'w') as fout:
            fout.write('minimum, mean, maximum')
    def log2logfile(self):
        agents = self.get_agents(self.AgentType)
        sizes = list(agent.size for agent in agents)
        stats = describe(sizes)
        with open(params['logfile'], 'a') as fout:
            fout.write(params['logformat'].format(**stats))
    def schedule(self):
        self.log2logfile() #self. agents size
        World05.schedule(self)
        if max(agent.size for agent in self.agents) >= 100: #from model 7
            self.log2logfile() #log final agent state
            self.stop(exit=True)
class World10(World08):
    def sortkey10(self, agent):
        return agent.size
    def schedule(self):
        self.log2logfile() #from model 8
        ask(self.patches, 'produce') #from model 3
        agents = self.get_agents(self.AgentType)
        agents.sort(key=self.sortkey10, reverse=True) #model 10
        ask(agents, 'move') #from model 1
        ask(agents, 'change_size') #from model 3
        if max(agent.size for agent in agents) >= 100: #from model 7
            self.log2logfile() #from model 8
            self.stop(exit=True)
class Agent11(Agent05):
    def sortkey11(self, cell):
        return cell.supply
    def choose_location(self):
        MyType = self.__class__
        hood = self.neighborhood('moore', 4) #get the neighboring cells
        available = [cell for cell in hood if not cell.get_agents(MyType)]
        available.append(self.patch) #agent can always stay put
        best_cells = maximizers(self.sortkey11, available)
        if self.patch in best_cells:
            return self.position
        else:
            return random.choice(best_cells).position
class World11(World10):
    AgentType = Agent11
class Agent12(Agent11):
    def split_if_ready(self):
        if self.size > 100000:
            self.propagate()
            self.die()
    def propagate(self):
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
    def venture(self):
        if random.uniform(0,1) < params['agent_exit_probability']:
            self.die()
class World12(World11):
    AgentType = Agent12
    def schedule(self):
        World11.schedule(self)
        agents = self.get_agents(self.AgentType)
        askrandomly(agents, 'split_if_ready') #creates new entrants
        agents = self.get_agents(self.AgentType) #include new entrants
        ask(agents, 'venture')
        if (self.iteration==200) or (len(agents)==0): #model 12
            self.log2logfile() #from model 8
            self.stop()
class GUI13(GUI06):
    def gui(self):
        GUI06.gui(self)
        def number_living():
            world = self.subject
            return len(world.get_agents(world.AgentType))
        self.add_plot('Number of Agents', number_living)
class World14(World12):
    agent_size_mean = params['agent_size_mean']
    agent_size_sd = params['agent_size_sd']
    def setup_agents(self): #random size for initial agents
        myagents = self.create_agents(self.AgentType, number=self.n_agents)
        mean = self.agent_size_mean
        sd = self.agent_size_sd
        for agent in myagents:
            size_drawn = random.normalvariate(mean, sd)
            agent.size = max(0.0, size_drawn)
class GUI14(GUI13):
    def gui(self):
        GUI13.gui(self)
        self.add_slider('Init. Size Mean', 'agent_size_mean', 0.0, 1.0, 0.1)
        self.add_slider('Init. Size SD', 'agent_size_sd', 0.0, 0.1, 0.01)
class Cell15(Cell03):
    def initialize(self):
        self.change_color()
    def produce(self):
        self.supply += self.max_produce #no longer random
        self.change_color()
    def change_color(self):
        if self.max_produce<= 1.7:
            r = b = 0
            g = min(2*self.supply, 1.0)
        else:
            r=g=0
            b=1
        self.display(fillcolor=(r, g, b))
class World15(World14):
    PatchType = Cell15
    def setup_patches(self):
        celldata = read_celldata(params['cell_data_file'])
        shape = celldata.pop('shape')
        self.set_topology(RectangularGrid(shape=shape))
        patches = self.create_patches(self.PatchType)
        for (x,y), prodrate in celldata.items():
            patches[x][y].max_produce = prodrate
if __name__ == '__main__':
    myworld = World15(topology=None)
    myobserver = GUI14(myworld)
    myobserver.mainloop()