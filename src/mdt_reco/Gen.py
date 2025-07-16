import numpy as np
import random



class Generator:
    """
    A (hopefully) simple event generator class that will produce a muon with a specific momentum(10-1000Gev),
    a random initial direction. this class should also have a function called FindTrajectory(FT) which will return a path given a magnetic field
    use the results of FT to determine what path the particles go through
    csm_id of all the tdc's hit, tdc_id's, channels of tdc's, drift time needs drift radius but not filled by me,tdc_time, pulse width(random normal number) 
    """
    np.random.seed(1234)
    muon_mass= .10566 #muon mass in GeV
    angle_max = np.pi/3.5
    Energy = random.gauss(4,1)
    Momentum = np.sqrt(Energy**2 - muon_mass**2) # Total muon momentum in GeV/c

    def __init__(self, Chamber):
        self.x_interval = [Chamber["locX"].min() - 30,  Chamber["locX"].max() + 30]
        self.y_interval = [Chamber["locY"].max() + 30, Chamber["locY"].max() + 60]
        self.chamber= Chamber
        self.SimEvents = {
            "pos_init": [],
            "angle_of_attack": [],
            "px": [],
            "py": []
        }
        self.track_params={
            "A":[],
            "C":[],
            "tubes_hit":[]

        }
        

    def SimEvents(self):
        self.x_pos = np.random.uniform(self.x_interval[0], self.x_interval[1])
        self.y_pos = np.random.uniform(self.y_interval[0], self.y_interval[1])
    
        self.SimEvents["pos_init"].append([self.x_pos,self.y_pos])
        self.SimEvents["angle_of_attack"].append([np.random.uniform(-Generator.angle_max, Generator.angle_max)])
        self.SimEvents["px"] = Generator.Momentum*np.sin(self.SimEvents["angle_of_attack"])
        self.SimEvents["py"] = Generator.Momentum*np.cos(self.SimEvents["angle_of_attack"])
        
    def FindTrajectory(self):
        """
        I expect this function to be run after the entire SimEvents dictionary is created. I think it will still work if this is not the case but 
        it would be easier if write some loop that develops the entire SimEvents dictionary(SimEvents() for i in range....)
        then just run FindTrajectory once as it just loops through the entirety of the dictionary in SimEvents
        """
        for i in range(len(self.SimEvents["pos_init"])):
            x0, y0 = self.SimEvents["pos_init"][i]
            px = self.SimEvents["px"][i]
            py = self.SimEvents["py"][i]

        # Compute slope (A) and y-intercept (C)
            A = py / px
            C = y0 - A * x0

        # Store A and C
            self.track_params["A"].append(A)
            self.track_params["C"].append(C)

        # Calculate distance from track to all tubes
            x = self.chamber["locX"]
            y = self.chamber["locY"]
            d = np.abs(A * x - y + C) / np.sqrt(A**2 + 1)

        # Determine which tubes are hit
            tubes_hit = np.where(d < self.chamber.radius())[0]
            self.track_params["tubes_hit"].append(tubes_hit)



