class PodScheduler:
    def __init__(self):
        self.nodes = {}  # Dictionary to track nodes and their resource availability
        self.pod_assignments = {}  # Dictionary to track which node each pod is assigned to
        self.pod_requests = {}  # Dictionary to track CPU requests of each pod
        self.pending_pods = {}  # Dictionary to track pods waiting for available nodes
        
    def register_node(self, node_id, cpu_capacity):
        """Add a node to the scheduler"""
        self.nodes[node_id] = {
            "cpu_capacity": cpu_capacity,
            "cpu_available": cpu_capacity,
            "pods": []
        }
        
    def print_pod_list(self):
        """Print the list of pods for each node"""
        for node_id, node_info in self.nodes.items():
            print(f"Node {node_id} has pods: {node_info['pods']}")

    def schedule_pod(self, pod_id, cpu_request):
        """Schedule a pod on a node with available resources"""
        if pod_id in self.pod_assignments:
            print(f"Pod {pod_id} already scheduled on node {self.pod_assignments[pod_id]}")
            return self.pod_assignments[pod_id]
            
        # Find node with sufficient CPU
        best_fit_node = None
        min_cpu_remaining = float('inf')
        
        for node_id, node_info in self.nodes.items():
            if node_info["cpu_available"] >= cpu_request:
                # Use best-fit algorithm: choose node that will have minimal remaining CPU after scheduling
                cpu_after_allocation = node_info["cpu_available"] - cpu_request
                if cpu_after_allocation < min_cpu_remaining:
                    min_cpu_remaining = cpu_after_allocation
                    best_fit_node = node_id
        
        if best_fit_node:
            # Assign pod to node
            self.nodes[best_fit_node]["cpu_available"] -= cpu_request
            self.nodes[best_fit_node]["pods"].append(pod_id)
            self.pod_assignments[pod_id] = best_fit_node
            self.pod_requests[pod_id] = cpu_request
            # Remove from pending pods if it was there
            if pod_id in self.pending_pods:
                del self.pending_pods[pod_id]
            print(f"Scheduled pod {pod_id} on node {best_fit_node}, remaining CPU: {self.nodes[best_fit_node]['cpu_available']}")
            self.print_pod_list()  # Print the pod list after scheduling
            return best_fit_node
        else:
            # Store in pending pods list
            self.pending_pods[pod_id] = cpu_request
            print(f"Failed to schedule pod {pod_id}: No nodes with {cpu_request} CPU available. Added to pending pods queue.")
            return None
            
    def get_node_for_pod(self, pod_id):
        """Return the node a pod is scheduled on"""
        return self.pod_assignments.get(pod_id)
        
    def get_pod_cpu_request(self, pod_id):
        """Return the CPU request for a pod"""
        return self.pod_requests.get(pod_id, 10)  # Default to 10 if not found
        
    def unschedule_pod(self, pod_id):
        """Remove a pod from its node"""
        if pod_id not in self.pod_assignments:
            return False
            
        node_id = self.pod_assignments[pod_id]
        
        if node_id in self.nodes:
            cpu_request = self.pod_requests.get(pod_id, 10)
            
            # Free up resources
            self.nodes[node_id]["cpu_available"] += cpu_request
            
            # Remove pod from node
            if pod_id in self.nodes[node_id]["pods"]:
                self.nodes[node_id]["pods"].remove(pod_id)
        
        # Remove from tracking dictionaries
        del self.pod_assignments[pod_id]
        if pod_id in self.pod_requests:
            del self.pod_requests[pod_id]
            
        return True
        
    def reschedule_pods(self, pods_dict):
        """Reschedule pods from failed nodes
        
        Args:
            pods_dict: Dictionary where keys are node_ids and values are dictionaries 
                      mapping pod_ids to their CPU requests
        
        Returns:
            Dictionary mapping pod_ids to their new nodes (or None if couldn't reschedule)
        """
        results = {}
        
        if not pods_dict:
            print("No pods to reschedule")
            return results
            
        print(f"Rescheduling pods from {len(pods_dict)} nodes: {', '.join(pods_dict.keys())}")
        
        for node_id, pods in pods_dict.items():
            print(f"Rescheduling {len(pods)} pods from node {node_id}: {list(pods.keys())}")
            
            for pod_id, cpu_request in pods.items():
                # Check if pod is already assigned to a new node (avoid duplicate rescheduling)
                current_node = self.get_node_for_pod(pod_id)
                if current_node and current_node != node_id and current_node in self.nodes:
                    print(f"Pod {pod_id} already rescheduled to node {current_node}")
                    results[pod_id] = {
                        "old_node": node_id,
                        "new_node": current_node,
                        "status": "already_rescheduled"
                    }
                    continue
                
                # Debug: Print the current state of nodes before rescheduling
                print(f"Current state of nodes: {self.nodes}")
                
                # Debug: Print the pods being unscheduled
                print(f"Unscheduling pod {pod_id} from node {node_id}")
                
                # Remove old assignment if it exists in our records
                self.unschedule_pod(pod_id)
                
                # Try to find a new node for this pod
                available_nodes = [n for n in self.nodes.keys() if self.nodes[n]["cpu_available"] >= cpu_request]
                print(f"Finding new node for pod {pod_id} (CPU: {cpu_request}). Available nodes: {available_nodes}")
                
                # Try to reschedule the pod
                new_node = self.schedule_pod(pod_id, cpu_request)
                
                status = "rescheduled" if new_node else "failed"
                print(f"Pod {pod_id} rescheduling {status}" + (f" to {new_node}" if new_node else ""))
                
                results[pod_id] = {
                    "old_node": node_id,
                    "new_node": new_node,
                    "status": status
                }
                
        return results
        
    def schedule_pending_pods(self):
        """Try to schedule any pending pods"""
        if not self.pending_pods:
            return {}
            
        print(f"Attempting to schedule {len(self.pending_pods)} pending pods")
        results = {}
        
        # Create a copy to iterate over, as we'll be modifying the original during iteration
        pending_pods_copy = self.pending_pods.copy()
        
        for pod_id, cpu_request in pending_pods_copy.items():
            assigned_node = self.schedule_pod(pod_id, cpu_request)
            
            if assigned_node:
                print(f"Successfully scheduled pending pod {pod_id} on node {assigned_node}")
                results[pod_id] = {
                    "node": assigned_node,
                    "status": "scheduled"
                }
            else:
                # Pod is still pending
                results[pod_id] = {
                    "node": None,
                    "status": "still_pending"
                }
                
        return results