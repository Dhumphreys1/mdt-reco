import argparse

import numpy as np

import mdt_reco

argparser = argparse.ArgumentParser()
argparser.add_argument(
    "--config",
    type=str,
    default="../ci_config.yaml",
    help="Path to the configuration file",
)
args = argparser.parse_args()


def getTDCInfo(events):
    tdc_ids = []
    tdc_times = []
    adc_times = []
    tdc_channels = []

    for event in events:
        tdc_ids.append(event["tdc_id"])
        tdc_times.append(event["tdc_time"])
        adc_times.append(event["adc_time"])
        tdc_channels.append(event["channels"])

    tdc_ids = np.concatenate(tdc_ids)
    tdc_times = np.concatenate(tdc_times)
    adc_times = np.concatenate(adc_times)
    tdc_channels = np.concatenate(tdc_channels)

    return tdc_ids, tdc_times, adc_times, tdc_channels


def main():
    config_path = args.config
    config = mdt_reco.configParser(config_path)
    # run_path = f"../output/{config['General']['run_name']}.npy"
    # events = np.load(events_path, allow_pickle=True)

    path = "/home/dhumphreys/L0MDT/l0mdt_felixanalysis/data/simulated/mdt-reco_data/"
    file_name = "events_10k.npy"
    events_path = path + file_name
    data = np.load(events_path, allow_pickle=True)

    events = []
    for event in data:
        empty_event = mdt_reco.event()
        empty_event["tdc_id"] = event["tdc"].astype(np.uint8)
        empty_event["channel"] = event["channel"].astype(np.uint8)
        empty_event["drift_time"] = event["drift_time"].astype(np.float32)
        empty_event["tdc_time"] = event["tdc_time"].astype(np.float32)
        empty_event["x"] = event["x"].astype(np.float32)
        empty_event["y"] = event["y"].astype(np.float32)
        events.append(empty_event)

    del data
    tdc_ids, tdc_times, adc_times, tdc_channels = getTDCInfo(events)
    del events
    unqiue_tdc_ids = np.concatenate(
        [
            config["Geometry"]["multilayers"][multilayer]["TDC_ids"]
            for multilayer in config["Geometry"]["multilayers"]
        ]
    )

    histos = {}
    for tdc_id in unqiue_tdc_ids:
        mask = tdc_ids == tdc_id
        tdc_times_for_id = tdc_times[mask]
        adc_times_for_id = adc_times[mask]

        if len(tdc_times_for_id) > 0:  # Only create histogram if there's data
            tdc_counts, tdc_bin_edges = np.histogram(tdc_times_for_id, bins=50)
            adc_counts, adc_bin_edges = np.histogram(adc_times_for_id, bins=50)
            histos[tdc_id] = {
                "adc_counts": adc_counts.astype(np.int32),
                "adc_bins": adc_bin_edges.astype(np.float32),
                "tdc_counts": tdc_counts.astype(np.int32),
                "tdc_bins": tdc_bin_edges.astype(np.float32),
            }
