import argparse
import os
import pickle

import mdt_reco


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("events")
    parser.add_argument("file")
    args = parser.parse_args()
    config_path = args.config
    config = mdt_reco.configParser(config_path)
    signal_object = mdt_reco.Signal(config)
    with open(args.events, "rb") as f:
        events = pickle.load(f)
        output_dir = "../raw_data"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/{args.file}"
        signal_object.encodeEvents(events, output_file)


if __name__ == "__main__":
    main()
