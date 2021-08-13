import test_controller as controller
from test_controller import Workload

serials = ['fft', 'canneal']
done = list()
initialized = False

def scheduler(memcached, workloads, sys_cpu_util):
    # assume there is no pausing and un-pausing
    global done, initialized, serials
    completed = list(filter(lambda x: x.state == Workload.FINISHED, workloads.values()))
    pending = list(filter(lambda x: x.state == Workload.PENDING, workloads.values()))

    def on_end(name):
        if name == 'fft':
            # now canneal is still in serial mode
            # un-pause
            workloads['blackscholes'].adjust_cores([2, 3])
            workloads['canneal'].adjust_cores([0, 1])
            # will be changed when canneal leave serial stage
        elif name == 'canneal':
            # grant it ownership of all cores
            workloads['freqmine'].adjust_cores([0, 1, 2, 3])
        elif name == 'blackscholes':
            # inherit the core left by blackscholes
            workloads['freqmine'].start(num_threads=4, core_list=[2, 3])
        else:
            pending[0].start(num_threads=4, core_list=[0, 1, 2, 3])

    def initialize():
        # we expect it runs only on core3 in its serial stage, other cores are also assigned so that we can know quickly
        # if it starts running in parallel mode
        # TODO monitor when number of threads change; s5 simple
        workloads['fft'].start(num_threads=4, core_list=[1, 3])
        # run its serial stage in core 2
        workloads['canneal'].start(num_threads=2, core_list=[2])
        # co-locate with memcached...
        # at first, memcached may use less than 1T, we allow the 2C blackscholes to steal the slack -> 0, 1
        # in s5, we observe some P95 SLO violations -> add core 2, 3, in hope that pressure can be balanced
        workloads['blackscholes'].start(num_threads=2, core_list=[0, 1, 2, 3])

    if not initialized:
        initialize()
        initialized = True

    for workload in completed:
        if workload.name in done:
            continue
        on_end(workload.name)
        done.append(workload.name)

    # serial workload
    if 'canneal' in serials:
        #cpu_util = workloads['canneal'].cpu_util[3]
        cpu_util = workloads['canneal'].cpu_util
        if workloads['canneal'].state == Workload.RUNNING and cpu_util is not None and cpu_util > 1:
            workloads['canneal'].adjust_cores([0, 1, 2])
            workloads['blackscholes'].adjust_cores([2, 3])
            serials.remove('canneal')
    if 'fft' in serials:
        #cpu_util = workloads['fft'].cpu_util[3]
        cpu_util = workloads['fft'].cpu_util
        if workloads['fft'].state == Workload.RUNNING and cpu_util is not None and cpu_util > 1:
            if workloads['canneal'].state == Workload.RUNNING:
                workloads['canneal'].adjust_cores([])
            if workloads['blackscholes'].state == Workload.RUNNING:
                workloads['blackscholes'].adjust_cores([])
            # preempt execution right because fft takes lots of memory: better executed than paused
            workloads['fft'].adjust_cores([0, 1, 2, 3])
            serials.remove('fft')

def main():
    ctrl = controller.Controller(scheduler, log_name='s6', memcached_core_list=[0, 1])
    ctrl.run()

if __name__ == '__main__':
    main()

