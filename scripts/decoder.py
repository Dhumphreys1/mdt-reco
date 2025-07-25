import argparse
import os
import pickle

import mdt_reco


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=str, required=True, help="Path to the configuration file"
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "../configs", args.config)
    config = mdt_reco.configParser(config_path)
    signal_object = mdt_reco.Signal(config)

    input_dir = f"{script_dir}/../raw_data"
    file_path = f"{input_dir}/{config['General']['input_file']}.bin"
    if not os.path.exists(file_path):
        msg = f"Input file {file_path} does not exist. Please provide a valid file."
        raise FileNotFoundError(msg)

    print(f"Decoding events from {file_path}")
    events = signal_object.decodeEvents(file_path)

    output_dir = f"{script_dir}/../output/{config['General']['run_name']}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/{config['General']['input_name']}.pkl"

    with open(output_file, "wb") as f:
        pickle.dump(events, f)
    print(f"Decoded events saved to {output_file}")


if __name__ == "__main__":
    main()
