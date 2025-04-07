from pod_scheduler import PodScheduler
from health_monitor import HealthMonitor
from node import Node
import time

def main():
    # Initialize components
    health_monitor = HealthMonitor()
    scheduler = PodScheduler()
    
    # Create and register nodes
    nodes = {}
    for i in range(2):
        node_id = f"node-{i}"
        scheduler.register_node(node_id, cpu_capacity=100)
        nodes[node_id] = Node(node_id, cpu_capacity=100, health_monitor=health_monitor)
    
    # Launch a pod
    pod_id = "pod-1"
    cpu_request = 50
    assigned_node = scheduler.schedule_pod(pod_id, cpu_request)
    
    if assigned_node:
        print(f"Pod {pod_id} assigned to node {assigned_node}")
        nodes[assigned_node].add_pod(pod_id)
    else:
        print("Failed to schedule pod - insufficient resources")
    
    # Keep the system running for a while
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Cleanup
        for node in nodes.values():
            node.stop()
        health_monitor.stop()

if __name__ == "__main__":
    main()
