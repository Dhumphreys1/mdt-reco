from .ConfigParser import ConfigParser
from .Event import Event
from .Gen import Generator
from .Geometry import Chamber
from .Signal import Signal
from .TDCFitter import TDCFitter
from .TrackFitter import TrackFitter

configParser = ConfigParser
geo = Chamber
event = Event
gen = Generator
trackFitter = TrackFitter
signal = Signal
tdcFitter = TDCFitter
