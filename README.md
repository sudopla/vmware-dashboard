VMware Dashboard
------------------

This application will help you understand how you are using the resources in your VMware infrastructure and identity performance issues. 

 The application was built with Django and uses the libraries [plotly](https://plot.ly/graphing-libraries/) for the graphs and [pyVmomi](https://github.com/vmware/pyvmomi) to connect to the vCenter Server API. 
 
 Before running the application, please go to the file [perfdata.py](application/lib/perfdata.py) line #26 and write the credentials for a vCenter read-only user. 
 ```
 self.c = SmartConnect(host="vcenter_IP", user="user@vsphere.local", pwd="Password", sslContext=s)
 ```
 
 When you first load the application you will have a general view of the resources in your infrastrcuture. 

 ![datacenter](img/datacenter_1.PNG)

You can see the resources that are using more resources in your infrastructure 

![datacenter](img/datacenter_2.PNG)

Historical metrics reports

![datacenter](img/datacenter_3.PNG)
![datacenter](img/datacenter_4.PNG)

You can then go to a specific cluster

![cluster](img/cluster_1.PNG)

In the real time graphs you can see if there are performance problems in the cluster

![cluster](img/cluster_2.PNG)

VMs using more resources in the cluster

![cluster](img/cluster_3.PNG)

Historical metrics and trends in the cluster

![cluster](img/cluster_4.PNG)

In the ESXi hosts

![cluster](img/esxi_1.PNG)

Trends

![cluster](img/esxi_2.PNG)

VMware View

![vm](img/vm_1.PNG)

![vm](img/vm_2.PNG)

![vm](img/vm_3.PNG)
