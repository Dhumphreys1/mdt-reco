import argparse
import os
import pickle

import mdt_reco


def main():
    parser = argparse.ArgumentParser(description="Muon Event Generator")
    parser.add_argument(
        "--config", "-c", required=True, help="Path to config YAML file"
    )
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "../configs", args.config)
    config = mdt_reco.configParser(config_path)

    generator = mdt_reco.gen(config, seed=args.seed)

    sim_events = generator.simEvents(config["Simulator"]["nevents"])
    track_params = generator.findTrajectories(B=0, sim_events=sim_events)

    events = []
    event_params = []
    for A, C in zip(track_params["A"], track_params["C"], strict=False):
        event = generator.createEvent(A, C)
        if event is not None:
            events.append(event)
            event_params.append({"A": A, "C": C})

    output_dir = f"{script_dir}/../output/{config['General']['run_name']}"
    os.makedirs(output_dir, exist_ok=True)
    with open(
        f"{output_dir}/sim_events_{config['Simulator']['nevents']}.pkl", "wb"
    ) as f:
        pickle.dump(events, f)

    with open(f"{output_dir}/track_params.pkl", "wb") as f:
        pickle.dump(event_params, f)
    print(f"Generated {len(events)} events and saved to {output_dir}")


if __name__ == "__main__":
    main()
