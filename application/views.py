from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from application.lib.perfdata import *


# Create your views here.
class HomePageView(LoginRequiredMixin, TemplateView):

    def get(self, request, **kwargs):
        user_name = request.user.username

        perf = PerfData()
        datacenters = perf.get_elements()

        graph_memory = perf.get_graph_cumulative('mem.consumed.average', 1, 1, 'Memory Consumed')
        graph_cpu = perf.get_graph_cumulative('cpu.usagemhz.average', 1, 2, 'CPU Usage')
        graph_storage = perf.get_graph_cumulative('disk.used.latest', 1, 0, 'Storage Usage')

        metrics_usage = perf.get_usage_metrics_datacenter()

        perf.disconnect()

        # Doughnut graphs data
        cluster_pie = {'cluster_names': metrics_usage['cluster_names'],
                       'cluster_mem_values': metrics_usage['cluster_mem_values'],
                       'cluster_cpu_values': metrics_usage['cluster_cpu_values'],
                       'cluster_storage_values': metrics_usage['cluster_storage_values'],
                       'cluster_network_values': metrics_usage['cluster_network_values']}

        cluster_pie_json = json.dumps(cluster_pie)

        context = {'title': 'Company Name', 'user_name': user_name, 'interval_m': '1', 'datacenters': datacenters,
                   'metrics_usage': metrics_usage, 'graph_memory': graph_memory, 'graph_cpu': graph_cpu,
                   'graph_storage': graph_storage, 'cluster_pie_json': cluster_pie_json}

        return render(request, 'vmware_dashboard.html', context)


class DashboardGraphsView(LoginRequiredMixin, TemplateView):

    def get(self, request, interval):

        perf = PerfData()

        graph_memory = perf.get_graph_cumulative('mem.consumed.average', interval, 1, 'Memory Consumed')
        graph_cpu = perf.get_graph_cumulative('cpu.usagemhz.average', interval, 2, 'CPU Usage')
        graph_storage = perf.get_graph_cumulative('disk.used.latest', interval, 0, 'Storage Usage')

        perf.disconnect()

        context = {'interval_m': interval, 'graph_memory': graph_memory, 'graph_cpu': graph_cpu,
                   'graph_storage': graph_storage}

        return render(request, 'dashboard_graphs.html', context)

# Ajax functions for Dashboard view

# End Ajax functions for Dashboard view


class ClusterPageView(LoginRequiredMixin, TemplateView):

    def get(self, request, cluster, interval):

        perf = PerfData()

        cluster_name = cluster
        metric_interval = interval
        graph_memory_usage = perf.get_graph(cluster_name, 3, 'mem.consumed.average', metric_interval, 'Memory Consumed (GB)', 3)
        graph_cpu_usage = perf.get_graph(cluster_name, 3, 'cpu.usage.average', metric_interval, 'CPU Usage (%)', 1)
        graph_network_usage, graph_disk_usage = perf.get_graph_cluster_network_disk(cluster_name, 1)

        # Get Current usage of Storage, CPU & Memory
        metrics_usage = perf.get_usage_metrics_cluster(cluster_name)

        perf.disconnect()

        # Memory Real Time graphs data
        memory = {'time': metrics_usage['active_memory_time'],
                  'active_memory': metrics_usage['total_active_memory'],
                  'ballooned_memory': metrics_usage['total_ballooned_memory'],
                  'swapused_memory': metrics_usage['total_swapused_memory']}

        memory_realtime = json.dumps(memory)

        cpu = {'cpu_usage_percent': metrics_usage['total_cpu_usage_percent'],
               'cpu_readiness_percent': metrics_usage['total_cpu_readiness_percent']}

        cpu_realtime = json.dumps(cpu)

        network = {'network_transmitted_rate': metrics_usage['total_network_transmitted_rate'],
                   'network_received_rate': metrics_usage['total_network_received_rate']}

        network_realtime = json.dumps(network)

        disks = {'disks_read_rate': metrics_usage['total_disks_read_rate'],
                 'disks_write_rate': metrics_usage['total_disks_write_rate']}

        disks_realtime = json.dumps(disks)

        context = {'interval_m': metric_interval, 'cluster_name': cluster_name, 'graph_memory': graph_memory_usage,
                   'graph_cpu': graph_cpu_usage, 'graph_network_usage': graph_network_usage,
                   'graph_disk_usage': graph_disk_usage,
                   'metrics_usage': metrics_usage,
                   'memory_realtime': memory_realtime, 'cpu_realtime': cpu_realtime,
                   'network_realtime': network_realtime, 'disks_realtime': disks_realtime}

        return render(request, 'cluster.html', context)


