import json

# functions used to parse raw data
def load_measurement_logs(file_path, repeat=False, include_target=False):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # log is a nested list: repetition, qps interval, values (latency & timestamps)
    logs = list()
    for line in lines:
        if line.startswith('#type'):
            logs.append({'times': list(), 'metrics': list()})
        if not line.startswith('read'):
            continue
        values = line.split()
        # start time, end time, actual qps, P95 in ms
        logs[-1]['times'].append([int(values[-2]), int(values[-1])])
        if not include_target:
            logs[-1]['metrics'].append([float(values[-4]), float(values[12]) / 1000.])
        else:
            # actual qps, target qps, P95 in ms
            logs[-1]['metrics'].append([float(values[-4]), float(values[-3]), float(values[12]) / 1000.])

    if repeat:
        return logs
    else:
        result = {'times': list(), 'metrics': list()}
        for record in logs:
            result['times'] += record['times']
            result['metrics'] += record['metrics']
        return result

# align monitor samples with measurement logs and calculate utilization
def calc_utilization(measure_logs, util_logs):
    cpu_utils, proc_cpu_utils, mem_usages = list(), list(), list()

    samples = util_logs['samples']
    # kernel_tick_sec = 1. / util_logs['ticks_per_sec']
    kernel_tick_sec = 0.01
    page_size = util_logs['page_size']
    mb = 1024 * 1024

    j = 0
    for i, ts in enumerate(measure_logs['times']):
        # minimum greater, maximum smaller
        while samples[j][-1] * 1000 < ts[0]:
            j += 1
        left = samples[j]

        while samples[j + 1][-1] * 1000 <= ts[1]:
            j += 1
        right = samples[j]

        # 0: idle time, 1: total time
        cpu_util = 100.0 - float(right[0] - left[0]) / float(right[1] - left[1]) * 100
        # 2: user ticks, 3: sys ticks, 5 / -1: timestamp
        proc_cpu_time = (right[2] + right[3] - left[2] - left[3]) * kernel_tick_sec
        proc_cpu_util = proc_cpu_time / (right[-1] - left[-1]) * 100
        # 4: rss
        mem_usage = right[4] * page_size / mb

        cpu_utils.append(cpu_util)
        proc_cpu_utils.append(proc_cpu_util)
        mem_usages.append(mem_usage)

    return cpu_utils, proc_cpu_utils, mem_usages

def load_aligned_logs(measure_path, utilization_path):
    m_logs = load_measurement_logs(measure_path)
    with open(utilization_path, 'r') as f:
        util_logs = json.load(f)
    return m_logs, *calc_utilization(m_logs, util_logs)

