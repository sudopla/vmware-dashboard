#plotly libraries
import plotly
from plotly.graph_objs import Scatter, Layout
import plotly.graph_objs as go


# vCenter libraries
from pyVim import connect
from pyVim.connect import SmartConnect, Disconnect
import datetime
from pyVmomi import vim
from datetime import timedelta, datetime
import ssl

#s = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
#s.verify_mode = ssl.CERT_NONE
s = ssl._create_unverified_context()

class PerfData:

    def __init__(self):
        self.c = SmartConnect(host="", user="", pwd="", sslContext=s)

        self.content = self.c.RetrieveContent()

        # Get all the performance counters
        self.perf_dict = {}
        self.perfList = self.content.perfManager.perfCounter
        for counter in self.perfList:
            counter_full = "{}.{}.{}".format(counter.groupInfo.key, counter.nameInfo.key, counter.rollupType)
            self.perf_dict[counter_full] = counter.key

    # Get metric values
    def BuildQuery(self, content, CounterId, interval, instance, entity, startTime, endTime):
        perfManager = content.perfManager
        metricId = vim.PerformanceManager.MetricId(counterId=CounterId, instance=instance)

        query = vim.PerformanceManager.QuerySpec(intervalId=interval,
                                                 entity=entity,
                                                 metricId=[metricId],
                                                 startTime=startTime,
                                                 endTime=endTime)

        perfResults = perfManager.QueryPerf(querySpec=[query])

        return perfResults

    # Get real-time metric values
    def BuildQuery_RealTime(self, content, CounterId, interval, instance, entity):
        perfManager = content.perfManager
        metricId = vim.PerformanceManager.MetricId(counterId=CounterId, instance=instance)

        query = vim.PerformanceManager.QuerySpec(intervalId=interval,
                                                 entity=entity,
                                                 metricId=[metricId])

        perfResults = perfManager.QueryPerf(querySpec=[query])

        return perfResults

    def StatCheck(self, perf_dict, counter_name):
        counter_key = perf_dict[counter_name]
        return counter_key

    # Function to get metric values when there is only one instance in perfResults
    def get_values(self, perfResults):
        values = perfResults[0].value[0].value
        times = []
        for val in perfResults[0].sampleInfo:
            times.append(val.timestamp)

        return times, values

    # Function to get instances (LUNs) and their metric values
    def get_instance_values(self, perfResults):
        lun_instances = {}
        values = perfResults[0].value
        for val_instances in values:
                lun_instances[val_instances.id.instance] = val_instances.value

        times = []
        for val in perfResults[0].sampleInfo:
                times.append(val.timestamp)

        return times, lun_instances

    # Function to get instances (LUNs) and their metric values
    def get_network_values(self, perfResults):
        network_usage_values = []
        values = perfResults[0].value
        for val_instances in values:
            if val_instances.id.instance == '':
                        network_usage_values = val_instances.value

        times = []
        for val in perfResults[0].sampleInfo:
                times.append(val.timestamp)

        return times, network_usage_values

    def get_metric(self, identifier, element, metric, interval, get_max=False):
        # identifier - it's the name of the object to get the metric from. There is a specific case where identifier is the object itself
        # element - a number to define if it's a host, vm, cluster
        # metric - the metric to get the information from
        # interval - interval where to get the metric from

        identifier = identifier
        search_index = self.content.searchIndex

        if element == 1:
            # Look for VM
            object = search_index.FindByUuid(uuid=identifier, vmSearch=True, instanceUuid=True)
        elif element == 2:
            # Look for ESXi host
            object = search_index.FindByDnsName(dnsName=identifier, vmSearch=False)
        elif element == 3:
            # look for cluster
            datacenters = self.content.rootFolder.childEntity
            for datacenter in datacenters:  # Iterate through DataCenters
                clusters = datacenter.hostFolder.childEntity
                for cluster in clusters:
                    if cluster.name == identifier:
                        object = cluster
        elif element == 4:
            # the object was passed in the argument of the method
            object = identifier

        # INTERVALS
        # ONE DAY
        end_time = datetime.today() - timedelta(days=1)
        sampling_period = 300

        if interval == '2':
            # ONE WEEK - 5 minutes sampling period
            end_time = datetime.today() - timedelta(weeks=1)
            sampling_period = 1800
        elif interval == '3':
            # ONE MONTH - 2 hours sampling period
            end_time = datetime.today() - timedelta(weeks=4)
            sampling_period = 7200
        elif interval == '4':
            # ONE YEAR or Historic Interval - 1 day sampling period
            end_time = datetime.today() - timedelta(days=365)
            sampling_period = 86400

        metric_object = self.BuildQuery(self.content, (self.StatCheck(self.perf_dict, metric)), sampling_period, "", object,
                                        end_time, datetime.today())

        (metric_times, metric_values) = self.get_values(metric_object)

        # GET MAX VALUE OF MEMORY
        if get_max == True:
            if element == 1:
                # get max value for VM
                max_value = object.summary.config.memorySizeMB
            elif element == 2:
                # get max value for ESXi host
                max_value = object.systemResources.config.memoryAllocation.limit
            else:
                # get max value for cluster
                max_value = object.summary.effectiveMemory

            return metric_times, metric_values, max_value

        return metric_times, metric_values

    def get_graph(self, identifier, element, metric, interval, title, conversion):

        if conversion == 3:
            # Get max value also in this case
            get_max = True
            time_values, metric_values, max_value = self.get_metric(identifier, element, metric, interval, get_max)
            max_value = round(max_value / 1024)
        else:
            time_values, metric_values = self.get_metric(identifier, element, metric, interval)

        if conversion == 1:
            # The metric in % needs to be divided by 100
            metric_values = [x / 100 for x in metric_values]
        elif conversion == 2:
            # Convert metric from  KBps to Mbps
            metric_values = [(x * 8) / 1024 for x in metric_values]
        elif conversion == 3:
            # Convert metric from KB to GB
            metric_values = [((x / 1024) / 1024) for x in metric_values]

        data = [
            go.Scatter(
                x=time_values,
                y=metric_values
            )
        ]

        if conversion == 1:
            layout = go.Layout(
                margin=dict(t=20, l=40, r=40, b=40),
                showlegend=False,
                height=300,
                xaxis=dict(
                    title="Date",
                    autorange=True
                ),
                yaxis=dict(
                    title="Percentage",
                    rangemode='tozero',
                    range=[0, 100]
                )
            )
        elif conversion == 2:
            layout = go.Layout(
                margin=dict(t=20, l=40, r=40, b=40),
                showlegend=False,
                height=300,
                xaxis=dict(
                    title="Date",
                    autorange=True
                ),
                yaxis=dict(
                    title="Mbps",
                    autorange=True,
                    rangemode='tozero'
                )
            )
        elif conversion == 3:
            layout = go.Layout(
                margin=dict(t=20, l=40, r=40, b=40),
                showlegend=False,
                height=300,
                xaxis=dict(
                    title="Date",
                    autorange=True
                ),
                yaxis=dict(
                    title='GB',
                    range=[0, max_value]
                )
            )
        else:
            layout = go.Layout(
                margin=dict(t=20, l=40, r=40, b=40),
                showlegend=False,
                height=300,
                xaxis=dict(
                    title="Date",
                    autorange=True
                ),
                yaxis=dict(
                    title="KBps",
                    autorange=True,
                    rangemode='tozero'
                )
            )

        fig = go.Figure(data=data, layout=layout)
        graph = plotly.offline.plot(fig, auto_open=False, output_type='div', show_link=False)

        return graph

    def get_graph_cluster_network_disk(self, cluster_name, interval):

        total_network_usage = []
        network_metric_times = []
        total_disk_usage = []
        disk_metric_times = []

        # INTERVALS
        # ONE DAY
        end_time = datetime.today() - timedelta(days=1)
        sampling_period = 300

        if interval == '2':
            # ONE WEEK - 5 minutes sampling period
            end_time = datetime.today() - timedelta(weeks=1)
            sampling_period = 1800
        elif interval == '3':
            # ONE MONTH - 2 hours sampling period
            end_time = datetime.today() - timedelta(weeks=4)
            sampling_period = 7200
        elif interval == '4':
            # ONE YEAR or Historic Interval - 1 day sampling period
            end_time = datetime.today() - timedelta(days=365)
            sampling_period = 86400

        datacenters = self.content.rootFolder.childEntity

        for datacenter in datacenters:  # Iterate through DataCenters
            clusters = datacenter.hostFolder.childEntity
            for cluster in clusters:  # Iterate through the clusters in DC
                if cluster.name == cluster_name:
                    hosts = cluster.host
                    for host in hosts:  # Iterate through Hosts in the cluster
                        # GET Network Usage [KBps]
                        metric_object_network = self.BuildQuery(self.content, (self.StatCheck(self.perf_dict, 'net.usage.average')), sampling_period, "", host,
                                                        end_time, datetime.today())

                        (network_metric_times, host_network_values) = self.get_values(metric_object_network)

                        if total_network_usage:
                            # It is not empty
                            temp_list = [(x + y) for x, y in zip(total_network_usage, host_network_values)]
                            total_network_usage = list(temp_list)
                        else:
                            total_network_usage = list(host_network_values)

                        # GET Disk [KBps]
                        metric_object = self.BuildQuery(self.content, (self.StatCheck(self.perf_dict, 'disk.usage.average')), sampling_period, "", host,
                                                             end_time, datetime.today())

                        (disk_metric_times, host_disk_values) = self.get_values(metric_object)

                        if total_disk_usage:
                            # It is not empty
                            temp_list = [(x + y) for x, y in zip(total_disk_usage, host_disk_values)]
                            total_disk_usage = list(temp_list)
                        else:
                            total_disk_usage = list(host_disk_values)

        network_data = [
            go.Scatter(
                x=network_metric_times,
                y=total_network_usage
            )
        ]
        disk_data = [
            go.Scatter(
                x=disk_metric_times,
                y=total_disk_usage
            )
        ]
        layout = go.Layout(
                margin=dict(t=20, l=40, r=40, b=40),
                showlegend=False,
                height=300,
                xaxis=dict(
                    title="Date",
                    autorange=True
                ),
                yaxis=dict(
                    title="KBps",
                    autorange=True,
                    rangemode='tozero'
                )
        )

        fig_network = go.Figure(data=network_data, layout=layout)
        graph_network = plotly.offline.plot(fig_network, auto_open=False, output_type='div', show_link=False)

        fig_disk = go.Figure(data=disk_data, layout=layout)
        graph_disk= plotly.offline.plot(fig_disk, auto_open=False, output_type='div', show_link=False)

        return graph_network, graph_disk

    # Function to get values for doughnut graphs (Top memory, cpu and storage)
    def get_pie_graph(self, metric, total_value, consumed_value):

        if metric == 'MEMORY':
            labels = ['Consumed Memory', 'Free Memory']
        elif metric == 'CPU':
            labels = ['Consumed CPU', 'Free CPU']
        elif metric == 'STORAGE':
            labels = ['Used Storage', 'Free Storage']

        values = [consumed_value, (total_value - consumed_value)]

        fig = {
            'data': [
                {
                    'labels': labels,
                    'values': values,
                    'type': 'pie',
                    'name': 'Memory'
                }
            ],
            'layout': {'showlegend': False, 'width': 300, 'height': 300}
        }

        graph = plotly.offline.plot(fig, auto_open=False, output_type='div')

        return graph

    # Function to get values and graph metrics of all clusters together
    def get_graph_cumulative(self, metric, interval, convert, title):

        datacenters = self.content.rootFolder.childEntity

        y_cluster_values = []
        time_x = []
        max_len_time_x = 0

        for datacenter in datacenters:  # Iterate through DataCenters
            clusters = datacenter.hostFolder.childEntity
            for cluster in clusters:
                values = []
                metric_time = []
                # Get Storage Usage in the cluster
                if title == 'Storage Usage':
                    datastores = cluster.datastore
                    for datastore in datastores:
                        (metric_time_1, metric_values) = self.get_metric(datastore, 4, metric, interval)

                        if values:
                            # It is not empty
                            temp_list = [(x + y) for x, y in zip(values, metric_values)]
                            values = list(temp_list)
                        else:
                            values = list(metric_values)

                        metric_time = list(metric_time_1)

                    # Convert values from KB to GB
                    values = [round(((x / 1024) / 1024), 2) for x in values]

                else:
                    (metric_time, metric_values) = self.get_metric(cluster, 4, metric, interval)
                    # convert from KB to GB
                    if convert == 1:
                        values = [round(((x / 1024) / 1024), 2) for x in metric_values]
                    # convert from MHz to GHz
                    if convert == 2:
                        values = [round((x / 1000), 2) for x in metric_values]

                cluster_values = {'name': cluster.name, 'values': values}
                y_cluster_values.append(cluster_values.copy())
                # keep only the largest time_x (metric_time)
                len_time = len(metric_time)
                if len_time > max_len_time_x:
                    max_len_time_x = len_time
                    time_x = metric_time

        y_accumulative = []
        count = 0
        data_graph = []
        colors = ['rgb(255, 211, 154)', 'rgb(128, 195, 210)', 'rgb(255, 253, 186)', 'rgb(187, 233, 252)',
                  'rgb(184, 247, 212)', 'rgb(229, 182, 251)', 'rgb(200, 82, 51)', 'rgb(130, 140, 50)', 'rgb(232, 12, 21)']
        for y_value in y_cluster_values:
            y_values = y_value['values']
            if count == 0:
                y_accumulative = y_values
                count += 1
            else:
                y_temp = y_accumulative
                # Check size of the list - make both of the same size (largest one)
                len_accumulative = len(y_temp)
                len_values = len(y_values)
                if len_accumulative < len_values:
                    diff_len = len_values - len_accumulative
                    list_zeros = [0] * diff_len
                    y_temp = list_zeros + y_temp
                else:
                    diff_len = len_accumulative - len_values
                    list_zeros = [0] * diff_len
                    y_values = list_zeros + y_values

                y_accumulative = [y0 + y1 for y0, y1 in zip(y_values, y_temp)]

            # Make original values strings and add % for hover text
            # This is to show the real value when mouse over in the graph
            if convert == 1:
                y0_txt = [str(y0) + 'GB' for y0 in y_values]
                y_title = 'GB'
            if convert == 2:
                y0_txt = [str(y0) + 'GHz' for y0 in y_values]
                y_title = 'GHz'
            if title == 'Storage Usage':
                y0_txt = [str(y0) + 'GB' for y0 in y_values]
                y_title = 'GB'

            trace = go.Scatter(
                x=time_x,
                y=y_accumulative,
                text=y0_txt,
                hoverinfo='x+text',
                mode='lines',
                name=y_value['name'],
                line=dict(width=0.5,
                          color=colors[count - 1]),
                fill='tonexty'
            )

            data_graph.append(trace)
            count += 1

        layout = go.Layout(
            margin=dict(t=20, b=40),
            height=400,
            xaxis=dict(
                title="Date",
                autorange=True
            ),
            yaxis=dict(
                title=y_title,
                autorange=True,
                rangemode='tozero'
            )
        )

        fig = go.Figure(data=data_graph, layout=layout)
        graph = plotly.offline.plot(fig, auto_open=False, output_type='div', show_link=False)

        return graph

    # Get clusters, hosts and VMs to create menu
    def get_elements(self):
        datacenters = self.content.rootFolder.childEntity

        list_datacenters = []

        for datacenter in datacenters:  # Iterate through DataCenters
            clusters = datacenter.hostFolder.childEntity
            list_clusters = []

            for cluster in clusters:  # Iterate through the clusters in DC
                hosts = cluster.host
                list_hosts = []
                list_vm = []
                for host in hosts:  # Iterate through Hosts in the cluster
                    vms = host.vm
                    for vm in vms:
                        try:
                            dict_vm = {'name': vm.name, 'uuid': vm.config.instanceUuid}
                            list_vm.append(dict_vm.copy())
                        except:
                            pass
                    list_hosts.append(host.name)

                list_vms_sorted = sorted(list_vm, key=lambda i: i['name'])
                list_hosts.sort()
                dict_cluster = {'name': cluster.name, 'hosts': list_hosts, 'vms': list_vms_sorted}
                list_clusters.append(dict_cluster.copy())

            dict_datacenter = {datacenter.name: list_clusters}
            list_datacenters.append(dict_datacenter.copy())

        return list_datacenters

    def get_vms(self):
        datacenters = self.content.rootFolder.childEntity

        vm_list = []

        for datacenter in datacenters:  # Iterate through DataCenters
            clusters = datacenter.hostFolder.childEntity
            for cluster in clusters:  # Iterate through the clusters in DC
                hosts = cluster.host
                for host in hosts:  # Iterate through Hosts in the cluster
                    vms = host.vm
                    for vm in vms:
                        vm_list.append(vm.name)
        return vm_list

    # Function to get VMs that are using more resources in the Cluster - CPU, Memory
    def get_top_vms_cluster(self, cluster_name, resource):

        datacenters = self.content.rootFolder.childEntity

        vms_top_name = ['']*5
        vms_top_val = [0, 0, 0, 0, 0]

        for datacenter in datacenters:  # Iterate through DataCenters
            clusters = datacenter.hostFolder.childEntity
            for cluster in clusters:  # Iterate through the clusters in DC
                # print ('Cluster: ' + cluster.name)
                if cluster.name == cluster_name:
                    hosts = cluster.host
                    for host in hosts:  # Iterate through Hosts in the cluster
                        # print ('Host: ' + host.name)
                        vms = host.vm
                        for vm in vms:
                            # GET value of consumed memory [MB] or CPU [MHz] at that moment
                            if resource == 'MEMORY':
                                value = vm.summary.quickStats.hostMemoryUsage
                            else:
                                value = vm.summary.quickStats.overallCpuUsage

                            for index, val in enumerate(vms_top_val):
                                if value > val:
                                    # Insert Value
                                    temp_mem = vms_top_val[index:4]
                                    if resource == 'MEMORY':
                                        # Convert Memory from MB to GB
                                        value = value
                                    else:
                                        # Convert Consumed CPU from MHz to GHz
                                        value = value
                                    vms_top_val[index] = value
                                    vms_top_val = vms_top_val[0:(index + 1)] + temp_mem
                                    # NAMES
                                    temp_name = vms_top_name[index:4]
                                    vms_top_name[index] = vm.name
                                    new_vms_top_name = vms_top_name[0:(index+1)] + temp_name
                                    vms_top_name = new_vms_top_name
                                    break

        # Remove not initialized elements from list
        top_names = list(filter(lambda a: a != '', vms_top_name))

        top_vms = {'name': top_names, 'values': vms_top_val}

        return top_vms

    # Function to get Hosts that are using more resources in the Cluster - CPU, Memory
    def get_top_hosts_cluster(self, cluster_name, resource):

        datacenters = self.content.rootFolder.childEntity

        hosts_top_name = ['']*5
        hosts_top_val = [0, 0, 0, 0, 0]

        for datacenter in datacenters:  # Iterate through DataCenters
            clusters = datacenter.hostFolder.childEntity
            for cluster in clusters:  # Iterate through the clusters in DC
                # print ('Cluster: ' + cluster.name)
                if cluster.name == cluster_name:
                    hosts = cluster.host
                    for host in hosts:  # Iterate through Hosts in the cluster
                        # GET value of consumed memory [MB] or CPU at that moment
                        if resource == 'MEMORY':
                            mem_consumed_val = host.summary.quickStats.overallMemoryUsage
                        else:
                            mem_consumed_val = host.summary.quickStats.overallCpuUsage

                        for index, mem_val in enumerate(hosts_top_val):
                            if mem_consumed_val > mem_val:
                                # MEMORY
                                temp_mem = hosts_top_val[index:4]
                                hosts_top_val[index] = mem_consumed_val
                                hosts_top_val = hosts_top_val[0:(index + 1)] + temp_mem
                                # NAMES
                                temp_name = hosts_top_name[index:4]
                                hosts_top_name[index] = host.name
                                new_hosts_top_name = hosts_top_name[0:(index+1)] + temp_name
                                hosts_top_name = new_hosts_top_name
                                break

        # Remove not initialized elements from list
        top_names = list(filter(lambda a: a != '', hosts_top_name))

        top_hosts = {'name': top_names, 'values': hosts_top_val}

        return top_hosts

    # Function to get Memory, CPU and Storage Capacity in the Datacenter
    def get_usage_metrics_datacenter(self):

        num_clusters = 0
        num_hosts = 0
        num_vms = 0
        num_datastores = 0
        total_memory = 0
        total_memory_cluster = 0
        total_cpu = 0
        total_cpu_cluster = 0
        total_consumed_mem = 0
        total_consumed_mem_cluster = 0
        total_consumed_cpu = 0
        total_consumed_cpu_cluster = 0
        total_storage = 0
        total_storage_cluster = 0
        free_storage = 0
        free_storage_cluster = 0
        total_used_network_cluster = 0

        cluster_names = []
        cluster_mem_values = []
        cluster_cpu_values = []
        cluster_storage_values = []
        cluster_network_values = []

        #Dict
        clusters_percents = {}

        max_total_values = []
        counter_hosts = 0

        datacenters = self.content.rootFolder.childEntity

        for datacenter in datacenters:  # Iterate through DataCenters
            clusters = datacenter.hostFolder.childEntity
            for cluster in clusters:  # Iterate through the clusters in DC
                num_clusters += 1
                num_hosts += cluster.summary.numHosts
                num_vms += cluster.summary.usageSummary.totalVmCount
                # GET Total Memory [bytes]
                total_memory_cluster = cluster.summary.totalMemory
                # Get Total CPU [MHz]
                total_cpu_cluster = cluster.summary.totalCpu
                # GET Total Consumed Memory and CPU in the cluster
                hosts = cluster.host
                for host in hosts:  # Iterate through Hosts in the cluster
                    # GET value of consumed memory [MB] and CPU [MHz] at that moment
                    total_consumed_mem_cluster += host.summary.quickStats.overallMemoryUsage
                    total_consumed_cpu_cluster += host.summary.quickStats.overallCpuUsage

                    # Get Network Usage
                    # ONE DAY
                    end_time = datetime.today() - timedelta(days=1)
                    sampling_period = 300
                    metric_object = self.BuildQuery(self.content, (self.StatCheck(self.perf_dict, 'net.usage.average')), sampling_period, "*", host,
                                                    end_time, datetime.today())

                    (times, network_usage_values) = self.get_values(metric_object)

                    # Get the average for network usage
                    counter = 0
                    total = 0
                    for val in network_usage_values:
                        counter += 1
                        total = total + val

                    network_usage_values_average = total / counter
                    total_used_network_cluster += network_usage_values_average

                    # GET MAX Latency values (Only query one host - supposing same datastores connected to all hosts)
                    if counter_hosts == 0:
                        metric = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'disk.maxTotalLatency.latest')), 20, "*", host)
                        (times, max_total_values) = self.get_values(metric)
                        counter_hosts = 1

                counter_hosts = 0

                # Get list of Datastores in the Cluster
                datastores = cluster.datastore
                num_datastores += len(datastores)
                for datastore in datastores:  # Iterate through Datastores in the cluster
                    # Get Total Storage [Bytes] and Free Storage [Bytes] and add them to total cluster metric
                    total_storage_cluster += datastore.summary.capacity
                    free_storage_cluster += datastore.summary.freeSpace

                # Get values for Pie Charts graphs
                pie_consumed_memory = round(total_consumed_mem_cluster / 1024, 2)  # GB
                pie_consumed_cpu = round(total_consumed_cpu_cluster / 1000, 3)  # GHz
                temp_consumed_storage = total_storage_cluster - free_storage_cluster
                pie_consumed_storage = round((((temp_consumed_storage / 1024) / 1024) / 1024), 2)   # GB
                pie_consumed_network = round(total_used_network_cluster)  # KBps

                cluster_names.append(cluster.name)

                cluster_mem_values.append({'cluster_name': cluster.name, 'value': pie_consumed_memory})
                cluster_cpu_values.append({'cluster_name': cluster.name, 'value': pie_consumed_cpu})
                cluster_storage_values.append({'cluster_name': cluster.name, 'value': pie_consumed_storage})
                cluster_network_values.append({'cluster_name': cluster.name, 'value': pie_consumed_network})

                # End Pie Charts values

                # Get values for Line Charts

                percent_cpu_used_cluster = round((total_consumed_cpu_cluster / total_cpu_cluster) * 100)
                # Convert Total Memory in the cluster from bytes to MB
                total_memory_cluster_mb = round((total_memory_cluster / 1024) / 1024, 2)
                percent_memory_consumed_cluster = round((total_consumed_mem_cluster / total_memory_cluster_mb) * 100)
                percent_used_storage_cluster = round((temp_consumed_storage / total_storage_cluster) * 100)

                # Get the average for Max_Total_Latency
                counter = 0
                total = 0
                for val in max_total_values:
                    counter += 1
                    total += val

                max_latency_average = total / counter
                # The total disk average latency should be below 20ms.
                # In this case I am using 25 as the maximum for the line graph
                if max_latency_average <= 25:
                    max_latency_average_percent = round((max_latency_average / 25) * 100)
                else:
                    max_latency_average_percent = 100

                value_percent = {'cpu': percent_cpu_used_cluster, 'memory': percent_memory_consumed_cluster,
                                 'storage': percent_used_storage_cluster, 'max_average_latency_percent': max_latency_average_percent,
                                 'max_latency_value': round(max_latency_average)}
                clusters_percents[cluster.name] = value_percent

                # END Line Charts values

                total_memory += total_memory_cluster
                total_cpu += total_cpu_cluster

                total_consumed_mem += total_consumed_mem_cluster
                total_consumed_cpu += total_consumed_cpu_cluster

                total_storage = total_storage + total_storage_cluster
                free_storage = free_storage + free_storage_cluster

                # Reset cluster variables
                total_consumed_mem_cluster = 0
                total_consumed_cpu_cluster = 0
                total_storage_cluster = 0
                free_storage_cluster = 0
                total_used_network_cluster = 0

        # Calculate CPU % before doing conversions
        percent_consumed_cpu = round((total_consumed_cpu / total_cpu) * 100)

        # Convert Consumed Memory from MB to GB
        total_consumed_mem = round(total_consumed_mem / 1024, 2)

        # Convert Total CPU from MHz to GHz
        total_cpu = round(total_cpu / 1000, 2)
        # Convert Total Memory from bytes to GB
        total_memory = round(((total_memory / 1024) / 1024) / 1024, 2)
        # Calculate free memory
        free_memory = round(total_memory - total_consumed_mem, 2)

        # Convert Consumed CPU from MHz to GHz
        total_consumed_cpu = round(total_consumed_cpu / 1000, 3)

        # Calculate free cpu
        free_cpu = round(total_cpu - total_consumed_cpu, 2)

        # Convert Total and Free Storage from Bytes to TB
        total_storage = round(((((total_storage / 1024) / 1024) / 1024) / 1024), 2)
        free_storage = round(((((free_storage / 1024) / 1024) / 1024) / 1024), 2)

        # Calculate Memory %
        percent_consumed_mem = round((total_consumed_mem / total_memory) * 100)

        used_storage = round(total_storage - free_storage, 2)
        percent_used_storage = round((used_storage / total_storage) * 100)

        # SORT PIE VALUES - TOP 5
        cluster_mem_values_sorted = sorted(cluster_mem_values, key=lambda i: i['value'], reverse=True)
        cluster_cpu_values_sorted = sorted(cluster_cpu_values, key=lambda i: i['value'], reverse=True)
        cluster_storage_values_sorted = sorted(cluster_storage_values, key=lambda i: i['value'], reverse=True)
        cluster_network_values_sorted = sorted(cluster_network_values, key=lambda i: i['value'], reverse=True)

        return_value = {'total_memory': total_memory, 'total_consumed_mem': total_consumed_mem,
                        'free_memory': free_memory, 'percent_consumed_mem': percent_consumed_mem,
                        'total_cpu': total_cpu, 'total_consumed_cpu': total_consumed_cpu,
                        'free_cpu': free_cpu, 'percent_consumed_cpu': percent_consumed_cpu,
                        'total_storage': total_storage, 'free_storage': free_storage,
                        'used_storage': used_storage, 'percent_used_storage': percent_used_storage,
                        'cluster_names': cluster_names, 'cluster_mem_values': cluster_mem_values_sorted[:5],
                        'cluster_cpu_values': cluster_cpu_values_sorted[:5], 'cluster_storage_values': cluster_storage_values_sorted[:5],
                        'cluster_network_values': cluster_network_values_sorted[:5], 'clusters_percents': clusters_percents,
                        'num_clusters': num_clusters, 'num_hosts': num_hosts, 'num_vms': num_vms, 'num_datastores': num_datastores}

        return return_value

    # Function to get Memory, CPU and Storage Capacity in the Cluster, also RealTime graph values
    def get_usage_metrics_cluster(self, object_name):

        total_memory = 0
        total_cpu = 0
        total_consumed_mem = 0
        total_consumed_cpu = 0
        total_active_memory = []
        active_memory_time = []
        total_ballooned_memory = []
        total_swapused_memory = []
        total_cpu_usage_percent = []
        total_cpu_readiness_percent = []
        total_network_transmitted_rate = []
        total_network_received_rate = []
        total_disks_read_rate = []
        total_disks_write_rate = []
        total_storage = 0
        free_storage = 0

        total_power = 0

        counter_hosts = 0
        lun_instances = {}
        times = []
        datastores_latency = {}
        datastores_lun_name = {}
        datastores_usage_dict = {}

        datacenters = self.content.rootFolder.childEntity

        for datacenter in datacenters:  # Iterate through DataCenters
            # print ('Data Center: ' + datacenter.name)
            clusters = datacenter.hostFolder.childEntity
            for cluster in clusters:  # Iterate through the clusters in DC
                # print ('Cluster: ' + cluster.name)
                if cluster.name == object_name:
                    num_hosts = cluster.summary.numHosts
                    num_vms = cluster.summary.usageSummary.totalVmCount
                    # Check if HA and DRS are enabled
                    if cluster.configuration.dasConfig.enabled:
                        ha = 'ON'
                    else:
                        ha = 'OFF'
                    if cluster.configuration.drsConfig.enabled:
                        drs = 'ON'
                    else:
                        drs = 'OFF'
                    # GET Total Memory [bytes]
                    total_memory = cluster.summary.totalMemory
                    # Get Total CPU [MHz]
                    total_cpu = cluster.summary.totalCpu
                    # GET Total Consumed Memory and CPU in the cluster
                    hosts = cluster.host
                    for host in hosts:  # Iterate through Hosts in the cluster
                        # Get power
                        metric_object = self.BuildQuery_RealTime(self.content, self.perf_dict['power.power.average'],
                                                                 20, "*", host)
                        values = metric_object[0].value[0].value
                        power_average = sum(values) / len(values)
                        total_power += power_average

                        # GET value of consumed memory [MB] and CPU [MHz] at that moment
                        total_consumed_mem = total_consumed_mem + host.summary.quickStats.overallMemoryUsage
                        total_consumed_cpu = total_consumed_cpu + host.summary.quickStats.overallCpuUsage

                        # GET ACTIVE MEMORY
                        metric_active_memory = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'mem.active.average')), 20, "", host)
                        (memory_time, active_memory_values) = self.get_values(metric_active_memory)

                        if total_active_memory:
                            # It is not empty
                            temp_list = [(x + y) for x, y in zip(total_active_memory, active_memory_values)]
                            total_active_memory = list(temp_list)
                        else:
                            total_active_memory = list(active_memory_values)

                        active_memory_time = list(memory_time)

                        # GET BALLOONED MEMORY
                        metric_balloned_memory = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'mem.vmmemctl.average')), 20, "", host)
                        (memory_time, ballooned_memory_values) = self.get_values(metric_balloned_memory)

                        if total_ballooned_memory:
                            # It is not empty
                            temp_list = [(x + y) for x, y in zip(total_ballooned_memory, ballooned_memory_values)]
                            total_ballooned_memory = list(temp_list)
                        else:
                            total_ballooned_memory = list(ballooned_memory_values)

                        # GET SWAPPED MEMORY
                        metric_swapped_memory = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'mem.swapused.average')), 20, "", host)
                        (memory_time, swapused_memory_values) = self.get_values(metric_swapped_memory)

                        if total_swapused_memory:
                            # It is not empty
                            temp_list = [(x + y) for x, y in zip(total_swapused_memory, swapused_memory_values)]
                            total_swapused_memory = list(temp_list)
                        else:
                            total_swapused_memory = list(swapused_memory_values)

                        # GET CPU Usage (%)
                        metric_cpu_usage = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'cpu.usage.average')), 20, "", host)
                        (cpu_time, cpu_usage_values) = self.get_values(metric_cpu_usage)

                        # The metric in % needs to be divided by 100
                        cpu_usage_values_percent = [x / 100 for x in cpu_usage_values]

                        if total_cpu_usage_percent:
                            # It is not empty
                            temp_list = [(x + y) for x, y in zip(total_cpu_usage_percent, cpu_usage_values_percent)]
                            total_cpu_usage_percent = list(temp_list)
                        else:
                            total_cpu_usage_percent = list(cpu_usage_values_percent)

                        # GET CPU Readiness (%)
                        metric_cpu_readiness = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'cpu.readiness.average')), 20, "", host)
                        (cpu_time, cpu_readiness_values) = self.get_values(metric_cpu_readiness)

                        # The metric in % needs to be divided by 100
                        cpu_readiness_values_percent = [x / 100 for x in cpu_readiness_values]

                        if total_cpu_readiness_percent:
                            # It is not empty
                            temp_list = [(x + y) for x, y in zip(total_cpu_readiness_percent, cpu_readiness_values_percent)]
                            total_cpu_readiness_percent = list(temp_list)
                        else:
                            total_cpu_readiness_percent = list(cpu_readiness_values_percent)

                        # Get Network transmitted rate [KBps]
                        network_transmitted_rate = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'net.transmitted.average')), 20, "", host)
                        (network_time, network_transmitted_rate_values) = self.get_values(network_transmitted_rate)

                        if total_network_transmitted_rate:
                            # It is not empty
                            temp_list = [(x + y) for x, y in zip(total_network_transmitted_rate, network_transmitted_rate_values)]
                            total_network_transmitted_rate = list(temp_list)
                        else:
                            total_network_transmitted_rate = list(network_transmitted_rate_values)

                        # Get Network Received rate [KBps]
                        network_received_rate = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'net.received.average')), 20, "", host)
                        (network_time, network_received_rate_values) = self.get_values(network_received_rate)

                        if total_network_received_rate:
                            # It is not empty
                            temp_list = [(x + y) for x, y in zip(total_network_received_rate, network_received_rate_values)]
                            total_network_received_rate = list(temp_list)
                        else:
                            total_network_received_rate = list(network_received_rate_values)



                        # GET LUNs Latency Values (Only query one host - supposing same datastores connected to all hosts)
                        # GET READ RATE (Rate at which data is read from each LUN on the hos)
                        # GET WRITE RATE (Rate at which data is written to each LUN on the host)
                        if counter_hosts == 0:
                            metric = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'disk.totalLatency.average')), 20, "*", host)
                            (times, lun_instances) = self.get_instance_values(metric)


                            # Look for the datastore name for the specific Disk name (naa.24324...)
                            # Get a dictionary dict[disk_name] = datastore_name
                            storage_system = host.configManager.storageSystem
                            host_file_sys_vol_mount_info = storage_system.fileSystemVolumeInfo.mountInfo

                            for host_mount_info in host_file_sys_vol_mount_info:
                                # Add support later for other type of volumes: VVOL, VSAN
                                if host_mount_info.volume.type == "VMFS":
                                    datastore_name = host_mount_info.volume.name
                                    disks = host_mount_info.volume.extent
                                    for disk in disks:
                                        datastores_lun_name[disk.diskName] = datastore_name


                            # GET READ RATE [KBps]
                            disk_read_rate = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'disk.read.average')), 20, "", host)
                            (disk_time, total_disks_read_rate) = self.get_network_values(disk_read_rate)

                            # GET WRITE RATE [KBps]
                            disk_write_rate = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'disk.write.average')), 20, "", host)
                            (disk_time, total_disks_write_rate) = self.get_network_values(disk_write_rate)

                            counter_hosts = 1

                    # Get list of Datastores in the Cluster
                    datastores = cluster.datastore
                    for datastore in datastores:  # Iterate through Datastores in the cluster
                        num_datastores = len(datastores)
                        # Get Total Storage and Free Storage [bytes] and add them to total cluster metric
                        capacity = datastore.summary.capacity
                        free_space = datastore.summary.freeSpace

                        total_storage = total_storage + capacity
                        free_storage = free_storage + free_space

                        # Create Dictionary with Datastores and their free and used space
                        # Convert Total Storage from Bytes to GB
                        capacity_GB = round((((capacity / 1024) / 1024) / 1024), 1)
                        free_space_GB = round((((free_space / 1024) / 1024) / 1024), 1)
                        used_space_GB = round(capacity_GB - free_space_GB, 1)

                        percent = round((used_space_GB / capacity_GB) * 100)

                        usage_dict = {'percent': percent, 'used_space_GB': used_space_GB}

                        datastores_usage_dict[datastore.name] = usage_dict

                        #Modify later to only add the more used datastores (top 5?)


                    # GET VALUES for LINEAR GRAPHS - Datastores -latencies
                    for instance_lun, latency_values in lun_instances.items():
                        # Make sure the deviceID exist in the dictionary created above - datastores_lun_name
                        if instance_lun in datastores_lun_name:
                            # Get average of latency_values
                            # Get the average for Max_Total_Latency
                            counter = 0
                            total = 0
                            latency_average_percent = 0
                            for val in latency_values:
                                counter += 1
                                total = total + val

                            latency_average = total / counter
                            # The total disk average latency should be below 20ms.
                            # In this case I am using 25 as the maximum for the line graph
                            if latency_average <= 25:
                                latency_average_percent = round((latency_average / 25) * 100)
                            else:
                                latency_average_percent = 100

                            datastore_latency_values = {'percent': latency_average_percent, 'value': round(latency_average)}
                            datastore_name = datastores_lun_name[instance_lun]
                            datastores_latency[datastore_name] = datastore_latency_values

                        ## MODIFY LATER BECAUSE I ONLY NEED TOP 5 DASTORES WITH HIGHEST LATECNY VALUES

                    #Sort names
                    datastores_usage_dict_sorted = dict(sorted(datastores_usage_dict.items(), key=lambda i: i[0]))
                    datastores_latency_sorted = dict(sorted(datastores_latency.items(), key=lambda i: i[0]))

                    # END LINEAR GRAPH


        # Calculate CPU % before doing conversions
        percent_consumed_cpu = round((total_consumed_cpu / total_cpu) * 100)

        # Convert Consumed Memory from MB to GB
        total_consumed_mem = round(total_consumed_mem / 1024, 2)

        # Convert Total CPU from MHz to GHz
        total_cpu = round(total_cpu / 1000, 2)

        # Convert consumed_memory only for clusters and Storage is only for cluster not ESXi hosts
        # Convert Total Memory from bytes to GB
        total_memory = round(((total_memory / 1024) / 1024) / 1024, 2)
        # Calculate free memory
        free_memory = round(total_memory - total_consumed_mem, 2)
        # Convert Consumed CPU from MHz to GHz
        total_consumed_cpu = round(total_consumed_cpu / 1000, 3)
        free_cpu = round(total_cpu - total_consumed_cpu, 2)
        # Convert Total Storage from Bytes to TB
        total_storage = round((((total_storage / 1024) / 1024) / 1024) / 1024, 2)
        free_storage = round((((free_storage / 1024) / 1024) / 1024) / 1024, 2)


        # Convert this list from datetime.datetime object to string
        active_memory_time_converted = [x.__str__() for x in active_memory_time]

        # Convert Total Active Memory from KB to GB
        temp_list_1 = [(x / 1024) / 1024 for x in total_active_memory]
        total_active_memory = list(temp_list_1)

        # Convert Total Ballooned Memory from KB to GB
        temp_list_2 = [(x / 1024) / 1024 for x in total_ballooned_memory]
        total_ballooned_memory = list(temp_list_2)

        # Convert Total Swapped Memory from KB to GB
        temp_list_3 = [(x / 1024) / 1024 for x in total_swapused_memory]
        total_swapused_memory = list(temp_list_3)

        # Get the percent of the total_CPU_USAGE (%) RealTime
        # All the percents for each host were added when iterating the hosts in the cluster
        for list_key, value in enumerate(total_cpu_usage_percent):
            total_cpu_usage_percent[list_key] = round(value / num_hosts, 2)

        # Get the percent of the total_CPU_Readiness (%) RealTime
        # All the percents for each host were added when iterating the hosts in the cluster
        for list_key, value in enumerate(total_cpu_readiness_percent):
            total_cpu_readiness_percent[list_key] = round(value / num_hosts, 2)

        # Calculate Memory %
        percent_consumed_mem = round((total_consumed_mem / total_memory) * 100)

        used_storage = round(total_storage - free_storage, 2)
        percent_used_storage = round((used_storage / total_storage) * 100)

        return_value = {'total_memory': total_memory, 'total_consumed_mem': total_consumed_mem,
                        'free_memory': free_memory, 'percent_consumed_mem': percent_consumed_mem,
                        'total_cpu': total_cpu, 'total_consumed_cpu': total_consumed_cpu,
                        'free_cpu': free_cpu, 'percent_consumed_cpu': percent_consumed_cpu,
                        'total_storage': total_storage, 'free_storage': free_storage,
                        'used_storage': used_storage, 'percent_used_storage': percent_used_storage,
                        'datastores_latency': datastores_latency_sorted, 'active_memory_time': active_memory_time_converted,
                        'total_active_memory': total_active_memory, 'total_ballooned_memory': total_ballooned_memory,
                        'total_swapused_memory': total_swapused_memory, 'datastores_usage_dict': datastores_usage_dict_sorted,
                        'total_cpu_usage_percent': total_cpu_usage_percent, 'total_cpu_readiness_percent': total_cpu_readiness_percent,
                        'total_network_transmitted_rate': total_network_transmitted_rate,
                        'total_network_received_rate': total_network_received_rate,
                        'total_disks_read_rate': total_disks_read_rate, 'total_disks_write_rate': total_disks_write_rate,
                        'num_hosts': num_hosts, 'num_vms': num_vms, 'num_datastores': num_datastores, 'ha': ha,
                        'drs': drs, 'total_power': round(total_power)}

        return return_value

    # Function to get Memory, CPU and Storage Capacity for host and how much is being used
    # Also to get Real Time metrics
    def get_usage_metrics_host(self, object_name):

        search_index = self.content.searchIndex
        # Look for ESXi host
        esxi_host = search_index.FindByDnsName(dnsName=object_name, vmSearch=False)

        server_model = esxi_host.summary.hardware.model
        esxi_version = esxi_host.summary.config.product.version[:-2]
        num_vms = len(esxi_host.vm)
        num_nics = len(esxi_host.config.network.pnic)
        num_cpus = esxi_host.hardware.cpuInfo.numCpuThreads
        num_pg = len(esxi_host.network)
        boot_time_date = esxi_host.summary.runtime.bootTime
        today_date = datetime.utcnow()
        diff_time = today_date - boot_time_date.replace(tzinfo=None)
        uptime = diff_time.days

        # Get Memory. Memory values are in MB
        total_memory = esxi_host.systemResources.config.memoryAllocation.limit
        total_consumed_mem = esxi_host.summary.quickStats.overallMemoryUsage
        # Get CPU. CPU values are in MHz
        total_consumed_cpu = esxi_host.summary.quickStats.overallCpuUsage
        total_cpu = esxi_host.systemResources.config.cpuAllocation.limit

        # Calculate CPU % before doing conversions
        percent_consumed_cpu = round((total_consumed_cpu / total_cpu) * 100)

        # Convert Consumed Memory from MB to GB
        total_consumed_mem = round(total_consumed_mem / 1024, 2)

        # Convert Total CPU from MHz to GHz
        total_cpu = round(total_cpu / 1000, 2)

        # Convert Total Memory from MB to GB
        total_memory = round(total_memory / 1024, 2)
        # Calculate free memory
        free_memory = round(total_memory - total_consumed_mem, 2)
        temp_consumed_cpu = round(total_consumed_cpu / 1000, 3)
        free_cpu = round(total_cpu - temp_consumed_cpu, 2)

        # Calculate Memory %
        percent_consumed_mem = round((total_consumed_mem / total_memory) * 100)

        # REAL TIME METRICS

        # GET ACTIVE MEMORY
        metric_active_memory = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'mem.active.average')), 20, "", esxi_host)
        (memory_time, active_memory_values) = self.get_values(metric_active_memory)

        memory_time_values = list(memory_time)

        # GET BALLOONED MEMORY
        metric_balloned_memory = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'mem.vmmemctl.average')), 20, "", esxi_host)
        (memory_time, ballooned_memory_values) = self.get_values(metric_balloned_memory)

        # GET SWAPPED MEMORY
        metric_swapped_memory = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'mem.swapused.average')), 20, "", esxi_host)
        (memory_time, swapused_memory_values) = self.get_values(metric_swapped_memory)

        # GET CPU Usage (%)
        metric_cpu_usage = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'cpu.usage.average')), 20, "", esxi_host)
        (cpu_time, cpu_usage_values) = self.get_values(metric_cpu_usage)

        # The metric in % needs to be divided by 100
        cpu_usage_values_percent = [x / 100 for x in cpu_usage_values]

        # GET CPU Readiness (%)
        metric_cpu_readiness = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'cpu.readiness.average')), 20, "", esxi_host)
        (cpu_time, cpu_readiness_values) = self.get_values(metric_cpu_readiness)

        # The metric in % needs to be divided by 100
        cpu_readiness_values_percent = [x / 100 for x in cpu_readiness_values]

        # Get Network transmitted rate [KBps]
        network_transmitted_rate = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'net.transmitted.average')), 20, "", esxi_host)
        (network_time, network_transmitted_rate_values) = self.get_values(network_transmitted_rate)

         # Get Network Received rate [KBps]
        network_received_rate = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'net.received.average')), 20, "", esxi_host)
        (network_time, network_received_rate_values) = self.get_values(network_received_rate)

         # GET READ RATE [KBps]
        disk_read_rate = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'disk.read.average')), 20, "", esxi_host)
        (disk_time, disks_read_rate_values) = self.get_network_values(disk_read_rate)

        # GET WRITE RATE [KBps]
        disk_write_rate = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'disk.write.average')), 20, "", esxi_host)
        (disk_time, disks_write_rate_values) = self.get_network_values(disk_write_rate)

        # Convert Values

        # Concert this list from datetime.datetime object to string
        memory_time_converted = [x.__str__() for x in memory_time_values]

        # Convert Active Memory from KB to GB
        temp_list_1 = [(x / 1024) / 1024 for x in active_memory_values]
        active_memory = list(temp_list_1)

        active_memory_avg = round(sum(active_memory) / len(active_memory), 2)

        # Convert Ballooned Memory from KB to GB
        temp_list_2 = [(x / 1024) / 1024 for x in ballooned_memory_values]
        ballooned_memory = list(temp_list_2)

        # Convert Swapped Memory from KB to GB
        temp_list_3 = [(x / 1024) / 1024 for x in swapused_memory_values]
        swapused_memory = list(temp_list_3)

        return_value = {'total_memory': total_memory, 'total_consumed_mem': total_consumed_mem,
                        'free_memory': free_memory, 'percent_consumed_mem': percent_consumed_mem,
                        'total_cpu': total_cpu, 'total_consumed_cpu': total_consumed_cpu,
                        'free_cpu': free_cpu, 'percent_consumed_cpu': percent_consumed_cpu,
                        'memory_time': memory_time_converted, 'active_memory': active_memory,
                        'ballooned_memory': ballooned_memory, 'swapused_memory': swapused_memory,
                        'cpu_usage_percent': cpu_usage_values_percent, 'cpu_readiness_percent': cpu_readiness_values_percent,
                        'network_transmitted_rate': network_transmitted_rate_values,
                        'network_received_rate': network_received_rate_values, 'disks_read_rate': disks_read_rate_values,
                        'disks_write_rate': disks_write_rate_values, 'server_model': server_model,
                        'esxi_version': esxi_version, 'num_vms': num_vms, 'uptime': uptime, 'active_memory_avg': active_memory_avg,
                        'num_nics': num_nics, 'num_cpus': num_cpus, 'num_pg': num_pg}

        return return_value

    # Function to get Memory, CPU and Storage Capacity for a VM and how much is being used
    def get_usage_metrics_vm(self, vm_uuid):

        search_index = self.content.searchIndex
        # Look for VM
        vm = search_index.FindByUuid(uuid=vm_uuid, vmSearch=True, instanceUuid=True)

        #VMTools status
        vm_tools = vm.summary.guest.toolsRunningStatus
        if vm_tools == 'guestToolsRunning':
            vm_tools_status = 'running'
        else:
            vm_tools_status = 'not running'

        num_cpus = vm.config.hardware.numCPU
        ip_address = vm.guest.ipAddress
        num_nics = len(vm.guest.net)
        os_name = vm.guest.guestFamily[:-5]

        # Uptime - It is not used
        if vm.summary.runtime.bootTime:
            boot_time = vm.summary.runtime.bootTime
            today_date = datetime.utcnow()
            diff_time = today_date - boot_time.replace(tzinfo=None)
            uptime = diff_time.days
        else:
            uptime = None

        # Get Memory. Memory values are in MB . This is consumed memory (not active)
        total_memory = vm.config.hardware.memoryMB
        # Active Memory
        total_consumed_mem = vm.summary.quickStats.guestMemoryUsage

        # Get CPU. CPU values are in MHz
        total_cpu = vm.runtime.maxCpuUsage
        total_consumed_cpu = vm.summary.quickStats.overallCpuDemand

        # Convert Total and Consumed Memory from MB to GB
        total_memory = round(total_memory / 1024, 2)
        total_consumed_mem = round(total_consumed_mem / 1024, 2)
        # Calculate free memory
        free_memory = round(total_memory - total_consumed_mem, 2)

        free_cpu = total_cpu - total_consumed_cpu

        # Calculate Memory and CPU in %
        percent_consumed_mem = round((total_consumed_mem / total_memory) * 100, 1)
        percent_consumed_cpu = round((total_consumed_cpu / total_cpu) * 100, 1)

        # Get Virtual Disks space #

        total_disk_capacity = 0
        total_disk_free_space = 0
        total_disk_used_space = 0
        percent_storage_used = 0
        number_of_disks = 0
        disks_dict = {}
        disk_bool = False

        disks = vm.guest.disk
        if disks:
            disk_bool = True
            for disk in disks:
                number_of_disks += 1
                capacity = disk.capacity
                free_space = disk.freeSpace
                disk_path = disk.diskPath

                total_disk_capacity += capacity
                total_disk_free_space += free_space

                # Convert values from Bytes to GB
                used_space = capacity - free_space
                percent = round((used_space / capacity) * 100, 2)
                used_space_GB = round((((used_space / 1024) / 1024) / 1024), 2)

                # Short disk_path or name
                if len(disk_path) > 14:
                    disk_path = disk_path[0:13] + '...'

                disks_dict[disk_path] = {'percent': percent, 'used_space': used_space_GB}

            # Convert values from Bytes to GB
            total_disk_capacity = round((((total_disk_capacity / 1024) / 1024) / 1024), 2)
            total_disk_free_space = round((((total_disk_free_space / 1024) / 1024) / 1024), 2)
            total_disk_used_space = round(total_disk_capacity - total_disk_free_space, 2)
            percent_storage_used = round((total_disk_used_space / total_disk_capacity) * 100, 1)

        # GET VIRTUAL DISKS LATENCY
        metric = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'virtualDisk.totalWriteLatency.average')), 20, "*", vm)
        (times, disks_instances) = self.get_instance_values(metric)

        disks_latency = {}

        for disk_scsi, latency_values in disks_instances.items():
                        # Get average of latency_values
                        # Get the average for Max_Total_Latency
                        counter = 0
                        total = 0
                        latency_average_percent = 0
                        for val in latency_values:
                            counter += 1
                            total = total + val

                        latency_average = total / counter
                        # The total disk average latency should be below 20ms.
                        # In this case I am using 25 as the maximum for the line graph
                        if latency_average <= 25:
                            latency_average_percent = round((latency_average / 25) * 100)
                        else:
                            latency_average_percent = 100

                        disk_latency_values = {'percent': latency_average_percent, 'value': round(latency_average)}
                        disks_latency[disk_scsi] = disk_latency_values


        # REAL TIME METRICS #

        # GET ACTIVE MEMORY
        metric_active_memory = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'mem.active.average')), 20, "", vm)
        (memory_time, active_memory_values) = self.get_values(metric_active_memory)

        memory_time_values = list(memory_time)

        # GET BALLOONED MEMORY
        metric_balloned_memory = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'mem.vmmemctl.average')), 20, "", vm)
        (memory_time, ballooned_memory_values) = self.get_values(metric_balloned_memory)

        # GET SWAPPED MEMORY
        metric_swapped_memory = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'mem.swapped.average')), 20, "", vm)
        (memory_time, swapused_memory_values) = self.get_values(metric_swapped_memory)

        # GET CPU Usage (%)
        metric_cpu_usage = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'cpu.usage.average')), 20, "", vm)
        (cpu_time, cpu_usage_values) = self.get_values(metric_cpu_usage)

        # The metric in % needs to be divided by 100
        cpu_usage_values_percent = [x / 100 for x in cpu_usage_values]

        # GET CPU Readiness (%)
        metric_cpu_readiness = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'cpu.readiness.average')), 20, "", vm)
        (cpu_time, cpu_readiness_values) = self.get_values(metric_cpu_readiness)

        # The metric in % needs to be divided by 100
        cpu_readiness_values_percent = [x / 100 for x in cpu_readiness_values]

        # Get Network transmitted rate [KBps]
        network_transmitted_rate = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'net.transmitted.average')), 20, "", vm)
        (network_time, network_transmitted_rate_values) = self.get_values(network_transmitted_rate)

         # Get Network Received rate [KBps]
        network_received_rate = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'net.received.average')), 20, "", vm)
        (network_time, network_received_rate_values) = self.get_values(network_received_rate)

        # GET READ RATE [KBps]
        disk_read_rate = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'disk.read.average')), 20, "", vm)
        (disk_time, disks_read_rate_values) = self.get_network_values(disk_read_rate)

        # GET WRITE RATE [KBps]
        disk_write_rate = self.BuildQuery_RealTime(self.content, (self.StatCheck(self.perf_dict, 'disk.write.average')), 20, "", vm)
        (disk_time, disks_write_rate_values) = self.get_network_values(disk_write_rate)

        # Convert Values

        # Concert this list from datetime.datetime object to string
        memory_time_converted = [x.__str__() for x in memory_time_values]

        # Convert Active Memory from KB to GB
        temp_list_1 = [(x / 1024) / 1024 for x in active_memory_values]
        active_memory = list(temp_list_1)

        # Convert Ballooned Memory from KB to GB
        temp_list_2 = [(x / 1024) / 1024 for x in ballooned_memory_values]
        ballooned_memory = list(temp_list_2)

        # Convert Swapped Memory from KB to GB
        temp_list_3 = [(x / 1024) / 1024 for x in swapused_memory_values]
        swapused_memory = list(temp_list_3)

        return_value = {'total_memory': total_memory, 'total_consumed_mem': total_consumed_mem,
                        'free_memory': free_memory, 'percent_consumed_mem': percent_consumed_mem,
                        'total_cpu': total_cpu, 'total_consumed_cpu': total_consumed_cpu,
                        'free_cpu': free_cpu, 'percent_consumed_cpu': percent_consumed_cpu,
                        'total_storage': total_disk_capacity, 'percent_used_storage': percent_storage_used,
                        'free_storage': total_disk_free_space, 'used_storage': total_disk_used_space,
                        'disk_bool': disk_bool, 'disks_list_dict': disks_dict, 'disks_latency': disks_latency,
                        'number_of_disks': number_of_disks, 'memory_time': memory_time_converted,
                        'active_memory': active_memory, 'ballooned_memory': ballooned_memory,
                        'swapused_memory': swapused_memory, 'cpu_usage_percent': cpu_usage_values_percent,
                        'cpu_readiness_percent': cpu_readiness_values_percent,
                        'network_transmitted_rate': network_transmitted_rate_values,
                        'network_received_rate': network_received_rate_values,
                        'disks_read_rate': disks_read_rate_values, 'disks_write_rate': disks_write_rate_values,
                        'vm_tools_status': vm_tools_status, 'num_cpus': num_cpus, 'uptime': uptime,
                        'ip_address': ip_address, 'num_nics': num_nics, 'os_name': os_name}

        return return_value

    # Get number of VMs Powered On in the cluster
    def get_number_vms(self, cluster_name):

        datacenters = self.content.rootFolder.childEntity

        number_vms = 0

        for datacenter in datacenters:  # Iterate through DataCenters
            clusters = datacenter.hostFolder.childEntity
            for cluster in clusters:  # Iterate through the clusters in DC
                if cluster.name == cluster_name:
                    hosts = cluster.host
                    for host in hosts:  # Iterate through Hosts in the cluster
                        vms = host.vm
                        for vm in vms:
                            if vm.runtime.powerState != 'poweredOff':
                                number_vms += 1

        return number_vms

    def disconnect(self):
        Disconnect(self.c)
