from pod_scheduler import PodScheduler
from node_manager import NodeManager
from health_manager import HealthManager

class Scheduler:
    def __init__(self):
        self.node_manager = NodeManager()
        self.health_manager = HealthManager(self.node_manager)
        self.pod_scheduler = PodScheduler()
        
    def add_node(self, node_id, cpu_capacity):
        """Add a new node to the cluster"""
        # Add node to node manager (creates Docker container)
        success, message = self.node_manager.add_node(node_id, cpu_capacity)
        
        if not success:
            return False, message
        
        # Register node with health monitoring
        self.health_manager.register_node_with_health_monitor(node_id)
        
        # Register node with pod scheduler
        self.pod_scheduler.register_node(node_id, cpu_capacity)
        
        return True, f"Node {node_id} added successfully"
        
    def schedule_pod(self, pod_id, cpu_request):
        """Schedule a pod on an available node"""
        # Get node health status
        health_status = self.health_manager.get_node_health_status()
        
        # Schedule pod
        assigned_node = self.pod_scheduler.schedule_pod(pod_id, cpu_request)
        
        # If assigned node is not healthy, return None
        if assigned_node and assigned_node in health_status and health_status[assigned_node] != "Healthy":
            return None
            
        return assigned_node
        
    def get_cluster_status(self):
        """Get comprehensive cluster status"""
        nodes = self.node_manager.list_nodes()
        health_status = self.health_manager.get_node_health_status()
        scheduler_nodes = self.pod_scheduler.nodes
        
        cluster_status = {}
        
        for node_id, node_info in nodes.items():
            cluster_status[node_id] = {
                "container_id": node_info["container_id"],
                "cpu_capacity": node_info["cpu_capacity"],
                "health": health_status.get(node_id, "Unknown"),
                "cpu_available": scheduler_nodes.get(node_id, {}).get("cpu_available", 0),
                "pods": scheduler_nodes.get(node_id, {}).get("pods", [])
            }
            
        return cluster_status