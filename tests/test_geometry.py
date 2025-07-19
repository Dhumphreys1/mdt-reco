from mdt_reco.Geometry import Chamber
from mdt_reco import ConfigParser
import pickle


def test_geo():
    """
    Test that generating a Geometry object produces the expected output.
    Expected output is stored in ci_test_geo.pickle. This pickle file
    stores the reference object that we compare the current output to.
    """
    with open("tests/ci_test_geo.pickle", "rb") as handle:
        ref_ch = pickle.load(handle)

    # current Geometry
    path = "configs/ci_config.yaml"
    cp = ConfigParser(path)
    current_ch = Chamber(cp)
    if current_ch.chamber.keys() != ref_ch.chamber.keys():
        assert False
    for key in current_ch.chamber.keys():
        if (current_ch.chamber[key] != ref_ch.chamber[key]).all():
            assert False
    assert True
