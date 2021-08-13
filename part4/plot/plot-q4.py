import os
import math

import numpy as np
import matplotlib.pyplot as plt

import parse

interval = 5

if interval == 10:
    # file_path = '/home/yliu/courses/cloud-architecture/repo/part4/logs/controller/s6-random.txt'
    file_path = '/home/yliu/courses/cloud-architecture/repo/part4/final_logs/10/s6-1.txt'
    # file_path = '/home/yliu/courses/cloud-architecture/repo/part4/final_logs/10/s6-5.txt'

    title_prefix = '2'
    # s6-random
    # start, end = 1622154458.22365, 1622155579.90861
    # p, up = 1622154499.244009, 1622154565.5628865
    # t_start = [1622154458.223655, 1622154458.6765683, 1622154459.1492782, 1622154744.8130224, 1622155045.2551215, 1622155532.215973]
    # s6-1
    start, end = 1622180943.0587697, 1622182072.0741904
    p, up = 1622180985.3599188, 1622181049.8398297
    t_start = [1622180943.0587697, 1622180943.366142, 1622180943.7641354, 1622181229.3854394, 1622181533.1972718,
               1622182024.7529767]
    # s6-5
    # start, end = 1622190816.1938002, 1622191958.129685
    # p, up = 1622190881.6747277, 1622190943.0118816
    # t_start = [1622190816.1938002, 1622190816.587808, 1622190816.9222333, 1622191098.7443607, 1622191420.3796437, 1622191913.2311587]

else:
    # 6-2
    title_prefix = '1'
    file_path = '/home/yliu/courses/cloud-architecture/repo/part4/final_logs/5/s6-2-5.txt'
    start, end = 1622197507.9009862, 1622198656.2828257
    p, up = 1622197566.2750535, 1622197628.6597073
    t_start = [1622197507.9009862, 1622197508.320962, 1622197508.8286784, 1622197793.924478, 1622198121.8343642, 1622198608.6704123]

    # 6-3
    # title_prefix = '2'
    # file_path = '/home/yliu/courses/cloud-architecture/repo/part4/final_logs/5/s6-3-5.txt'
    # start, end = 1622199547.2514648, 1622200698.327898
    # p, up = 1622199592.0193737, 1622199660.7715335
    # t_start = [1622199547.2514648, 1622199547.689498, 1622199548.2684927, 1622199833.3756027, 1622200160.4111836, 1622200650.875115,]

    # 6-4
#     title_prefix = '3'
#     file_path = '/home/yliu/courses/cloud-architecture/repo/part4/final_logs/5/s6-4-5.txt'
#     start, end = 1622202054.6530163, 1622203209.6028514
#     p, up = 1622202075.662226, 1622202162.8270633
#     t_start = [1622202054.6530163, 1622202055.224507, 1622202055.8169136, 1622202354.2179468, 1622202679.0089254, 1622203162.0847542, 1622203209.6028514,
# ]

def main():
    logs = parse.load_measurement_logs(file_path, repeat=False)
    names = ['fft', 'canneal', 'blackscholes', 'freqmine', 'ferret', 'dedup', 'pause', 'unpause']
    annos = t_start + [p, up]

    times = list()
    qps = list()
    latency = list()
    cores = list()
    for ts, ms in zip(logs['times'], logs['metrics']):
        t = (ts[0] + ts[1]) / 2000
        # print(t)
        if t < start:
            continue
        if t > end:
            break
        times.append(t - start)
        qps.append(ms[0])
        latency.append(ms[-1])
        cores.append(2)

    fig, axs = plt.subplots(2, 1, tight_layout=True)
    axs_ = [axs[0].twinx(), axs[1].twinx()]

    # A
    l1=axs[0].plot(times, latency, 'r-o', label='P95', markersize=3, linewidth=1)
    l2=axs_[0].plot(times, qps, 'b-o', label='QPS', markersize=3, linewidth=1)
    lns = l1+l2
    labs = [l.get_label() for l in lns]
    axs[0].legend(lns, labs, loc=0, fontsize=12)

    # B
    l3=axs[1].plot(times, cores, 'r-o', label='#Cores', markersize=3, linewidth=1)
    l4=axs_[1].plot(times, qps, 'b-o', label='QPS', markersize=3, linewidth=1)
    lns = l3 + l4
    labs = [l.get_label() for l in lns]
    axs[1].legend(lns, labs, loc=0, fontsize=12)

    # annotations
    for ax, ax_ in zip(axs, axs_):
        ls = list()
        for name, anno in zip(names, annos):
            x = anno - start
            if name == 'pause' or name == 'unpause':
                ls.append(ax_.plot([x, x], [0, 10000], '--', label=name, linewidth=3))
            else:
                ls.append(ax_.plot([x, x], [0, 10000], label=name, linewidth=3))
        lns = ls[0]
        for l in ls[1:]:
            lns = lns + l
        labs = [l.get_label() for l in lns]
        ax_.legend(lns, labs, loc="lower right", fontsize=10)

    axs[0].set_ylabel('P95 Latency (ms)', fontsize=16, labelpad=0.1)
    axs_[0].set_ylabel('QPS', fontsize=16, labelpad=0.1)

    axs[1].set_ylabel('Number of Cores', fontsize=16, labelpad=0.1)
    axs_[1].set_ylabel('QPS', fontsize=16, labelpad=0.1)

    axs[0].yaxis.label.set_color("red")
    axs_[0].yaxis.label.set_color("blue")
    axs[1].yaxis.label.set_color("red")
    axs_[1].yaxis.label.set_color("blue")

    axs[0].set_xlabel('Time (s)', fontsize=16, labelpad=0.1)
    # axs_[0].set_xlabel('Achieved QPS', fontsize=16, labelpad=0.1)

    axs[1].set_xlabel('Time (s)', fontsize=16, labelpad=0.1)
    # axs_[1].set_xlabel('Achieved QPS', fontsize=16, labelpad=0.1)

    axs[0].set_title(title_prefix + "A", fontsize=20)
    axs[1].set_title(title_prefix + "B", fontsize=20)

    axs[0].set_ylim([0, 2.4])
    axs_[0].set_ylim([0, 110000])
    axs[1].set_ylim([0, 4])
    axs_[1].set_ylim([0, 110000])

    y_ticks = list(range(0, 110000, 20000))
    y_tick_labels = [str(y // 1000) + 'K' for y in y_ticks]

    axs_[0].set_yticks(y_ticks)
    axs_[0].set_yticklabels(y_tick_labels, fontsize=12)
    axs_[1].set_yticks(y_ticks)
    axs_[1].set_yticklabels(y_tick_labels, fontsize=12)

    axs[0].set_xlim([-50, 1300])
    axs[1].set_xlim([-50, 1300])
    x_ticks = [0, 200, 400, 600, 800, 1000, 1200]
    axs[0].set_xticks(x_ticks)
    axs[1].set_xticks(x_ticks)

    # axs_0_1.set_xticks(x_ticks)
    # axs_0_1.set_xticklabels(x_tick_labels)
    # axs_1_1.set_xticks(x_ticks)
    # axs_1_1.set_xticklabels(x_tick_labels)
    # https://stackoverflow.com/questions/12890752/adjusting-tick-label-size-on-twin-axes
    tick_labels = axs[0].xaxis.get_majorticklabels() + axs[0].yaxis.get_majorticklabels() + \
                  axs[1].xaxis.get_majorticklabels() + axs[1].yaxis.get_majorticklabels()
    for label in tick_labels:
        label.set_fontsize(14)

    axs[0].grid(True)
    axs[1].grid(True)

    plt.show()

if __name__ == '__main__':
    main()

