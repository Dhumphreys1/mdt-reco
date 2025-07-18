import argparse
import os
import pickle

import mdt_reco


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("event_name")
    args = parser.parse_args()
    config_path = args.config
    config = mdt_reco.configParser(config_path)
    signal_object = mdt_reco.Signal(config)
    path_to_events = "../raw_data"
    file_path = f"{path_to_events}/{args.event_name}.bin"
    events = signal_object.decodeEvents(file_path)
    run_name = config["General"]["run_name"]
    output_dir = f"../output/{run_name}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/{args.event_name}.pkl"
    with open(output_file, "wb") as f:
        pickle.dump(events, f)


if __name__ == "__main__":
    main()
