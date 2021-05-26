import controller
from controller import Workload

workload_name, num_threads, workload_core_list = None, None, None
issued = False

def scheduler(memcached, workloads, sys_cpu_util):
    global issued
    if not issued:
        workloads[workload_name].start(num_threads=num_threads, core_list=workload_core_list)
        issued = True

def main():
    # set your test param here
    global workload_name, num_threads, workload_core_list
    workload_name = 'fft'
    num_threads = 4
    workload_core_list = [1, 2, 3]
    memcached_core_list = [0]

    w_core_str = ','.join([str(c) for c in workload_core_list])
    m_core_str = ','.join([str(c) for c in memcached_core_list])
    log_name = '-'.join([workload_name, str(num_threads), w_core_str, m_core_str])

    ctrl = controller.Controller(
        scheduler, log_name=log_name, memcached_core_list=memcached_core_list, single_task=True
    )
    ctrl.run()

if __name__ == '__main__':
    main()

