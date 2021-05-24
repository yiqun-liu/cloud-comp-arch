import os
import sys
import time
import json

# sampling interval, in second
INTERVAL = 1

# see Linux manual for "proc(5)"
def get_utilization(pid):
    with open('/proc/stat', 'r') as f:
        stats = f.readline().strip().split()
    stats = [int(v) for v in stats[1:]]
    idle_time, total_time = stats[3], sum(stats)
    with open('/proc/{}/stat'.format(pid), 'r') as f:
        stats = f.readline().split()
    proc_user_tick, proc_sys_tick, proc_rss_pages = int(stats[13]), int(stats[14]), int(stats[23])
    sample = [
        idle_time,
        total_time,
        proc_user_tick,
        proc_sys_tick,
        proc_rss_pages,
        time.time()
    ]
    return sample

def main(num_secs):
    stream = os.popen('pgrep memcached')
    pid = stream.read().strip()

    cur_time = time.time()
    cur_sec = cur_time - cur_time // 60 * 60
    sec_to_wait = 60 - cur_sec
    print('Starting at next whole minute, after {} secs.'.format(sec_to_wait))
    next_time = cur_time + sec_to_wait
    time.sleep(sec_to_wait)

    samples = list()
    num_samples = num_secs // INTERVAL + 2
    for i in range(num_samples):
        sample = get_utilization(pid)
        cur_time = sample[-1]
        samples.append(sample)

        # we do not sleep for INTERVAL secs every time to avoid error accumulation
        next_time += INTERVAL
        time.sleep(next_time - cur_time)

    # output Linux parameter and samples
    records = {
        'page_size': os.sysconf('SC_PAGE_SIZE'),
        'ticks_per_sec': os.sysconf['SC_CLK_TCK'],
        'samples': samples
    }
    # write to file
    file_name = time.strftime('%m%d-%H%M.json')
    with open(file_name, 'w') as f:
        json.dump(records, f)
    print('\nRecords have been written to {}.'.format(file_name))

# one positional argument: number of seconds to record
# example: python3 resource_monitor.py 180
if __name__ == '__main__':
    main(int(sys.argv[1]))