class ClusterGraphsView(LoginRequiredMixin, TemplateView):

    def get(self, request, cluster, interval):

        perf = PerfData()

        cluster_name = cluster
        metric_interval = interval
        graph_memory_usage = perf.get_graph(cluster_name, 3, 'mem.consumed.average', metric_interval, 'Memory Consumed (GB)', 3)
        graph_cpu_usage = perf.get_graph(cluster_name, 3, 'cpu.usage.average', metric_interval, 'CPU Usage (%)', 1)
        graph_network_usage, graph_disk_usage = perf.get_graph_cluster_network_disk(cluster_name, interval)

        perf.disconnect()

        context = {'interval_m': metric_interval, 'cluster_name': cluster_name, 'graph_memory': graph_memory_usage,
                   'graph_cpu': graph_cpu_usage, 'graph_network_usage': graph_network_usage,
                   'graph_disk_usage': graph_disk_usage}

        return render(request, 'cluster_graphs.html', context)


# Ajax functions for Cluster view

@login_required
def get_top_vms_cluster_memory(request, cluster):
    perf = PerfData()
    cluster_name = cluster
    top_vms_mem = perf.get_top_vms_cluster(cluster_name, 'MEMORY')

    return JsonResponse(top_vms_mem)

@login_required
def get_top_vms_cluster_cpu(request, cluster):
    perf = PerfData()
    cluster_name = cluster
    top_vms_cpu = perf.get_top_vms_cluster(cluster_name, 'CPU')

    return JsonResponse(top_vms_cpu)

@login_required
def get_top_hosts_cluster_memory(request, cluster):
    perf = PerfData()
    cluster_name = cluster
    top_hosts_memory = perf.get_top_hosts_cluster(cluster_name, 'MEMORY')

    return JsonResponse(top_hosts_memory)

@login_required
def get_top_hosts_cluster_cpu(request, cluster):
    perf = PerfData()
    cluster_name = cluster
    top_hosts_cpu = perf.get_top_hosts_cluster(cluster_name, 'CPU')

    return JsonResponse(top_hosts_cpu)

# End of Ajax functions for Cluster View


class HostPageView(LoginRequiredMixin, TemplateView):

    def get(self, request, host, interval):

        perf = PerfData()

        host_name = host
        metric_interval = interval
        graph_memory_usage = perf.get_graph(host_name, 2, 'mem.consumed.average', metric_interval, 'Consumed Memory (GB)', 3)
        graph_cpu_usage = perf.get_graph(host_name, 2, 'cpu.usage.average', metric_interval, 'CPU Usage (%)', 1)
        disk_usage = perf.get_graph(host_name, 2, 'disk.usage.average', metric_interval, 'Disk Usage (KBps)', 0)
        network_usage = perf.get_graph(host_name, 2, 'net.usage.average', metric_interval, 'Network Usage (Mbps)', 2)

        # Get Current usage of CPU & Memory
        metrics_usage = perf.get_usage_metrics_host(host_name)

        perf.disconnect()

        # Real Time graphs data
        memory = {'time': metrics_usage['memory_time'],
                  'active_memory': metrics_usage['active_memory'],
                  'ballooned_memory': metrics_usage['ballooned_memory'],
                  'swapused_memory': metrics_usage['swapused_memory']}
        memory_realtime = json.dumps(memory)

        cpu = {'cpu_usage_percent': metrics_usage['cpu_usage_percent'],
               'cpu_readiness_percent': metrics_usage['cpu_readiness_percent']}
        cpu_realtime = json.dumps(cpu)

        network = {'network_transmitted_rate': metrics_usage['network_transmitted_rate'],
                   'network_received_rate': metrics_usage['network_received_rate']}
        network_realtime = json.dumps(network)

        disks = {'disks_read_rate': metrics_usage['disks_read_rate'],
                 'disks_write_rate': metrics_usage['disks_write_rate']}
        disks_realtime = json.dumps(disks)

        context = {'interval_m': metric_interval, 'host_name': host_name, 'graph_memory': graph_memory_usage,
                   'graph_cpu': graph_cpu_usage, 'graph_disk': disk_usage, 'graph_network': network_usage,
                   'metrics_usage': metrics_usage, 'memory_realtime': memory_realtime,
                   'cpu_realtime': cpu_realtime, 'network_realtime': network_realtime,
                   'disks_realtime': disks_realtime}

        return render(request, 'host.html', context)


