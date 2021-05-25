import os
import sys
import time
import subprocess
import logging
import json
from collections import deque

import docker

client = docker.from_env()

# used for monitoring
KERNEL_TICK_SEC = 1. / os.sysconf('SC_CLK_TCK')

# general process which runs on the machine and need utilization monitoring
# (memcached + batch workload)
class Job:
    def __init__(self, name):
        # visible to scheduler
        # strings
        self.name = name
        # list of ints
        self.core_list = None
        # 1s, 3s, 5s, 10s CPU utilization of the process, tuples of floats
        self.cpu_util = (None, None, None, None)

        # exposed to Workload subclass
        self.pid = None

        # absolute private
        self.__container = None
        self.__samples = deque([None] * 11)

    # update utilization info
    def sample_util(self):
        if self.pid is None:
            success = self.__fetch_pid()
            if not success:
                return

        # process utilization information
        try:
            with open('/proc/{}/stat'.format(self.pid), 'r') as f:
                stats = f.readline().split()
            user_tick, sys_tick = int(stats[13]), int(stats[14])
            sample = ((user_tick + sys_tick) * KERNEL_TICK_SEC, time.time())

            # for debugging
            global debug_counter
            if debug_counter == 10:
                debug_counter = 0
                debug_records[self.name].append(sample)
        except FileNotFoundError:
            # the process have terminated
            sample = None

        self.__samples.pop()
        self.__samples.appendleft(sample)
        self.cpu_util = calc_cpu_util(self.__samples)

    # visible to scheduler (works only for memcached, shadowed for batch workloads)
    def adjust_cores(self, core_list=None):
        assert self.name == 'memcached'
        if self.pid is None:
            success = self.__fetch_pid()
            if not success:
                raise Exception('memcached not running when started.')

        logging.info('Adjusting cores allocated to {}: from {} to {}.'.format(
            self.name, self.core_list, core_list)
        )
        self.core_list = core_list

        # asynchronously taskset (requires sudo privilege)
        core_str = ','.join([str(core) for core in core_list])
        command = 'taskset -a -cp {} {}'.format(core_str, self.pid)
        subprocess.Popen(['/bin/bash', '-c', command])

    def __fetch_pid(self):
        stream = os.popen('pgrep ' + self.name)
        results = stream.read().split()
        if len(results) == 1:
            self.pid = results[0]
            return True
        elif len(results) > 1:
            raise ValueError(self.name + ': more than one running process!')
        else:
            # the process is not yet started
            return False


# batch workload
class Workload(Job):
    # state values
    PENDING = 0
    RUNNING = 1
    PAUSED = 2
    FINISHED = 3

    def __init__(self, name):
        super().__init__(name)

        # visible to scheduler
        # int (should be used as enum)
        self.state = Workload.PENDING
        # int
        self.num_threads = None
        # float timestamp
        self.start_time = None

        # private
        self.__container_id = None
        self.__container = None

    # visible to scheduler
    def start(self, num_threads=1, core_list=None):
        self.num_threads = num_threads
        self.core_list = core_list
        self.state = Workload.RUNNING

        image = configs[self.name]['image']
        command = configs[self.name]['command'].copy()
        command[-1] += (' -n ' + str(num_threads))

        if core_list is not None:
            core_str = ','.join([str(core) for core in core_list])
            container = client.containers.run(image, command, cpuset_cpus=core_str, detach=True)
        else:
            container = client.containers.run(image, command, detach=True)
        self.__container = container
        self.__container_id = container.id

        logging.info('Batch workload {}: starts with {} thread(s), running on core(s) {}.'.format(
            self.name, num_threads, core_list)
        )

    # visible to scheduler
    def adjust_cores(self, core_list=None):
        logging.info('Adjusting cores allocated to {}: from {} to {}.'.format(
            self.name, self.core_list, core_list)
        )
        self.core_list = core_list

        if core_list is None or len(core_list) == 0:
            self.__container.pause()
            self.state = Workload.PAUSED
            logging.info('batch workload {} paused.'.format(self.name))
            return

        if self.state == Workload.PAUSED:
            self.state = Workload.RUNNING
            self.__container.unpause()
            logging.info('batch workload {} un-paused.'.format(self.name))

        core_str = ','.join([str(core) for core in core_list])
        self.__container.update(cpuset_cpus=core_str)

    # should only be called by controller
    def update(self, running_containers):
        if self.state == Workload.PENDING or self.state == Workload.FINISHED:
            return

        self.sample_util()

        # the first condition is a safeguard (in case Docker returns stale data)
        if self.pid is not None and self.__container_id not in running_containers:
            self.state = Workload.FINISHED
            logging.info('batch workload {} finished.'.format(self.name))

