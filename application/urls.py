from django.conf.urls import url
from application import views

#Password for admnin - VMware123!

urlpatterns = [
    url(r'^$', views.HomePageView.as_view(), name='index'),
    url(r'^dashboard_graphs/(?P<interval>.*)$', views.DashboardGraphsView.as_view(), name='dashboard_graphs'),
    url(r'^cluster/(?P<cluster>.*)/(?P<interval>.*)$', views.ClusterPageView.as_view(), name='cluster'),
    url(r'^cluster_graphs/(?P<cluster>.*)/(?P<interval>.*)$', views.ClusterGraphsView.as_view(), name='cluster_graphs'),
    url(r'^top_vms_cluster/memory/(?P<cluster>.*)$', views.get_top_vms_cluster_memory, name='top_vms_cluster_memory'),
    url(r'^top_vms_cluster/cpu/(?P<cluster>.*)$', views.get_top_vms_cluster_cpu, name='top_vms_cluster_cpu'),
    url(r'^top_hosts_cluster/memory/(?P<cluster>.*)$', views.get_top_hosts_cluster_memory, name='top_hosts_cluster_memory'),
    url(r'^top_hosts_cluster/cpu/(?P<cluster>.*)$', views.get_top_hosts_cluster_memory, name='top_hosts_cluster_cpu'),
    url(r'^host/(?P<host>.*)/(?P<interval>.*)$', views.HostPageView.as_view(), name='host'),
    url(r'^host_graphs/(?P<host>.*)/(?P<interval>.*)$', views.HostGraphsView.as_view(), name='host_graphs'),
    url(r'^vm/(?P<uuid>.*)/(?P<interval>.*)$', views.VmPageView.as_view(), name='vm'),
    url(r'^vms_graphs/(?P<uuid>.*)/(?P<interval>.*)$', views.VmGraphsView.as_view(), name='vm_graphs'),
]

