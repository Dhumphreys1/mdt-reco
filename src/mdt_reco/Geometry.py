import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

class Chamber:
    def __init__(self, config):
        self.config = config["Geometry"]
        self.Chamber = {
                    'x':np.array([]),
                    'y':np.array([]),
                    'tdc_id':np.array([]),
                    'channel':np.array([]),
                    'layer':np.array([]),
                    'ML':np.array([]),
                    }
        self.BuildChamber()

    def BuildChamber(self):

        for multilayer_id, multilayer in enumerate(self.config["multilayers"]):
            self.BuildMultilayer(self.config["multilayers"][multilayer], multilayer_id)
            self.AddMultilayer()

        # A single instance of chamber will never cause memory overflow.
        # Numpy being annoying with initial type casting.
        # Recasting everything to smaller types once the chamber is buillt
        self.Chamber['tdc_id'] = np.array(self.Chamber['tdc_id'], dtype=np.int32)
        self.Chamber['channel'] = np.array(self.Chamber['channel'], dtype=np.int32)
        self.Chamber['layer'] = np.array(self.Chamber['layer'], dtype=np.int32)
        self.Chamber['ML'] = np.array(self.Chamber['ML'], dtype=np.int32)

    def AddMultilayer(self):
        if len(self.Chamber['y']) > 0:
            self.multilayer['y'] += self.Chamber['y'].max() + self.config["multilayer_spacing"]
        for key in self.multilayer:
            self.Chamber[key] = np.concatenate((self.Chamber[key], self.multilayer[key]))

    def BuildMultilayer(self, multilayer, multilayer_id):

        self.multilayer = {
                'x':np.array([]),
                'y':np.array([]),
                'tdc_id':np.array([]),
                'channel':np.array([]),
                'layer':np.array([]),
                'ML':np.array([]),
                }

        for k, activeTDC in enumerate(multilayer["activeTDCs"]):
            if activeTDC:

                TDC = self.BuildTDC(multilayer, k)
                TDC['x'] += k*TDC['x'].max()
                #TDC['x'] += k*(TDC['x'][1] - TDC['x'][0])/2 # This shifts by the maximum plus 1 tube radius + tube spacing
                self.AddTDC(TDC)
        self.multilayer['ML'] = np.full(len(self.multilayer['x']), multilayer_id)


    def AddTDC(self, TDC):
        for key in TDC:
            self.multilayer[key] = np.concatenate((self.multilayer[key], TDC[key]))

    def BuildTDC(self, multilayer, k):
        tdc_id = multilayer["TDC_ids"][k]
        if multilayer["tdcType"] == "446":
            TDC = self.BuildTDCType446(multilayer, tdc_id)
        elif multilayer["tdcType"] == "436":
            TDC = self.BuildTDCType436(multilayer, tdc_id)
        return TDC

    def BuildTDCType446(self, multilayer, tdc_id):
        nLayers = 4
        tubesPerLayer = 6
        TDC_446 = {
            'x': np.zeros(24),
            'y': np.zeros(24),
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
        x_shift = multilayer['radius'] + multilayer["tube_spacing"]/2
        for tube_num in range(tubesPerLayer):
            TDC_446['x'][tube_num] = (2*tube_num + 2)*x_shift
            TDC_446['x'][tube_num + 6] = (2*tube_num + 1)*x_shift
            TDC_446['x'][tube_num + 12] = TDC_446['x'][tube_num]
            TDC_446['x'][tube_num + 18] = TDC_446['x'][tube_num + 6]
        tube_center_distance = 2*multilayer["radius"] + multilayer["tube_spacing"]
        y_spacing = .5*tube_center_distance*np.sqrt(3)
        for layer in range(nLayers):
            TDC_446['y'][tubesPerLayer*layer:tubesPerLayer*(layer+1)] = y_spacing*layer + tube_center_distance/2
        TDC_446['channel'] = TDC_446['channel'] + tdc_id * 100

        return TDC_446

    def BuildTDCType436(self, multilayer, tdc_id):
        nLayers = 4
        tubesPerLayer = 6
        TDC_436 = {
            'x': np.zeros(24),
            'y': np.zeros(24),
            'tdc_id': np.full(24, tdc_id),
            'channel': np.array([[3, 1, 5, 0, 2, 4],
                                [9, 7, 11, 6, 8, 10],
                                [15, 13, 17, 12, 14, 16],
                                [19, 21, 23, 18, 20, 22]]).flatten(),
            'layer': np.array([[0, 0, 0, 0, 0, 0],
                                [1, 1, 1, 1, 1, 1],
                                [2, 2, 2, 2, 2, 2],
                                [3, 3, 3, 3, 3, 3]], dtype = np.int32).flatten(),
        }
        x_shift = multilayer['radius'] + multilayer["tube_spacing"]/2
        for tube_num in range(tubesPerLayer):
            TDC_436['x'][tube_num] = (2*tube_num + 1)*x_shift
            TDC_436['x'][tube_num + 6] = (2*tube_num + 2)*x_shift
            TDC_436['x'][tube_num + 12] = TDC_436['x'][tube_num]
            TDC_436['x'][tube_num + 18] = TDC_436['x'][tube_num + 6]
        tube_center_distance = 2*multilayer["radius"] + multilayer["tube_spacing"]
        # y_spacing = np.sqrt(tube_center_distance**2 - (tube_center_distance/2)**2)
        y_spacing = .5*tube_center_distance*np.sqrt(3)
        for layer in range(nLayers):
            TDC_436['y'][tubesPerLayer*layer:tubesPerLayer*(layer+1)] = y_spacing*layer + tube_center_distance/2
        TDC_436['channel'] = TDC_436['channel'] + tdc_id * 100
        return TDC_436

    def Draw(self, ax=None, key=None):
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        xmax = self.Chamber["x"].max()
        xmin = self.Chamber["x"].min()
        ymax = self.Chamber["y"].max()
        ymin = self.Chamber["y"].min()
        Ntubes = len(self.Chamber["x"])
        for tube in range(Ntubes):
            ml_num = self.Chamber['ML'][tube]
            radius = self.config["multilayers"][f"multilayer{int(ml_num + 1)}"]["radius"]
            center = (self.Chamber["x"][tube], self.Chamber["y"][tube])
            if int(self.Chamber['tdc_id'][tube]/2)%2 == 1:
                # Draw the tube as a filled circle
                circle = Circle(center, radius, fill=True,facecolor='lightgrey', ec='black', lw=1)
            else:
                circle = Circle(center, radius, fill=False, ec='black', lw=1)
            if key is None:
                continue
            elif key == "channel":
                ax.text(center[0], center[1], self.Chamber["channel"][tube]%100, color='black', fontsize=10, ha='center', va='center')
            else:
                ax.text(center[0], center[1], self.Chamber[key][tube], color='black', fontsize=10, ha='center', va='center')
            ax.add_patch(circle)
        ax.set_xlim(xmin-radius*2, xmax + radius*2)
        ax.set_ylim(ymin-radius*2, ymax + radius*2)

        ax.set_xlabel("x[mm]")
        ax.set_ylabel("y[mm]")
        ax.set_aspect("equal")
        ax.set_title("Chamber Geometry")