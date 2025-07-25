import argparse
import os
import pickle

import numpy as np
import mdt_reco

#from RTFitter import RTFitter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=str, required=True, help="Path to the configuration file"
    )
    args = parser.parse_args()

    config_path = os.path.abspath(args.config)
    config = mdt_reco.configParser(config_path)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = f"{script_dir}/../output/{config['General']['run_name']}"
    figure_dir = os.path.join(output_dir, "figures")
    os.makedirs(figure_dir, exist_ok=True)

    input_filename = config["General"]["input_file"]
    input_path = os.path.join(output_dir, f"{input_filename}.pkl")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input pickle file not found at: {input_path}")
    
    with open(input_path, "rb") as f:
        events = pickle.load(f)

    fitter = mdt_reco.rtFitter(config_path=config_path, data=events)
#    fitter.events = events
    fitter.fitRTCurve()

if __name__ == "__main__":
    main()
