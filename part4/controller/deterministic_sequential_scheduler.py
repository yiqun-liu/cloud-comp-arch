import controller
from controller import Workload

def scheduler(memcached, workloads, sys_cpu_util):
    # assume there is no pausing and un-pausing
    running = list(filter(lambda x: x.state == Workload.RUNNING, workloads.values()))
    if len(running) != 0:
        return

    completed = list(filter(lambda x: x.state == Workload.FINISHED, workloads.values()))
    num_completed = len(completed)

    if num_completed == 0:
        workloads['fft'].start(num_threads=2, core_list=[2, 3])
    elif num_completed == 1:
        workloads['freqmine'].start(num_threads=2, core_list=[2, 3])
    elif num_completed == 2:
        workloads['ferret'].start(num_threads=2, core_list=[2, 3])
    elif num_completed == 3:
        workloads['canneal'].start(num_threads=2, core_list=[2, 3])
    elif num_completed == 4:
        workloads['dedup'].start(num_threads=2, core_list=[2, 3])
    elif num_completed == 5:
        workloads['blackscholes'].start(num_threads=2, core_list=[2, 3])

def main():
    ctrl = controller.Controller(scheduler, log_name='deterministic_sequential', memcached_core_list=[0, 1])
    ctrl.run()

if __name__ == '__main__':
    main()
