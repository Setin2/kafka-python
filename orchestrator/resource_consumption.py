import os
import re
import time
import psutil
import subprocess as sp

def get_cpu_usage(pid):
    """
        Returns:
            float: current CPU usage percent
    """
    return psutil.cpu_percent()

# RAM 
def get_memory_usage(mem_total=None):
    """
        Returns:
            float: current RAM usage percent
    """
    mem_stats = psutil.virtual_memory()()
    if not mem_total: mem_total = mem_stats.total
    mem_used = mem_stats.used
    mem_percent = mem_stats.percent
    return mem_percent

def get_disk_usage(disk_total=None):
    """
        Returns:
            float: current DISK usage percent
    """
    disk_stats = psutil.disk_usage('/')
    if not disk_total: disk_total = disk_stats.total
    disk_used = disk_stats.used
    disk_percent = disk_stats.percent
    return disk_percent

def get_gpu_usage(total_memory=None):
    """
        Returns:
            float: current DISK usage percent
    """
    output_to_list = lambda x: x.decode('ascii').split('\n')[:-1]
    if not total_memory:
        COMMAND = "nvidia-smi --query-gpu=memory.used,memory.total --format=csv"
        try:
            memory_use_info = output_to_list(sp.check_output(COMMAND.split(),stderr=sp.STDOUT))[1:]
        except sp.CalledProcessError as e:
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        used_memory, total_memory = re.findall(r"\d+", memory_use_info[0])
        gpu_usage = float(used_memory) / float(total_memory) * 100
    else: 
        COMMAND = "nvidia-smi --query-gpu=memory.used --format=csv"
        try:
            memory_use_info = output_to_list(sp.check_output(COMMAND.split(),stderr=sp.STDOUT))[1:]
        except sp.CalledProcessError as e:
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        used_memory, total_memory = re.findall(r"\d+", memory_use_info[0])
        gpu_usage = float(used_memory) / float(total_memory) * 100
    return used_memory, gpu_usage