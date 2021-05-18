import os
import sys
import datetime
import json

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

def load_pods_data(file_path):
    time_format = '%Y-%m-%dT%H:%M:%SZ'
    with open(sys.argv[1], 'r') as f:
        logs = json.load(f)

    names, nodes, start_times, durations = list(), list(), list(), list()
    max_completion_time = dict()
    for item in logs['items']:
        name = str(item['status']['containerStatuses'][0]['name'])
        if name == 'memcached':
            continue
        name = name[6:]

        node = item['spec']['nodeSelector']['cca-project-nodetype']
        start_time = datetime.datetime.strptime(
                item['status']['containerStatuses'][0]['state']['terminated']['startedAt'],
                time_format).timestamp()
        completion_time = datetime.datetime.strptime(
                item['status']['containerStatuses'][0]['state']['terminated']['finishedAt'],
                time_format).timestamp()
        names.append(name)
        nodes.append(node)
        start_times.append(start_time)
        durations.append(completion_time - start_time)
        if node in max_completion_time:
            max_completion_time[node] = max(completion_time, max_completion_time[node])
        else:
            max_completion_time[node] = completion_time

    # normalize time
    base = min(start_times)
    start_times = [t - base for t in start_times]
    for k, v in max_completion_time.items():
        print('{}: {}s.'.format(k, v - base))

    return names, nodes, start_times, durations

def plot_time(names, start_times, durations, title=None, nodes=None):
    fig, ax = plt.subplots(tight_layout=True)

    if nodes is None:
        index = list(range(len(names)))
    else:
        unique_nodes = sorted(set(nodes))
        index = [unique_nodes.index(node) for node in nodes]

    for i, name, start, duration in zip(index, names, start_times, durations):
        ax.bar(i, duration, 0.5, bottom=start, alpha=0.7, label=name)

    ax.set_xticks(index)

    if nodes is None:
        ax.set_xticklabels(names)
        ax.set_xlabel('workload')
    else:
        ax.set_xticklabels(nodes)
        ax.set_xlabel('node')
        ax.legend()

    ax.set_ylim([0, 450])
    ax.set_ylabel('time (s)')

    if title is not None:
        plt.title(title)

    plt.show()

# example: python plot-time.py ../logs/s1-local.txt
# example: python plot-time.py ../logs/pods/s3-pods.json
def main():
    path = sys.argv[1]
    title = os.path.basename(path).split('-')[0]
    if path.endswith('txt'):
        names, start_times, durations = load_data(path)
        plot_time(names, start_times, durations, title=title)
    else:
        names, nodes, start_times, durations = load_pods_data(path)
        plot_time(names, start_times, durations, title=title, nodes=nodes)

if __name__ == '__main__':
    main()

