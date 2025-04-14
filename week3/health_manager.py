import time
from health_monitor import HealthMonitor
from node_manager import NodeManager

class HealthManager:
    def __init__(self, node_manager):
        self.node_manager = node_manager
        self.health_monitor = HealthMonitor()
        self.failed_nodes = set()
        
    def get_node_health_status(self):
        """Return health status for all nodes"""
        nodes = self.node_manager.list_nodes()
        health_status = {}
        
        for node_id in nodes:
            # Check if node is in health monitor's records
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
                        # TODO: Implement recovery logic for pods on failed node
            else:
                health_status[node_id] = "Unknown"
                
        return health_status
    
    def register_node_with_health_monitor(self, node_id):
        """Register a new node with the health monitor"""
        self.health_monitor.receive_heartbeat(node_id)
        
    def get_health_monitor(self):
        """Return the health monitor instance"""
        return self.health_monitor