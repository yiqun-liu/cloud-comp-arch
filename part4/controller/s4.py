import controller
from controller import Workload

serials = ['fft', 'canneal']
done = list()
main_workload = None

def scheduler(memcached, workloads, sys_cpu_util):
    # assume there is no pausing and un-pausing
    global done, main_workload, serials
    completed = list(filter(lambda x: x.state == Workload.FINISHED, workloads.values()))
    running = list(filter(lambda x: x.state == Workload.RUNNING, workloads.values()))
    paused = list(filter(lambda x: x.state == Workload.PAUSED, workloads.values()))
    pending = list(filter(lambda x: x.state == Workload.PENDING, workloads.values()))

    for workload in completed:
        if workload.name in done:
            continue
        if workload.name == main_workload:
            main_workload = None
        done.append(workload.name)

    if main_workload is None:
        if len(completed) == 0:
            workloads['fft'].start(num_threads=4, core_list=[0, 1])
            workloads['canneal'].start(num_threads=4, core_list=[0, 2])
            workloads['blackscholes'].start(num_threads=2, core_list=[0, 3])
            main_workload = 'blackscholes'
        else:
            # try to make a running workload the main workload
            for w in running:
                if w.name not in serials:
                    main_workload = w.name
                    w.adjust_cores([0, 1, 2, 3])
            if main_workload is None and len(paused) > 0:
                for w in paused:
                    w.adjust_cores([0, 1, 2, 3])
                    if w.name not in serials:
                        main_workload = w.name
            if main_workload is None and len(pending) > 0:
                pending[0].start(num_threads=4, core_list=[0, 1, 2, 3])
                main_workload = pending[0].name

    # serial workload
    if 'canneal' in serials:
        cpu_util = workloads['canneal'].cpu_util[3]
        if workloads['canneal'].state == Workload.RUNNING and cpu_util is not None and cpu_util > 1:
            serials.remove('canneal')
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
            main_workload = 'fft'

def main():
    ctrl = controller.Controller(scheduler, log_name='s4', memcached_core_list=[0, 1, 2, 3])
    ctrl.run()

if __name__ == '__main__':
    main()

