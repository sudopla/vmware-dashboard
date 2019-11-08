$(document).ready(function() {

    var colors = ['blue', 'green', 'purple', 'aero', 'red']

     $.ajax({
                // 'name' is a js variable that is coming from main.js file
                url: '/top_vms_cluster/memory/'+name,
                dataType: 'json',
                success: function (json) {
                  if (json.name) {

                    init_chart_doughnut(json, 'top_vms_cluster_memory');

                    for (var i = 0; i < json.name.length; i++) {
                        //alert(json.name[i])
                        $('.top_vms_cluster_memory').append('<tr>'+
                            '<td><p><i class="fa fa-square '+colors[i]+'"></i>'+json.name[i]+'</p></td>'+
                            '<td>'+json.values[i]+' MB</td>'+
                          '</tr>')
                    }
                  }

                }
            });

     $.ajax({
                url: '/top_vms_cluster/cpu/'+name,
                dataType: 'json',
                success: function (json, ) {
                  if (json.name) {

                    init_chart_doughnut(json, 'top_vms_cluster_cpu');

                    for (var i = 0; i < json.name.length; i++) {
                        //alert(json.name[i])
                        $('.top_vms_cluster_cpu').append('<tr>'+
                            '<td><p><i class="fa fa-square '+colors[i]+'"></i>'+json.name[i]+'</p></td>'+
                            '<td>'+json.values[i]+' MHz</td>'+
                          '</tr>')
                    }
                  }

                }
            });

     $.ajax({
                url: '/top_hosts_cluster/memory/'+name,
                dataType: 'json',
                success: function (json, ) {
                  if (json.name) {

                    init_chart_doughnut(json, 'top_hosts_cluster_memory');

                    for (var i = 0; i < json.name.length; i++) {
                        //alert(json.name[i])
                        $('.top_hosts_cluster_memory').append('<tr>'+
                            '<td><p><i class="fa fa-square '+colors[i]+'"></i>'+json.name[i]+'</p></td>'+
                            '<td>'+json.values[i]+' MHz</td>'+
                          '</tr>')
                    }
                  }

                }
            });

    $.ajax({
                url: '/top_hosts_cluster/cpu/'+name,
                dataType: 'json',
                success: function (json, ) {
                  if (json.name) {

                    init_chart_doughnut(json, 'top_hosts_cluster_cpu');

                    for (var i = 0; i < json.name.length; i++) {
                        //alert(json.name[i])
                        $('.top_hosts_cluster_cpu').append('<tr>'+
                            '<td><p><i class="fa fa-square '+colors[i]+'"></i>'+json.name[i]+'</p></td>'+
                            '<td>'+json.values[i]+' MHz</td>'+
                          '</tr>')
                    }
                  }

                }
            });


    //Real Time Graphs
    //Memory
    MEMORY = document.getElementById('realtime_graph_memory');

    time = json_memory.time
    values_active_memory= json_memory.active_memory
    values_ballooned_memory = json_memory.ballooned_memory
    values_swapused_memory = json_memory.swapused_memory

    //Convert time strings to JavaScript Date objects
    time.forEach(function(part, index) {
        time[index] = new Date(part);
    });

    var trace1 = {
        x: time,
	    y: values_active_memory,
	    name: 'Active'
    }

    var trace2 = {
        x: time,
	    y: values_ballooned_memory,
	    name: 'Ballooned'
    }

    var trace3 = {
        x: time,
	    y: values_swapused_memory,
	    name: 'Swap'
    }

    var data = [trace1, trace2, trace3]

    var layout = {
        legend: {
            orientation: 'h'
        },
        showlegend: true,
        height: 250,
        margin: { t: 0, l: 45, r: 30 },
        xaxis: {
            showgrid: false,
            autorange: true,
            hoverformat: '%H:%M:%S',
            tickformat: '%H:%M',
            zeroline: false
        },
        yaxis: {
            title: 'GB',
            rangemode: 'tozero',
            showline: false
        }
    };

	Plotly.newPlot(MEMORY, data, layout, {displayModeBar: false})

	//CPU
	CPU = document.getElementById('realtime_graph_cpu');

    //Use the same time from the Memory graphs
    values_cpu_usage= json_cpu.cpu_usage_percent
    values_cpu_readiness= json_cpu.cpu_readiness_percent

    var trace1_cpu = {
        x: time,
	    y: values_cpu_usage,
	    name: 'CPU Usage'
    }
    var trace2_cpu = {
        x: time,
	    y: values_ballooned_memory,
	    name: 'CPU Readiness'
    }
    var data_cpu = [trace1_cpu, trace2_cpu]

    var layout_cpu = {
        legend: {
            orientation: 'h'
        },
        showlegend: true,
        height: 250,
        margin: { t: 0, l: 45, r: 30 },
        xaxis: {
            showgrid: false,
            autorange: true,
            hoverformat: '%H:%M:%S',
            tickformat: '%H:%M',
            zeroline: false
        },
        yaxis: {
            title: '%',
            rangemode: 'tozero',
            showline: false
        }
    };

	Plotly.newPlot(CPU, data_cpu, layout_cpu, {displayModeBar: false})

    //NETWORK
    NETWORK = document.getElementById('realtime_graph_network');

    //Use the same time from the Memory graphs
    values_network_transmitted= json_network.network_transmitted_rate
    values_network_received= json_network.network_received_rate

    var trace1_network = {
        x: time,
	    y: values_network_transmitted,
	    name: 'Data Transmit'
    }
    var trace2_network = {
        x: time,
	    y: values_network_received,
	    name: 'Data Received'
    }

    var data_network = [trace1_network, trace2_network]

    var layout_network = {
        legend: {
            orientation: 'h'
        },
        showlegend: true,
        height: 250,
        margin: { t: 0, l: 45, r: 30 },
        xaxis: {
            showgrid: false,
            autorange: true,
            hoverformat: '%H:%M:%S',
            tickformat: '%H:%M',
            zeroline: false
        },
        yaxis: {
            title: 'KBps',
            rangemode: 'tozero',
            showline: false
        }
    };

	Plotly.newPlot(NETWORK, data_network, layout_network, {displayModeBar: false})


    //DISKS
    DISK = document.getElementById('realtime_graph_disk');

    //Use the same time from the Memory graphs
    values_disks_read_rate = json_disks.disks_read_rate
    values_disks_write_rate = json_disks.disks_write_rate

    var trace1_disks = {
        x: time,
	    y: values_disks_read_rate,
	    name: 'Read Rate'
    }
    var trace2_disks = {
        x: time,
	    y: values_disks_write_rate,
	    name: 'Write Rate'
    }

    var data_disks = [trace1_disks, trace2_disks]

    var layout_disks = {
        legend: {
            orientation: 'h'
        },
        showlegend: true,
        height: 250,
        margin: { t: 0, l: 45, r: 30 },
        xaxis: {
            showgrid: false,
            autorange: true,
            hoverformat: '%H:%M:%S',
            tickformat: '%H:%M',
            zeroline: false
        },
        yaxis: {
            title: 'KBps',
            rangemode: 'tozero',
            showline: false
        }
    };

	Plotly.newPlot(DISK, data_disks, layout_disks, {displayModeBar: false})

});


function init_chart_doughnut(json, element){

    var config = {
				type: 'doughnut',
				tooltipFillColor: "rgba(51, 51, 51, 0.55)",
				data: {
					labels: [
						json.name[0],
						json.name[1],
						json.name[2],
						json.name[3],
						json.name[4]
					],
					datasets: [{
						data: [json.values[0], json.values[1], json.values[2], json.values[3], json.values[4]],
						backgroundColor: [
							"#3498DB",
							"#1ABB9C",
							"#9B59B6",
							"#9CC2CB",
							"#E74C3C"
						],
						hoverBackgroundColor: [
							"#3498DB",
							"#1ABB9C",
							"#9B59B6",
							"#9CC2CB",
							"#E74C3C"
						]
					}]
				},
				options: {
					legend: false,
					responsive: false
				}
			}


	var ctx = $('#' + element);
    var myChart = new Chart(ctx, config);

}
