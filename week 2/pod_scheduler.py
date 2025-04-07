class PodScheduler:
    def __init__(self):
        self.nodes = {}  # Dictionary to store node information {node_id: {cpu_available: int, pods: []}}
    
    def register_node(self, node_id, cpu_capacity):
        self.nodes[node_id] = {
            'cpu_available': cpu_capacity,
            'pods': []
        }
    
    def schedule_pod(self, pod_id, cpu_request):
        # Simple scheduling algorithm - assign to node with most available CPU
        selected_node = None
        max_cpu_available = -1
        
        for node_id, node_info in self.nodes.items():
            if node_info['cpu_available'] >= cpu_request:
                if node_info['cpu_available'] > max_cpu_available:
                    max_cpu_available = node_info['cpu_available']
                    selected_node = node_id
        
        if selected_node:
            # Assign pod to node
            self.nodes[selected_node]['pods'].append(pod_id)
            self.nodes[selected_node]['cpu_available'] -= cpu_request
            return selected_node
        
        return None  # No suitable node found