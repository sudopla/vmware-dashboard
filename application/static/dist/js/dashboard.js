$(document).ready(function() {

    //alert(my_var.cluster_names[1]);
    //alert(json.cluster_names[0] + ' 2nd value - ' + json.cluster_mem_values[0])

    var colors = ['blue', 'purple', 'aero', 'red', 'green']

    cluster_names = []

    // Clusters Memory
    memory_data = []
    cluster_names_memory = []
    for (var i = 0; i < 5; i++) {
        //Data
        memory_data[i] = json.cluster_mem_values[i].value
        cluster_names_memory[i] = json.cluster_mem_values[i].cluster_name
        //alert(json.name[i])
        $('.cluster_memory').append('<tr>'+
            '<td><p><i class="fa fa-square '+colors[i]+'"></i>'+json.cluster_mem_values[i].cluster_name+'</p></td>'+
            '<td>'+json.cluster_mem_values[i].value+' GB</td>'+
          '</tr>')
    }

    init_chart_doughnut(memory_data, cluster_names_memory, 'cluster_memory', 'MEM');

    //Clusters CPU
    cpu_data = []
    cluster_names_cpu = []
    for (var i = 0; i < 5; i++) {
        //Data
        cpu_data[i] = json.cluster_cpu_values[i].value
        cluster_names_cpu[i] = json.cluster_cpu_values[i].cluster_name
        //alert(json.name[i])
        $('.cluster_cpu').append('<tr>'+
            '<td><p><i class="fa fa-square '+colors[i]+'"></i>'+json.cluster_cpu_values[i].cluster_name+'</p></td>'+
            '<td>'+json.cluster_cpu_values[i].value+' GHz</td>'+
          '</tr>')
    }

    init_chart_doughnut(cpu_data, cluster_names_cpu, 'cluster_cpu', 'CPU');

    //Clusters Storage
    storage_data = []
    cluster_names_storage = []
    for (var i = 0; i < 5; i++) {
        //Data
        storage_data[i] = json.cluster_storage_values[i].value
        cluster_names_storage[i] = json.cluster_storage_values[i].cluster_name
        //alert(json.name[i])
        $('.cluster_storage').append('<tr>'+
            '<td><p><i class="fa fa-square '+colors[i]+'"></i>'+json.cluster_storage_values[i].cluster_name+'</p></td>'+
            '<td>'+json.cluster_storage_values[i].value+' GB</td>'+
          '</tr>')
    }

    init_chart_doughnut(storage_data, cluster_names_storage, 'cluster_storage', 'Storage');

    //Clusters Network
    network_data = []
    cluster_names_network = []
    for (var i = 0; i < 5; i++) {
        //Values
        network_data[i] = json.cluster_network_values[i].value
        cluster_names_network[i] = json.cluster_network_values[i].cluster_name
        //alert(json.name[i])
        $('.cluster_network').append('<tr>'+
            '<td><p><i class="fa fa-square '+colors[i]+'"></i>'+json.cluster_network_values[i].cluster_name+'</p></td>'+
            '<td>'+json.cluster_network_values[i].value+' KBps</td>'+
          '</tr>')
    }

    init_chart_doughnut(network_data, cluster_names_network, 'cluster_network', 'Network');

});


function init_chart_doughnut(cluster_data, cluster_names, element, metric){

    var config = {
				type: 'doughnut',
				tooltipFillColor: "rgba(51, 51, 51, 0.55)",
				data: {
					labels: cluster_names,
					datasets: [{
						data: cluster_data,
						backgroundColor: [
							"#3498DB",
							"#9B59B6",
							"#9CC2CB",
							"#E74C3C",
							"#1ABB9C"
						],
						hoverBackgroundColor: [
							"#3498DB",
							"#9B59B6",
							"#9CC2CB",
							"#E74C3C",
							"#1ABB9C",
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
