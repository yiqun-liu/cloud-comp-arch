import controller
from controller import Workload

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
            workloads['blackscholes'].adjust_cores([0, 1, 2, 3])
            workloads['canneal'].adjust_cores([0, 1, 2, 3])
            # will be changed when canneal leave serial stage
        elif name == 'blackscholes':
            # TODO try this
            workloads['canneal'].adjust_cores([0, 1, 2, 3])
            # workloads['freqmine'].start(num_threads=4, core_list=[2, 3])
        else:
            pending[0].start(num_threads=4, core_list=[0, 1, 2, 3])

    def initialize():
        workloads['fft'].start(num_threads=4, core_list=[0, 3])
        workloads['canneal'].start(num_threads=2, core_list=[0, 2])
        workloads['blackscholes'].start(num_threads=2, core_list=[0, 1])

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
        cpu_util = workloads['canneal'].cpu_util[3]
        if workloads['canneal'].state == Workload.RUNNING and cpu_util is not None and cpu_util > 1:
            serials.remove('canneal')
            # TODO switch?
            workloads['canneal'].adjust_cores([2, 3])
            # same as part3
            workloads['blackscholes'].adjust_cores([0, 1])
    if 'fft' in serials:
        cpu_util = workloads['fft'].cpu_util[3]
        if workloads['fft'].state == Workload.RUNNING and cpu_util is not None and cpu_util > 1:
            if workloads['canneal'].state == Workload.RUNNING:
                workloads['canneal'].adjust_cores([])
            if workloads['blackscholes'].state == Workload.RUNNING:
                workloads['blackscholes'].adjust_cores([])
            # preempt execution right because fft takes lots of memory: better executed than paused
            workloads['fft'].adjust_cores([0, 1, 2, 3])
            serials.remove('fft')

def main():
    ctrl = controller.Controller(scheduler, log_name='s5-2', memcached_core_list=[0, 1])
    ctrl.run()

if __name__ == '__main__':
    main()

