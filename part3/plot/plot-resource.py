import os
import sys
import json
import matplotlib.pyplot as plt

# load the all json log in specified directory whose name starts with common prefix
# the prefix should always be the name of the schedule, e.g. 's1'
def load_logs(dir_path, prefix):
    logs = dict()

    file_names = os.listdir(dir_path)
    for name in file_names:
        if not name.startswith(prefix) or not name.endswith('.json'):
            continue
        file_path = os.path.join(dir_path, name)
        with open(file_path, 'r') as f:
            l = json.load(f)
        # combine the log together (here we assume they have sync clocks)
        logs.update(l)

    return logs

def extract_data(logs):
    # if the clock is not heavily skewed, the min_timestamp should be the first of memcached
    min_timestamp = min([v[0]['timestamp'] for v in logs.values()])

    timestamp, cpu_util, mem_util = dict(), dict(), dict()
    mega = 1024 * 1024
    for workload, samples in logs.items():
        timestamp[workload] = [sample['timestamp'] - min_timestamp for sample in samples]
        cpu_util[workload] = [sample['cpu_percent'] for sample in samples]
        mem_util[workload] = [sample['rss'] / mega for sample in samples]

    return timestamp, cpu_util, mem_util

def plot(timestamp, cpu_util, mem_util, title=None):
    fig, axs = plt.subplots(2, 1, tight_layout=True)

    for workload in timestamp.keys():
        axs[0].plot(timestamp[workload], cpu_util[workload], label=workload)
        axs[1].plot(timestamp[workload], mem_util[workload], label=workload)

    axs[0].set_xlabel('time(s)')
    axs[0].set_ylabel('cpu_util')
    axs[0].legend()

    axs[1].set_xlabel('time(s)')
    axs[1].set_ylabel('mem_util (MB)')
    axs[1].legend()

    if title is not None:
        plt.suptitle(title)

    plt.show()

# Usage: python plot-resource.py ../logs s1
def main():
    logs = load_logs(sys.argv[1], sys.argv[2])
    timestamp, cpu_util, mem_util = extract_data(logs)
    plot(timestamp, cpu_util, mem_util, sys.argv[2])

if __name__ == '__main__':
    main()

