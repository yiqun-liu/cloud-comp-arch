import controller
from controller import Workload

started = False
last_completed = list()
def scheduler(memcached, workloads, sys_cpu_util):
    global started, last_completed
    if not started:
        # start any workload
        workloads.values()[0].start(num_threads=2, core_list=[2, 3])
        started = True
        return

    completed = list(filter(lambda x: x.state == Workload.FINISHED, workloads.values()))

    # if a workload finished
    if len(completed) > len(last_completed):
        assert len(completed) == len(last_completed) + 1
        pending = list(filter(lambda x: x.state == Workload.PENDING, workloads.values()))
        pending[0].start(num_threads=2, core_list=[2, 3])

    last_completed = completed

def main():
    ctrl = controller.Controller(scheduler, log_name='random_sequential', memcached_core_list=[0, 1])
    ctrl.run()

if __name__ == '__main__':
    main()
