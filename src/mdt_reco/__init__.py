from .ConfigParser import ConfigParser
from .Event import Event
from .Gen import Generator
from .Geometry import Chamber
from .TDCFitter import TDCFitter
from .TrackFitter import TrackFitter
from .Signal import Signal

configParser = ConfigParser
geo = Chamber
event = Event
gen = Generator
trackFitter = TrackFitter
Signal = Signal
tdcFitter = TDCFitter