# prepare utilization data, and periodically executes 'scheduler' function object
# signature of scheduler: scheduler(memcached, workloads, sys_util)
class Controller:
    def __init__(self, scheduler, log_name=None, memcached_core_list=None):
        self.scheduler = scheduler
        self.memcached = Job('memcached')
        self.workloads = dict()
        self.sys_cpu_util = (None, None, None, None)
        self.samples = deque([None] * 11)

        # initialize logger
        if log_name is None:
            log_name = time.strftime('%m%d-%H%M')
        self.__log_name = log_name
        logging.basicConfig(
            level=logging.INFO,
            format="%(created)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_name + '.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.info('Logs will be written to ' + log_name)

        # set memcached
        if memcached_core_list is not None:
            self.memcached.adjust_cores(memcached_core_list)

        # pull all images before start running
        for name, config in configs.items():
            client.images.pull(config['image'])
            self.workloads[name] = Workload(name)
            logging.info('Image {} pulled.'.format(name))

    # called in main function
    def run(self):
        start_time = time.time()
        logging.info('Controller enters main control loop.')

        global debug_counter
        while True:
            # update controller state
            self.__sample_util()
            running_containers = Controller.__get_running_containers()

            # update memcached state
            self.memcached.sample_util()

            # update workloads state
            num_pending = 0
            for workload in self.workloads.values():
                workload.update(running_containers)
                if workload.state != Workload.FINISHED:
                    num_pending += 1

            # all done
            if num_pending == 0 and time.time() - start_time > 300:
                break

            # call scheduler
            self.scheduler(self.memcached, self.workloads, self.sys_cpu_util)

            # wait
            time.sleep(1)

            debug_counter += 1

        logging.info('All workloads finished. Controller quits.')
        with open(self.__log_name + '.json', 'w') as f:
            json.dump(debug_records, f)

    def __sample_util(self):
        with open('/proc/stat', 'r') as f:
            stats = f.readline().strip().split()
        stats = [int(v) for v in stats[1:]]
        idle_time, total_time = stats[3], sum(stats)
        busy_time = total_time - idle_time

        self.samples.pop()
        self.samples.appendleft((busy_time, total_time))
        self.sys_cpu_util = calc_cpu_util(self.samples)

        global debug_counter
        if debug_counter == 10:
            debug_counter = 0
            debug_records['sys'].append(self.sys_cpu_util)

    @staticmethod
    def __get_running_containers():
        # maybe there are more efficient approach
        containers = client.containers.list()
        return [c.id for c in containers]


def calc_cpu_util(samples):
    u1, u3, u5, u10 = None, None, None, None
    if samples[0] is not None:
        if samples[10] is not None:
            u10 = (samples[0][0] - samples[10][0]) / (samples[0][1] - samples[10][1])
        if samples[ 5] is not None:
            u5  = (samples[0][0] - samples[ 5][0]) / (samples[0][1] - samples[ 5][1])
        if samples[ 3] is not None:
            u3  = (samples[0][0] - samples[ 3][0]) / (samples[0][1] - samples[ 3][1])
        if samples[ 1] is not None:
            u1  = (samples[0][0] - samples[ 1][0]) / (samples[0][1] - samples[ 1][1])
    return (u1, u3, u5, u10)

debug_counter = 0
debug_records = {
    'sys': list(),
    'memcached': list(),
    'fft': list(),
    'freqmine': list(),
    'ferret': list(),
    'canneal': list(),
    'dedup': list(),
    'blackscholes': list()
}

configs = {
    "fft": {
        "image": "anakli/parsec:splash2x-fft-native-reduced",
        "command": ["/bin/sh", "-c", "./bin/parsecmgmt -a run -p splash2x.fft -i native"]
    },
    "freqmine": {
        "image": "anakli/parsec:freqmine-native-reduced",
        "command": ["/bin/sh", "-c", "./bin/parsecmgmt -a run -p freqmine -i native"]
    },
    "ferret": {
        "image": "anakli/parsec:ferret-native-reduced",
        "command": ["/bin/sh", "-c", "./bin/parsecmgmt -a run -p ferret -i native"]
    },
    "canneal": {
        "image": "anakli/parsec:canneal-native-reduced",
        "command": ["/bin/sh", "-c", "./bin/parsecmgmt -a run -p canneal -i native"]
    },
    "dedup": {
        "image": "anakli/parsec:dedup-native-reduced",
        "command": ["/bin/sh", "-c", "./bin/parsecmgmt -a run -p dedup -i native"]
    },
    "blackscholes": {
        "image": "anakli/parsec:blackscholes-native-reduced",
        "command": ["/bin/sh", "-c", "./bin/parsecmgmt -a run -p blackscholes -i native"]
    }
}
