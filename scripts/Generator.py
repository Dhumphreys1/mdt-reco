import argparse
import mdt_reco
import os
import numpy as np
import pickle


def main():
    parser = argparse.ArgumentParser(description="Muon Event Generator")
    parser.add_argument(
        "--config", "-c", required=True, help="Path to config YAML file"
    )
    args = parser.parse_args()

    config = mdt_reco.configParser(args.config)
    generator = mdt_reco.gen(config)

    sim_events = generator.simEvents(config["Simulator"]["nevents"])
    track_params = generator.findTrajectories(B=0, sim_events=sim_events)

    events=[]
    for A, C in zip(track_params["A"], track_params["C"], strict=False):
        event = generator.createEvent(A, C)
        events.append(event)

    output_dir = f"../output/{config['General']['run_name']}"
    os.makedirs(output_dir, exist_ok=True)
    with open(f"{output_dir}/sim_events_{config['Simulator']['nevents']}.pkl", "wb") as f:
        pickle.dump(events, f)

    with open(f"{output_dir}/track_params.pkl", "wb") as f:
        pickle.dump(track_params, f)

if __name__ == "__main__":
    main()
