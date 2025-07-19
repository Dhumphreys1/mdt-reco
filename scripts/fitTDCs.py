import argparse
import os
import pickle

import numpy as np

import mdt_reco

# import matplotlib.pyplot as plt
# import mplhep as hep
# from scipy.optimize import curve_fit
# plt.style.use([hep.style.ROOT, hep.style.firamath])


def gaussian(x, A, mu, sigma):
    return A * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


# NEEDS TO BE REFACTORED
def main():  # noqa: PLR0915
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=str, required=True, help="Path to the configuration file"
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "../configs", args.config)
    config = mdt_reco.configParser(config_path)
    max_iter = config["TDCFitting"]["max_iterations"]

    tdcFitter = mdt_reco.tdcFitter()
    input_file = f"{script_dir}/../output/{config['General']['run_name']}/{config['General']['input_file']}.pkl"
    with open(input_file, "rb") as f:
        events = pickle.load(f)

    tdc_ids, tdc_times, adc_times, tdc_channels = tdcFitter.getTDCInfo(events)
    del events  # Free memory
    active_tdcs = np.unique(tdc_ids)

    adc_max = config["TDCFitting"]["adc_max"]
    adc_min = config["TDCFitting"]["adc_min"]
    adc_bins = config["TDCFitting"]["adc_bins"]
    adc_range = np.linspace(adc_min, adc_max, adc_bins + 1)
    tdc_max = config["TDCFitting"]["tdc_max"]
    tdc_min = config["TDCFitting"]["tdc_min"]
    tdc_bins = config["TDCFitting"]["tdc_bins"]
    tdc_range = np.linspace(tdc_min, tdc_max, tdc_bins + 1)
    active_tdcs = np.unique(tdc_ids)

    tdc_history = {}
    tdc_histos = {}
    adc_histos = {}
    for tdc_id in active_tdcs:
        tdc_history[tdc_id] = {}
        tdc_histos[tdc_id] = {}
        adc_histos[tdc_id] = {}

        tdc_history[tdc_id]["All_Channels"] = {"t0": 0, "tmax": 0}
        tdc_histos[tdc_id]["All_Channels"] = tdcFitter.getHisto(
            tdc_id, tdc_ids, tdc_times, tdc_range
        )
        adc_histos[tdc_id]["All_Channels"] = tdcFitter.getHisto(
            tdc_id, tdc_ids, adc_times, adc_range
        )
        active_channels = np.unique(tdc_channels[tdc_ids == tdc_id])

        for channel in active_channels:
            tdc_history[tdc_id][channel] = {"t0": 0, "tmax": 0}
            tdc_histos[tdc_id][channel] = tdcFitter.getHisto(
                tdc_id, tdc_ids, tdc_times, tdc_range, channel, tdc_channels
            )
            adc_histos[tdc_id][channel] = tdcFitter.getHisto(
                tdc_id, tdc_ids, adc_times, adc_range, channel, tdc_channels
            )

    # PLOT HISTOS HERE

    # CALCUATE TDC CALIBRATION
    for i in range(max_iter):
        tdc_histos = {}
        tdc_range = np.linspace(tdc_min, tdc_max, 51 + int(50 * i / max_iter))
        for tdc_id in active_tdcs:
            tdc_histos[tdc_id] = {}
            tdc_histos[tdc_id]["All_Channels"] = tdcFitter.getHisto(
                tdc_id, tdc_ids, tdc_times, tdc_range
            )

            bin_centers = tdc_histos[tdc_id]["All_Channels"][1]
            counts = tdc_histos[tdc_id]["All_Channels"][0]
            t0 = tdcFitter.fitT0(counts, bin_centers, n_steps=1000)
            tmax = tdcFitter.fitTMax(counts, bin_centers, n_steps=1000)

            tdc_history[tdc_id]["All_Channels"]["t0"] += t0
            tdc_history[tdc_id]["All_Channels"]["tmax"] += tmax

            active_channels = np.unique(tdc_channels[tdc_ids == tdc_id])
            for channel in active_channels:
                tdc_histos[tdc_id][channel] = tdcFitter.getHisto(
                    tdc_id, tdc_ids, tdc_times, tdc_range, channel, tdc_channels
                )
                bin_centers = tdc_histos[tdc_id][channel][1]
                counts = tdc_histos[tdc_id][channel][0]

                t0 = tdcFitter.fitT0(counts, bin_centers, n_steps=1000)
                tmax = tdcFitter.fitTMax(counts, bin_centers, n_steps=1000)

                tdc_history[tdc_id][channel]["t0"] += t0
                tdc_history[tdc_id][channel]["tmax"] += tmax

    for _tdc_id, channels in tdc_history.items():
        for _channel, values in channels.items():
            values["t0"] /= max_iter
            values["tmax"] /= max_iter

    output_dir = f"{script_dir}/../output/{config['General']['run_name']}"
    os.makedirs(output_dir, exist_ok=True)
    np.save(f"{output_dir}/tdc_calibration.npy", tdc_history)


