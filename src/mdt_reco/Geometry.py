import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection

class Chamber:
    def __init__(self, config):
        self.config = config["Geometry"]
        self.chamber = {
                    'x': np.array([], dtype=np.float32),
                    'y': np.array([], dtype=np.float32),
                    'csm_id': np.array([], dtype=np.uint8),
                    'tdc_id': np.array([], dtype=np.uint8),
                    'channel': np.array([], dtype=np.uint8),
                    'layer': np.array([], dtype=np.uint8),
                    'ML': np.array([], dtype=np.uint8),
                    }
        self._radius_container = np.array([], dtype=np.float32)
        self.buildChamber()
        self.fillRadiusContainer()

    def __repr__(self):
        return repr(self.chamber)

    def __getitem__(self, key):
        if key in self.chamber:
            return self.chamber[key]
        else:
            raise KeyError(f"Key '{key}' not found in Chamber data.")

    def buildChamber(self):

        for multilayer_id, multilayer_name in enumerate(self.config["multilayers"]):
            multilayer_config = self.config["multilayers"][multilayer_name]
            self.buildMultilayer(multilayer_config, multilayer_id)
            self.addMultilayer(multilayer_config)

        """
        Numpy appears to be recasting to safer larger types somewhere in the code.
        This could be occuring when filling or during concatenation. A single instance of
        chamber will never cause memory overflow. So we can cast types after creation.
        """
        self.chamber['x'] = self.chamber['x'].astype(dtype=np.float32)
        self.chamber['y'] = self.chamber['y'].astype(dtype=np.float32)
        self.chamber['csm_id'] = self.chamber['csm_id'].astype(dtype=np.uint8)
        self.chamber['tdc_id'] = self.chamber['tdc_id'].astype(dtype=np.uint8)
        self.chamber['channel'] = self.chamber['channel'].astype(dtype=np.uint8)
        self.chamber['layer'] = self.chamber['layer'].astype( dtype=np.uint8)
        self.chamber['ML'] = self.chamber['ML'].astype(dtype=np.uint8)

    def addMultilayer(self, multilayer_config):
        if len(self.chamber['y']) > 0:
            self.multilayer['y'] += self.chamber['y'].max() + multilayer_config["radius"] + self.config["multilayer_spacing"]
        for key in self.multilayer:
            self.chamber[key] = np.concatenate((self.chamber[key], self.multilayer[key]))

    def buildMultilayer(self, multilayer_config, multilayer_id):
        self.multilayer = {
                        'x': np.array([], dtype=np.float32),
                        'y': np.array([], dtype=np.float32),
                        'csm_id': np.array([], dtype=np.int8),
                        'tdc_id': np.array([], dtype=np.int8),
                        'channel': np.array([], dtype=np.int8),
                        'layer': np.array([], dtype=np.int8),
                        'ML': np.array([], dtype=np.int8),
                        }

        for k, activeTDC in enumerate(multilayer_config["activeTDCs"]):
            if activeTDC:
                TDC = self.buildTDC(multilayer_config, k)
                TDC['x'] += k*TDC['x'].max()
                self.addTDC(TDC)
        self.multilayer['ML'] = np.full(len(self.multilayer['x']), multilayer_id)


    def addTDC(self, TDC):
        for key in TDC:
            self.multilayer[key] = np.concatenate((self.multilayer[key], TDC[key]))

    def buildTDC(self, multilayer_config, k):
        tdc_id = multilayer_config["TDC_ids"][k]
        csm_id = multilayer_config["CSM_ids"][k]
        if multilayer_config["tdcType"] == "446":
            TDC = self.buildTDCType446(multilayer_config, tdc_id, csm_id)
        elif multilayer_config["tdcType"] == "436":
            TDC = self.buildTDCType436(multilayer_config, tdc_id, csm_id)
        return TDC

    def buildTDCType446(self, multilayer_config, tdc_id, csm_id):
        nLayers = 4
        tubesPerLayer = 6
        TDC_446 = {
            'x': np.zeros(24),
            'y': np.zeros(24),
            'csm_id': np.full(24, csm_id),
            'tdc_id': np.full(24, tdc_id),
            'channel': np.array([[5, 3, 4, 2, 0, 1],
                                [11, 9, 10, 8, 6, 7],
                                [17, 15, 16, 14, 12, 13],
                                [23, 21, 22, 20, 18, 19]]).flatten(),
            'layer': np.array([[0, 0, 0, 0, 0, 0],
                                [1, 1, 1, 1, 1, 1],
                                [2, 2, 2, 2, 2, 2],
                                [3, 3, 3, 3, 3, 3]]).flatten(),
        }
        x_shift = multilayer_config['radius'] + multilayer_config["tube_spacing"]/2
        for tube_num in range(tubesPerLayer):
            TDC_446['x'][tube_num] = (2*tube_num + 2)*x_shift
            TDC_446['x'][tube_num + 6] = (2*tube_num + 1)*x_shift
            TDC_446['x'][tube_num + 12] = TDC_446['x'][tube_num]
            TDC_446['x'][tube_num + 18] = TDC_446['x'][tube_num + 6]
        tube_center_distance = 2*x_shift
        y_spacing = .5*tube_center_distance*np.sqrt(3)
        for layer in range(nLayers):
            TDC_446['y'][tubesPerLayer*layer:tubesPerLayer*(layer+1)] = y_spacing*layer + tube_center_distance/2
        #TDC_446['channel'] = TDC_446['channel'] + tdc_id * 100
        return TDC_446

    def buildTDCType436(self, multilayer_config, tdc_id, csm_id):
        nLayers = 4
        tubesPerLayer = 6
        TDC_436 = {
            'x': np.zeros(24),
            'y': np.zeros(24),
            'csm_id': np.full(24, csm_id),
            'tdc_id': np.full(24, tdc_id),
            'channel': np.array([[3, 1, 5, 0, 2, 4],
                                [9, 7, 11, 6, 8, 10],
                                [15, 13, 17, 12, 14, 16],
                                [19, 21, 23, 18, 20, 22]]).flatten(),
            'layer': np.array([[0, 0, 0, 0, 0, 0],
                                [1, 1, 1, 1, 1, 1],
                                [2, 2, 2, 2, 2, 2],
                                [3, 3, 3, 3, 3, 3]]).flatten(),
        }
        x_shift = multilayer_config['radius'] + multilayer_config["tube_spacing"]/2
        for tube_num in range(tubesPerLayer):
            TDC_436['x'][tube_num] = (2*tube_num + 1)*x_shift
            TDC_436['x'][tube_num + 6] = (2*tube_num + 2)*x_shift
            TDC_436['x'][tube_num + 12] = TDC_436['x'][tube_num]
            TDC_436['x'][tube_num + 18] = TDC_436['x'][tube_num + 6]
        tube_center_distance = 2*x_shift
        y_spacing = .5*tube_center_distance*np.sqrt(3)
        for layer in range(nLayers):
            TDC_436['y'][tubesPerLayer*layer:tubesPerLayer*(layer+1)] = y_spacing*layer + tube_center_distance/2
        #TDC_436['channel'] = TDC_436['channel'] + tdc_id * 100
        return TDC_436

    def getXY(self, tdc_id, channel):
        x = self['x'][np.where((self['tdc_id'] == tdc_id) & (self['channel'] == channel))]
        y = self['y'][np.where((self['tdc_id'] == tdc_id) & (self['channel'] == channel))]
        return x, y

    def getRadius(self, tdc_id):
        return self._radius_container[tdc_id]

    def fillRadiusContainer(self):
        max_tdc = np.max(self.chamber['tdc_id']+1)
        self._radius_container = np.zeros(max_tdc, dtype = np.float32)
        for multilayer in self.config["multilayers"]:
            for tdc_id in self.config["multilayers"][multilayer]["TDC_ids"]:
                self._radius_container[tdc_id] = self.config["multilayers"][multilayer]['radius']

    def draw(self, ax=None, key=None):
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        xmax = self.chamber["x"].max()
        xmin = self.chamber["x"].min()
        ymax = self.chamber["y"].max()
        ymin = self.chamber["y"].min()
        Ntubes = len(self.chamber["x"])
        patches = []
        for tube in range(Ntubes):
            ml_num = self.chamber['ML'][tube]
            radius = self.config["multilayers"][f"multilayer{int(ml_num + 1)}"]["radius"]
            center = (self.chamber["x"][tube], self.chamber["y"][tube])
            if int(self.chamber['tdc_id'][tube]/2) % 2 == 1:
                circle = Circle(center, radius, fill=True, facecolor='lightgrey', ec='black', lw=1)
            else:
                circle = Circle(center, radius, fill=False, ec='black', lw=1)
            if key == "channel":
                ax.text(center[0], center[1], self.chamber["channel"][tube]%100, color='black', fontsize=10, ha='center', va='center')
            elif key is not None:
                ax.text(center[0], center[1], self.chamber[key][tube], color='black', fontsize=10, ha='center', va='center')
            # ax.add_patch(circle)
            patches.append(circle)
        collection = PatchCollection(patches, match_original=True)
        ax.add_collection(collection)
        ax.set_xlim(xmin-radius*2, xmax + radius*2)
        ax.set_ylim(ymin-radius*2, ymax + radius*2)

        ax.set_xlabel("x[mm]")
        ax.set_ylabel("y[mm]")
        ax.set_aspect("equal")
        ax.set_title("Chamber Geometry")
