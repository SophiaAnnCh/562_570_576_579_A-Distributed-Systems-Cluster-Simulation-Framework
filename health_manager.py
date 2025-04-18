import time
from health_monitor import HealthMonitor
from node_manager import NodeManager

class HealthManager:
    def __init__(self, node_manager):
        self.node_manager = node_manager
        self.health_monitor = HealthMonitor()
        self.failed_nodes = set()
        self.pods_to_reschedule = {}  # Dictionary to track pods that need rescheduling
        self.pod_scheduler = None
        
    def set_pod_scheduler(self, pod_scheduler):
        """Set the pod scheduler reference"""
        self.pod_scheduler = pod_scheduler
        
    def get_node_health_status(self):
        """Return health status for all nodes"""
        nodes = self.node_manager.list_nodes()
        health_status = {}
        newly_failed_nodes = set()  # Track newly failed nodes in this check
        
        for node_id, node_info in nodes.items():
            container_id = node_info.get("container_id", "")
            
            # First check if the container is running (for real Docker containers)
            if not self.node_manager.is_container_running(container_id):
                health_status[node_id] = "Unhealthy"
                if node_id not in self.failed_nodes:
                    self.failed_nodes.add(node_id)
                    newly_failed_nodes.add(node_id)
                    print(f"Node {node_id} container no longer exists or is not running")
                continue
                
            # Then check heartbeat status
            if node_id in self.health_monitor.nodes_health:
                last_heartbeat = self.health_monitor.nodes_health[node_id]
                current_time = time.time()
                
                # Check if node is considered healthy (heartbeat within timeout)
                if current_time - last_heartbeat <= self.health_monitor.heartbeat_timeout:
                    health_status[node_id] = "Healthy"
                else:
                    health_status[node_id] = "Unhealthy"
                    # Add to failed nodes if not already tracked
                    if node_id not in self.failed_nodes:
                        self.failed_nodes.add(node_id)
                        newly_failed_nodes.add(node_id)
                        print(f"Node {node_id} missed heartbeat")
            else:
                health_status[node_id] = "Unknown"
        
        # Check for pods that need rescheduling from newly failed nodes
        if newly_failed_nodes:
            self._mark_pods_for_rescheduling(newly_failed_nodes)
                
        return health_status
    
    def _mark_pods_for_rescheduling(self, failed_node_ids):
        """Mark pods on failed nodes for rescheduling"""
        for node_id in failed_node_ids:
            if node_id in self.node_manager.nodes:
                pods = self.node_manager.nodes[node_id].get("pods", [])
                if pods:
                    print(f"Marking {len(pods)} pods from node {node_id} for rescheduling")
                    # Store pods with their CPU requests for rescheduling
                    node_pods_info = {}
                    for pod_id in pods:
                        # Get CPU request from pod_scheduler if available
                        cpu_request = 10  # Default CPU request
                        if self.pod_scheduler:
                            cpu_request = self.pod_scheduler.get_pod_cpu_request(pod_id)
                        node_pods_info[pod_id] = cpu_request
                    
                    self.pods_to_reschedule[node_id] = node_pods_info
    
    def get_pods_for_rescheduling(self):
        """Return pods that need to be rescheduled and clear the queue"""
        pods_to_reschedule = self.pods_to_reschedule.copy()
        self.pods_to_reschedule = {}  # Clear after retrieving
        return pods_to_reschedule
    
    def remove_node(self, node_id):
        """Remove a node to simulate failure"""
        if node_id in self.health_monitor.nodes_health:
            # Get pods from the node before removing
            if node_id in self.node_manager.nodes:
                pods = self.node_manager.nodes[node_id].get("pods", [])
                if pods:
                    # Mark pods for rescheduling
                    node_pods_info = {}
                    for pod_id in pods:
                        # Get CPU request from pod_scheduler if available
                        cpu_request = 10  # Default CPU request
                        if self.pod_scheduler:
                            cpu_request = self.pod_scheduler.get_pod_cpu_request(pod_id)
                        node_pods_info[pod_id] = cpu_request
                    
                    self.pods_to_reschedule[node_id] = node_pods_info
            
            # Remove node from health monitor
            with self.health_monitor.lock:
                if node_id in self.health_monitor.nodes_health:
                    del self.health_monitor.nodes_health[node_id]
            
            # Add to failed nodes list
            if node_id not in self.failed_nodes:
                self.failed_nodes.add(node_id)
                
            return True, f"Node {node_id} removed successfully"
        else:
            return False, f"Node {node_id} not found"
    
    def register_node_with_health_monitor(self, node_id):
        """Register a new node with the health monitor"""
        self.health_monitor.receive_heartbeat(node_id)
        
    def get_health_monitor(self):
        """Return the health monitor instance"""
        return self.health_monitor