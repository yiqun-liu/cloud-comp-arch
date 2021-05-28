import controller
from controller import Workload

old_completed = list()
def scheduler(memcached, workloads, sys_cpu_util):
    # assume there is no pausing and un-pausing
    running = list(filter(lambda x: x.state == Workload.RUNNING, workloads.values()))
    completed = list(filter(lambda x: x.state == Workload.FINISHED, workloads.values()))
    num_completed = len(completed)

    global old_completed
    if len(running) != 0:
        if num_completed > len(old_completed):
            if num_completed == 1:
                if workloads['fft'].state == Workload.FINISHED:
                    workloads['canneal'].adjust_cores([0, 1, 2, 3])
                else:
                    workloads['fft'].adjust_cores([0, 1, 2, 3])
            old_completed = completed
        return
    old_completed = completed

    # the following is executed only when there is no workload running now
    if num_completed == 0:
        workloads['fft'].start(num_threads=4, core_list=[0, 1, 3])
        workloads['canneal'].start(num_threads=4, core_list=[0, 2, 3])
    elif num_completed == 2:
        workloads['freqmine'].start(num_threads=4, core_list=[0, 1, 2, 3])
    elif num_completed == 3:
        workloads['ferret'].start(num_threads=4, core_list=[0, 1, 2, 3])
    elif num_completed == 4:
        workloads['dedup'].start(num_threads=4, core_list=[0, 1, 2, 3])
    elif num_completed == 5:
        workloads['blackscholes'].start(num_threads=4, core_list=[0, 1, 2, 3])

def main():
    ctrl = controller.Controller(scheduler, log_name='s1', memcached_core_list=[0, 1, 2, 3])
    ctrl.run()

if __name__ == '__main__':
    main()

