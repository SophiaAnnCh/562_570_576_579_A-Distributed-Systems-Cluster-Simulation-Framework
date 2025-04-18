from pod_scheduler import PodScheduler
from node_manager import NodeManager
from health_manager import HealthManager

class Scheduler:
    def __init__(self):
        self.node_manager = NodeManager()
        self.pod_scheduler = PodScheduler()
        # Initialize health_manager with only node_manager
        self.health_manager = HealthManager(self.node_manager)
        # Then set the pod_scheduler reference
        self.health_manager.set_pod_scheduler(self.pod_scheduler)
        self.rescheduled_pods = {}  # Track recently rescheduled pods
        
    def add_node(self, node_id, cpu_capacity):
        """Add a new node to the cluster"""
        # Add node to node manager (creates Docker container)
        success, message = self.node_manager.add_node(node_id, cpu_capacity)
        
        if not success:
            return False, message
        
        # Register node with pod scheduler
        self.pod_scheduler.register_node(node_id, cpu_capacity)
        
        # Try to schedule any pending pods
        scheduled_pending = self.pod_scheduler.schedule_pending_pods()
        
        # Register node with health monitoring
        self.health_manager.register_node_with_health_monitor(node_id)
        
        return True, f"Node {node_id} added successfully"
    
    def remove_node(self, node_id):
        """Remove a node from the cluster"""
        # First, get the pods that were on this node for proper rescheduling
        node_pods = []
        if node_id in self.pod_scheduler.nodes:
            node_pods = self.pod_scheduler.nodes[node_id].get("pods", []).copy()
            # Remove the node from pod_scheduler BEFORE rescheduling
            del self.pod_scheduler.nodes[node_id]

        # Add these pods to the rescheduling list
        if node_pods:
            node_pods_info = {}
            for pod_id in node_pods:
                cpu_request = self.pod_scheduler.get_pod_cpu_request(pod_id)
                node_pods_info[pod_id] = cpu_request
            self.health_manager.pods_to_reschedule[node_id] = node_pods_info

        # Print the rescheduling list
        print(f"Rescheduling list for node {node_id}: {self.health_manager.pods_to_reschedule.get(node_id, {})}")

        # Clean up pod assignments for the deleted node
        for pod_id in node_pods:
            if pod_id in self.pod_scheduler.pod_assignments and self.pod_scheduler.pod_assignments[pod_id] == node_id:
                # Unschedule the pod from the failed node
                self.pod_scheduler.unschedule_pod(pod_id)

        # Remove node from health manager (which will mark pods for rescheduling)
        self.health_manager.remove_node(node_id)

        # Remove node from node manager
        success, message = self.node_manager.remove_node(node_id)

        # Process any pods that need rescheduling after cleanup
        self.process_pod_rescheduling()

        return success, message
        
    def schedule_pod(self, pod_id, cpu_request):
        """Schedule a pod on an available node"""
        # Get node health status
        health_status = self.health_manager.get_node_health_status()
        
        # First check if pod is already assigned to a node that no longer exists
        if pod_id in self.pod_scheduler.pod_assignments:
            node_id = self.pod_scheduler.pod_assignments[pod_id]
            if node_id not in self.node_manager.nodes:
                # Node doesn't exist anymore, unschedule the pod
                print(f"Pod {pod_id} was scheduled on node {node_id} which no longer exists. Unscheduling.")
                self.pod_scheduler.unschedule_pod(pod_id)
        
        # Schedule pod
        assigned_node = self.pod_scheduler.schedule_pod(pod_id, cpu_request)
        
        # If assigned node is not healthy, return None
        if assigned_node and assigned_node in health_status and health_status[assigned_node] != "Healthy":
            return None
            
        return assigned_node
    
    def process_pod_rescheduling(self):
        """Check for and reschedule pods from failed nodes"""
        # Get pods that need rescheduling from the health manager
        pods_to_reschedule = self.health_manager.get_pods_for_rescheduling()
        
        if not pods_to_reschedule:
            return {}
        
        # Use pod scheduler to reschedule pods
        results = self.pod_scheduler.reschedule_pods(pods_to_reschedule)
        
        # Update rescheduled_pods with results
        self.rescheduled_pods = results
        
        return results
    
    def check_and_repair_cluster(self):
        """Check cluster health and reschedule pods if needed"""
        # Update node health status (this will detect newly failed nodes)
        health_status = self.health_manager.get_node_health_status()
        
        # Find any nodes that are unhealthy and force rescheduling of their pods
        for node_id, status in health_status.items():
            if status == "Unhealthy" and node_id in self.pod_scheduler.nodes:
                # Get pods on this node
                pods = self.pod_scheduler.nodes[node_id].get("pods", []).copy()
                
                # If node has pods, force their rescheduling
                if pods:
                    print(f"Node {node_id} is unhealthy, forcing rescheduling of {len(pods)} pods")
                    # Mark these pods for rescheduling
                    node_pods_info = {}
                    for pod_id in pods:
                        cpu_request = self.pod_scheduler.get_pod_cpu_request(pod_id)
                        node_pods_info[pod_id] = cpu_request
                        
                    # Add to health manager's reschedule queue
                    self.health_manager.pods_to_reschedule[node_id] = node_pods_info
        
        # Process any pods that need to be rescheduled
        return self.process_pod_rescheduling()
        
    def get_rescheduled_pods(self):
        """Get information about recently rescheduled pods and clear the list"""
        rescheduled = self.rescheduled_pods.copy()
        self.rescheduled_pods = {}
        return rescheduled
        
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