class HostGraphsView(LoginRequiredMixin, TemplateView):

    def get(self, request, host, interval):

        perf = PerfData()

        host_name = host
        metric_interval = interval
        graph_memory_usage = perf.get_graph(host_name, 2, 'mem.consumed.average', metric_interval, 'Consumed Memory (GB)', 3)
        graph_cpu_usage = perf.get_graph(host_name, 2, 'cpu.usage.average', metric_interval, 'CPU Usage (%)', 1)
        disk_usage = perf.get_graph(host_name, 2, 'disk.usage.average', metric_interval, 'Disk Usage (KBps)', 0)
        network_usage = perf.get_graph(host_name, 2, 'net.usage.average', metric_interval, 'Network Usage (Mbps)', 2)

        perf.disconnect()

        context = {'interval_m': metric_interval, 'host_name': host_name, 'graph_memory': graph_memory_usage,
                   'graph_cpu': graph_cpu_usage, 'graph_disk': disk_usage, 'graph_network': network_usage}

        return render(request, 'host_graphs.html', context)


class VmPageView(LoginRequiredMixin, TemplateView):

    def get(self, request, uuid, interval):

        perf = PerfData()

        instance_uuid = uuid
        metric_interval = interval
        graph_memory_usage = perf.get_graph(instance_uuid, 1, 'mem.consumed.average', metric_interval, 'Memory Consumed (GB)', 3)
        graph_cpu_usage = perf.get_graph(instance_uuid, 1, 'cpu.usage.average', metric_interval, 'CPU Usage (%)', 1)
        disk_usage = perf.get_graph(instance_uuid, 1, 'disk.usage.average', metric_interval, 'Disk Usage (KBps)', 0)
        network_usage = perf.get_graph(instance_uuid, 1, 'net.usage.average', metric_interval, 'Network Usage (KBps)', 0)

        # Get Current usage of CPU, Memory and Storage
        metrics_usage = perf.get_usage_metrics_vm(instance_uuid)

        perf.disconnect()

        # Real Time graphs data
        memory = {'time': metrics_usage['memory_time'],
                  'active_memory': metrics_usage['active_memory'],
                  'ballooned_memory': metrics_usage['ballooned_memory'],
                  'swapused_memory': metrics_usage['swapused_memory']}
        memory_realtime = json.dumps(memory)

        cpu = {'cpu_usage_percent': metrics_usage['cpu_usage_percent'],
               'cpu_readiness_percent': metrics_usage['cpu_readiness_percent']}
        cpu_realtime = json.dumps(cpu)

        network = {'network_transmitted_rate': metrics_usage['network_transmitted_rate'],
                   'network_received_rate': metrics_usage['network_received_rate']}
        network_realtime = json.dumps(network)

        disks = {'disks_read_rate': metrics_usage['disks_read_rate'],
                 'disks_write_rate': metrics_usage['disks_write_rate']}
        disks_realtime = json.dumps(disks)

        context = {'interval_m': metric_interval, 'instance_uuid': instance_uuid, 'graph_memory': graph_memory_usage,
                   'graph_cpu': graph_cpu_usage, 'graph_disk': disk_usage, 'graph_network': network_usage,
                   'metrics_usage': metrics_usage, 'memory_realtime': memory_realtime,
                   'cpu_realtime': cpu_realtime, 'network_realtime': network_realtime,
                   'disks_realtime': disks_realtime}

        return render(request, 'vm.html', context)


class VmGraphsView(LoginRequiredMixin, TemplateView):

    def get(self, request, uuid, interval):

        perf = PerfData()

        instance_uuid = uuid
        metric_interval = interval
        graph_memory_usage = perf.get_graph(instance_uuid, 1, 'mem.consumed.average', metric_interval, 'Memory Consumed (GB)', 3)
        graph_cpu_usage = perf.get_graph(instance_uuid, 1, 'cpu.usage.average', metric_interval, 'CPU Usage (%)', 1)
        disk_usage = perf.get_graph(instance_uuid, 1, 'disk.usage.average', metric_interval, 'Disk Usage (KBps)', 0)
        network_usage = perf.get_graph(instance_uuid, 1, 'net.usage.average', metric_interval, 'Network Usage (KBps)', 0)

        perf.disconnect()

        context = {'interval_m': metric_interval, 'instance_uuid': instance_uuid, 'graph_memory': graph_memory_usage,
                   'graph_cpu': graph_cpu_usage, 'graph_disk': disk_usage, 'graph_network': network_usage}

        return render(request, 'vm_graphs.html', context)