import argparse
import os
import pickle

import mdt_reco


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=str, required=True, help="Path to the configuration file"
    )
    parser.add_argument(
        "--input_name",
        type=str,
        required=True,
        help="Path to the events file to encode",
    )
    parser.add_argument(
        "--output_name",
        type=str,
        required=True,
        help="Output file name for encoded events",
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "../configs", args.config)
    config = mdt_reco.configParser(config_path)
    signal_object = mdt_reco.Signal(config)

    with open(args.input_name, "rb") as f:
        events = pickle.load(f)

    output_dir = f"{script_dir}/../raw_data"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/{args.output_name}.bin"
    signal_object.encodeEvents(events, output_file)
    print(f"Encoded events saved to {output_file}")


if __name__ == "__main__":
    main()
