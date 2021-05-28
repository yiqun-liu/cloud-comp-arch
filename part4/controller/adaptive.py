import controller
from controller import Workload

def scheduler(memcached, workloads, sys_cpu_util):
    # assume there is no pausing and un-pausing
    running = list(filter(lambda x: x.state == Workload.RUNNING, workloads.values()))
    if len(running) != 0:
        if memcached.cpu_util[2] is None:
            return
        if memcached.cpu_util[2] > 90:
            for w in running:
                w.adjust_cores([1, 2, 3])
        if memcached.cpu_util[2] < 70:
            for w in running:
                w.adjust_cores([0, 1, 2, 3])
        return

    completed = list(filter(lambda x: x.state == Workload.FINISHED, workloads.values()))
    num_completed = len(completed)

    init_cores = [1, 2, 3]
    if memcached.cpu_util[2] is not None and memcached.cpu_util[2] < 80:
        init_cores = [0, 1, 2, 3]

    if num_completed == 0:
        workloads['fft'].start(num_threads=4, core_list=init_cores)
    elif num_completed == 1:
        workloads['freqmine'].start(num_threads=4, core_list=init_cores)
    elif num_completed == 2:
        workloads['ferret'].start(num_threads=4, core_list=init_cores)
    elif num_completed == 3:
        workloads['canneal'].start(num_threads=4, core_list=init_cores)
    elif num_completed == 4:
        workloads['dedup'].start(num_threads=4, core_list=init_cores)
    elif num_completed == 5:
        workloads['blackscholes'].start(num_threads=4, core_list=init_cores)

def main():
    ctrl = controller.Controller(scheduler, log_name='adaptive', memcached_core_list=[0, 1])
    ctrl.run()

if __name__ == '__main__':
    main()
