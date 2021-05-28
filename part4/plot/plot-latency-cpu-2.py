import os
import math

import matplotlib.pyplot as plt
import numpy as np

import parse

def plot_latency_cpu(d, errorbar=False):

    fig, axs = plt.subplots(2, 1, tight_layout=True)

    for k, v in d.items():
        avg, err = v

        if k == "2T1C":
            axs_0_1 = axs[0].twinx()
            if errorbar:
               axs[0].errorbar(avg[:, 0], avg[:, 1], xerr=err[:, 0], yerr=err[:, 1], label=k+'-P95',
                   fmt='o-', markersize=3, capsize=3, linewidth=1)
               axs_0_1.errorbar(avg[:, 0], avg[:, 2], xerr=err[:, 0], yerr=err[:, 2], label=k+'-CPU',
                   fmt='D--', markersize=3, capsize=3, linewidth=1)
            else:
               axs[0].plot(avg[:, 0], avg[:, 1], 'b-o', label=k+'-P95', markersize=3, linewidth=1)
               axs_0_1.plot(avg[:, 0], avg[:, 2],'r-o', label=k+'-CPU', markersize=3, linewidth=1)

        else:
            axs_1_1 = axs[1].twinx()
            if errorbar:
                axs[1].errorbar(avg[:, 0], avg[:, 1], xerr=err[:, 0], yerr=err[:, 1], label=k+'-P95',
                                fmt='o-', markersize=3, capsize=3, linewidth=1)
                axs_1_1.errorbar(avg[:, 0], avg[:, 2], xerr=err[:, 0], yerr=err[:, 2], label=k+'-CPU',
                                 fmt='o-', markersize=3, capsize=3, linewidth=1)
            else:
                axs[1].plot(avg[:, 0], avg[:, 1], 'b-o', label=k+'-P95', markersize=3, linewidth=1)
                axs_1_1.plot(avg[:, 0], avg[:, 2],'r-o', label=k+'-CPU', markersize=3, linewidth=1)


    axs[0].set_ylabel('P95 Latency (ms)', fontsize=16, labelpad=0.1)
    axs_0_1.set_ylabel('CPU Usage %', fontsize=16, labelpad=0.1)
   
    axs[1].set_ylabel('P95 Latency (ms)', fontsize=16, labelpad=0.1)
    axs_1_1.set_ylabel('CPU Usage %', fontsize=16, labelpad=0.1)
    
    axs[0].yaxis.label.set_color("blue")
    axs_0_1.yaxis.label.set_color("red")
    axs[1].yaxis.label.set_color("blue")
    axs_1_1.yaxis.label.set_color("red")

    axs[0].set_xlabel('Achieved QPS', fontsize=16, labelpad=0.1)
    axs_0_1.set_xlabel('Achieved QPS', fontsize=16, labelpad=0.1)

    axs[1].set_xlabel('Achieved QPS', fontsize=16, labelpad=0.1)
    axs_1_1.set_xlabel('Achieved QPS', fontsize=16, labelpad=0.1)

    axs[1].set_ylim([0, 2.4])
    axs_1_1.set_ylim([0, 160])
    axs[0].set_ylim([0, 2.4])
    axs_0_1.set_ylim([0, 160]) 
    axs[0].set_xlim([0, 110000])
    axs[1].set_xlim([0, 110000])

    x_ticks = list(range(0, 110000, 20000))
    x_tick_labels = [str(x // 1000) + 'K' for x in x_ticks]

    axs[0].set_xticks(x_ticks)
    axs[0].set_xticklabels(x_tick_labels)
    axs[1].set_xticks(x_ticks)
    axs[1].set_xticklabels(x_tick_labels)


    axs_0_1.set_xticks(x_ticks)
    axs_0_1.set_xticklabels(x_tick_labels)
    axs_1_1.set_xticks(x_ticks)
    axs_1_1.set_xticklabels(x_tick_labels)
    # https://stackoverflow.com/questions/12890752/adjusting-tick-label-size-on-twin-axes
    tick_labels = axs[0].xaxis.get_majorticklabels() + axs[0].yaxis.get_majorticklabels() + \
        axs[1].yaxis.get_majorticklabels()
    for label in tick_labels:
        label.set_fontsize(14)

    axs[0].grid(True)
    axs[1].grid(True)

    plt.show()
def extract_data(log_dir):
    configs = ['2T1C', '2T2C']
    num_repeat = 3

    results = dict()
    for config in configs:
        repeats = list()
        for i in range(1, num_repeat + 1):
            test_name = config + '-' + str(i)
            m_name, u_name = test_name + '.txt', test_name + '.json'
            m_path, u_path = os.path.join(log_dir, m_name), os.path.join(log_dir, u_name)

            m_logs, _, proc_cpu_utils, _ = parse.load_aligned_logs(m_path, u_path)
            qps_latency = np.array(m_logs['metrics'])
            cpu_util = np.array(proc_cpu_utils).reshape(-1, 1)
            repeats.append(np.hstack([qps_latency, cpu_util]))
        values = np.stack(repeats)
        avg = np.mean(values, axis=0)
        err = np.std(values, axis=0) / math.sqrt(num_repeat)
        results[config] = [avg, err]

    return results

def main(log_dir):
    data = extract_data(log_dir)
    plot_latency_cpu(data)

if __name__ == '__main__':
    import sys
    main(sys.argv[1])

