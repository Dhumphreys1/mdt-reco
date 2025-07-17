import numpy as np
import random
from .Geometry import Chamber



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
    """
    when creating a class object you need to pass it the object config. config is defined as stated below:

    config_path = "/data/dhumphreys/L0MDT/mdt-reco/configs/ci_config.yaml"
    config = mdt_reco.configParser(config_path)

    """

    def __init__(self, config):
        
        self.Chamber= Chamber(config)
        self.x_interval = [self.Chamber["x"].min() - 30,  self.Chamber["x"].max() + 30]
        self.y_interval = [self.Chamber["y"].max() + 30, self.Chamber["y"].max() + 60]
        
    def simEvent(self):
        sim_event = {
            "pos_init": [],
            "angle_of_attack": [],
            "px": [],
            "py": []
        }
        self.x_pos = np.random.uniform(self.x_interval[0], self.x_interval[1])
        self.y_pos = np.random.uniform(self.y_interval[0], self.y_interval[1])
    
        sim_event["pos_init"]=[self.x_pos,self.y_pos]
        sim_event["angle_of_attack"]=np.random.uniform(-Generator.angle_max, Generator.angle_max)
        sim_event["px"]=Generator.Momentum*np.sin(sim_event["angle_of_attack"])
        sim_event["py"]=Generator.Momentum*np.cos(sim_event["angle_of_attack"])
        
        return sim_event
    
    def simEvents(self,num_events):
        sim_events=[]
        for i in range(num_events):
            sim_events.append(self.simEvent())
        return sim_events


    def findTrajectory(self, B, sim_event):
        """
        I expect this function to be run after the entire SimEvents dictionary is created. I think it will still work if this is not the case but 
        it would be easier if write some loop that develops the entire SimEvents dictionary(SimEvents() for i in range....)
        then just run FindTrajectory once as it just loops through the entirety of the dictionary in SimEvents
        """
        track_params={
            "A":[],
            "C":[],
            "tubes_hit(indices)":[],
        }
        
        if B == 0:
        
            x0, y0 = sim_event["pos_init"]
            px = sim_event["px"]
            py = sim_event["py"]

            # Compute slope (A) and y-intercept (C)
            A = py / px
            C = y0 - A * x0

            

            # Calculate distance from track to all tubes
            x = self.Chamber["x"]
            y = self.Chamber["y"]
            d = np.abs(A * x - y + C) / np.sqrt(A**2 + 1)
            #pot_hits= np.where(d < 15)

            tdc_ids = self.Chamber["tdc_id"] 
            tube_radi= self.Chamber.getRadius(tdc_ids)


            # Determine which tubes are hit
            tubes_hit = np.where(d< tube_radi)[0]


            # Store A and C
            track_params["A"].append(A)
            track_params["C"].append(C)
            track_params["tubes_hit(indices)"].append(tubes_hit)

        else:
            raise NotImplementedError
            # Implement the case for non-zero magnetic field if needed
        return track_params



