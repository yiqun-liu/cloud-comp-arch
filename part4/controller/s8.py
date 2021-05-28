import controller
from controller import Workload

serials = ['fft', 'canneal']
done = list()
initialized = False

monitor_canneal = False
back_to_serial = False

# s7 + early canneal + early freqmine
def scheduler(memcached, workloads, sys_cpu_util):
    # assume there is no pausing and un-pausing
    global done, initialized, serials, monitor_canneal, back_to_serial
    completed = list(filter(lambda x: x.state == Workload.FINISHED, workloads.values()))
    pending = list(filter(lambda x: x.state == Workload.PENDING, workloads.values()))

    def on_end(name):
        global monitor_canneal
        if name == 'fft':
            workloads['blackscholes'].adjust_cores([0, 1, 2])
            workloads['canneal'].adjust_cores([3])
        elif name == 'blackscholes':
            workloads['canneal'].adjust_cores([0, 1, 2, 3])
            monitor_canneal = True
        elif name == 'canneal':
            if workloads['freqmine'].state != Workload.RUNNING:
                workloads['freqmine'].start(num_threads=4, core_list=[0, 1, 2, 3])
            else:
                workloads['freqmine'].adjust_cores([0, 1, 2, 3])
        else:
            pending[0].start(num_threads=4, core_list=[0, 1, 2, 3])

    def initialize():
        # fft takes 3 (allocated more observe when it enters parallel mode
        # canneal takes 2, blackscholes use the rest
        workloads['fft'].start(num_threads=4, core_list=[0, 1, 3])
        workloads['canneal'].start(num_threads=4, core_list=[2])
        workloads['blackscholes'].start(num_threads=3, core_list=[0, 1, 2])

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
            print('canneal out of serial')
            serials.remove('canneal')
    if 'fft' in serials:
        cpu_util = workloads['fft'].cpu_util[3]
        if workloads['fft'].state == Workload.RUNNING and cpu_util is not None and cpu_util > 1:
            workloads['blackscholes'].adjust_cores([])
            workloads['canneal'].adjust_cores([])
            # preempt execution right because fft takes lots of memory: better executed than paused
            workloads['fft'].adjust_cores([0, 1, 2, 3])
            serials.remove('fft')
    if monitor_canneal and not back_to_serial:
        cpu_util = workloads['canneal'].cpu_util[3]
        if cpu_util is not None and cpu_util < 2 and workloads['freqmine'].state != Workload.RUNNING:
            print('canneal back to serial')
            workloads['freqmine'].start(num_threads=4, core_list=[3])

def main():
    ctrl = controller.Controller(scheduler, log_name='s8', memcached_core_list=[0, 1])
    ctrl.run()

if __name__ == '__main__':
    main()

