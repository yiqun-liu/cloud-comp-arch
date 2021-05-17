import os
import sys

import matplotlib.pyplot as plt

def str_to_sec(s):
    if 'm' in s:
        m_index = s.index('m')
        return 60 * int(s[: m_index]) + int(s[m_index + 1: -1])
    else:
        return int(s[:-1])

def load_data(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # skip the table head
    names, durations, ages = list(), list(), list()
    for line in lines[1:]:
        values = line.split()
        names.append(values[0][7:])
        durations.append(str_to_sec(values[2]))
        ages.append(str_to_sec(values[3]))

    curr_time = max(ages)
    start_times = [curr_time - age for age in ages]

    return names, start_times, durations

def plot_time(names, start_times, durations):
    fig, ax = plt.subplots(tight_layout=True)

    index = list(range(len(names)))
    for i, start, duration in zip(index, start_times, durations):
        ax.bar(i, duration, 0.5, bottom=start)

    ax.set_xticks(index)
    ax.set_xticklabels(names)

    plt.show()

# example: python plot-time.py ../logs/s1-local.txt
def main():
    names, start_times, end_times = load_data(sys.argv[1])
    plot_time(names, start_times, end_times)

if __name__ == '__main__':
    main()