if __name__ == "__main__":
    main()
# NYI

# for tdc_id in range(active_tdcs):
#     for key in tdc_histos[tdc_id]:
#         bin_centers = tdc_histos[tdc_id][key][1]
#         bin_counts = tdc_histos[tdc_id][key][0]
#         bin_width = bin_centers[1] - bin_centers[0]
#         bin_widths = bin_width*np.ones_like(bin_centers)
#         bin_edges = np.concatenate(([bin_centers[0] - bin_width/2], bin_centers + bin_width/2))
#         #plt.bar(bin_centers, bin_counts, bin_widths)
#         fig, ax = plt.subplots(figsize=(8,8))
#         if key == "All Channels":
#             label = f"TDC Times, TDC {tdc_id}"
#         else:
#             label = f"TDC Times, TDC {tdc_id} Channel {key}"
#         hep.histplot(bin_counts, bin_edges, ax = ax, yerr = np.sqrt(bin_counts))
#         ax.set_title(label)
#         ax.set_xlabel("Time [ns]")
#         ax.set_ylabel("Hits")
#         try:

#         except Exception as e:
#             print(f"Fit failed: {e}")
#         ax.legend()
#         ax.set_xlim(0, 400)


# adc_results = {}
# for tdc_id in range(active_tdcs):
#     adc_results[tdc_id] = {}
#     for key in adc_histos[tdc_id]:
#         bin_centers = adc_histos[tdc_id][key][1]
#         bin_counts = adc_histos[tdc_id][key][0]
#         bin_width = bin_centers[1] - bin_centers[0]
#         bin_widths = bin_width*np.ones_like(bin_centers)
#         bin_edges = np.concatenate(([bin_centers[0] - bin_width/2], bin_centers + bin_width/2))
#         #plt.bar(bin_centers, bin_counts, bin_widths)
#         fig, ax = plt.subplots(figsize=(8,8))
#         if key == "All Channels":
#             label = f"ADC Times, TDC {tdc_id}"
#         else:
#             label = f"ADC Times, TDC {tdc_id} Channel {key}"
#         hep.histplot(bin_counts, bin_edges, ax = ax, yerr = np.sqrt(bin_counts))
#         ax.set_title(label)
#         ax.set_xlabel("Time [ns]")
#         ax.set_ylabel("Hits")
#         p0 = [bin_counts.max(), bin_centers[np.argmax(bin_counts)], bin_width*5]
#         try:
#             popt, _ = curve_fit(gaussian, bin_centers, bin_counts, p0=p0)
#             time_space = np.linspace(bin_edges.min(), bin_edges.max(), 1000)
#             label =  f"$\mu$ = {popt[1]:.2f} \n$\sigma$ = {popt[2]:.2f}"
#             ax.plot(time_space, gaussian(time_space, *popt), color='red', label=label)
#         except Exception as e:
#             print(f"Fit failed: {e}")
#         ax.legend()
#         ax.set_xlim(0, 400)
#         adc_results[tdc_id][key] = {
#                                     "mean": popt[1],
#                                     "std": popt[2]
#                                     }
#         #plt.savefig()
