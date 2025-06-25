import numpy as np

MZ   MezzCh  locY      locZ     Layer  Tube_y ML
0    105     45.7675   30.0175  1      1      1
0    103     45.7675   60.0525  1      2      1
0    104     45.7675   90.0875  1      3      1
0    102     45.7675   120.122  1      4      1
0    100     45.7675   150.157  1      5      1
0    101     45.7675   180.192  1      6      1

0    111     71.7786   15.0     2      1      1
0    109     71.7786   45.035   2      2      1
0    110     71.7786   75.07    2      3      1
0    108     71.7786   105.105  2      4      1
0    106     71.7786   135.14   2      5      1
0    107     71.7786   165.175  2      6      1

0    117     97.7896   30.0175  3      1      1
0    115     97.7896   60.0525  3      2      1
0    116     97.7896   90.0875  3      3      1
0    114     97.7896   120.122  3      4      1
0    112     97.7896   150.157  3      5      1
0    113     97.7896   180.192  3      6      1

0    123     123.801   15.0     4      1      1
0    121     123.801   45.035   4      2      1
0    122     123.801   75.07    4      3      1
0    120     123.801   105.105  4      4      1
0    118     123.801   135.14   4      5      1
0    119     123.801   165.175  4      6      1

class Chamber:
    def __init__(self, chamber_type: str):
        if chamber_type == 'sMDT':
            self.radius = 7.5
            self.layer_distance = 13.0769836
        elif chamber_type == 'MDT':
            self.radius = 15.0
            self.layer_distance = 26.0111
        self.BuildTdcs()
    def BuildTdcs(self):
        """
        tdcTypeA and tdcTypeB are generic TDCs defined by 4 layers by 6 tubes.
        Their x and y are coordinates depending on the radius of the chamber.
        x (Float): The local x coordinate of the tube center.
        y (Float): The local y coordinate of the tube center.
        tdc_id (Int): The TDC ID, this is constant for all tubes
        channel (Int): The channel number of the tube, this is the channel recorded by the TDC during digitization.
        layer (Int): The layer number of the tube, this is constant for each row of tubes
        ML (Int): Multilayer. Chambers typically have 2 multilayers, 1 multilayer is a row of TDCs. Effectively a TDC group.
        """
        tdcTypeA = {
            'x': np.zeros(24),
            'y': np.zeros(24),
            'tdc_id': np.zeros(24),
            'channel': np.zeros(24),
            'layer': np.zeros(24),
            'ML': np.zeros(24),
        }
        tdcTypeB = {
            'x': np.zeros(24),
            'y': np.zeros(24),
            'tdc_id': np.zeros(24),
            'channel': np.zeros(24),
            'layer': np.zeros(24),
            'ML': np.zeros(24),
        }

        typeA_channel_map = [5, 3, 4, 2, 0, 1]
        for i in range(4):
            layer = i // 6
            tdcTypeA["layer"][i:(i+1)*6] = layer
            tdcTypeA["x"][i] = self.radius
            tdcTypeA["y"][i] = self.radius
            tdcTypeA["channel"][i] = typeA_channel_map[i % 6] + 6*(layer)