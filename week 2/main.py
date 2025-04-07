from pod_scheduler import PodScheduler
from health_monitor import HealthMonitor
from node import Node
import time

def print_cluster_status(nodes, scheduler):
    print("\n=== Cluster Status ===")
    for node_id, node_info in scheduler.nodes.items():
        print(f"\nNode: {node_id}")
        print(f"├── CPU Capacity: 100")
        print(f"├── CPU Used: {100 - node_info['cpu_available']}")
        print(f"├── CPU Available: {node_info['cpu_available']}")
        print(f"└── Pods: {node_info['pods']}")

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
    
    print("\n=== Initial Cluster Status ===")
    print_cluster_status(nodes, scheduler)
    
    # Launch a pod
    pod_id = "pod-1"
    cpu_request = 50
    print(f"\n=== Scheduling Pod ===")
    print(f"Request: Pod {pod_id} with CPU requirement: {cpu_request}")
    
    assigned_node = scheduler.schedule_pod(pod_id, cpu_request)
    
    if assigned_node:
        print(f"\n✓ Success: Pod {pod_id} assigned to node {assigned_node}")
        nodes[assigned_node].add_pod(pod_id)
        print_cluster_status(nodes, scheduler)
    else:
        print(f"\n✗ Failed: Could not schedule pod {pod_id} - insufficient resources")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n=== Shutting down cluster ===")
        for node in nodes.values():
            node.stop()
        health_monitor.stop()

if __name__ == "__main__":
    main()
