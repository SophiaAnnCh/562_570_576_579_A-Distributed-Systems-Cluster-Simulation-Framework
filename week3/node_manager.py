import docker
import traceback

class NodeManager:
    def __init__(self):
        self.nodes = {}
        try:
            self.client = docker.from_env()
            # Test the connection
            self.client.ping()
            self.docker_available = True
        except Exception as e:
            print(f"Docker client initialization failed: {e}")
            self.docker_available = False
            self.client = None

    def add_node(self, node_id, cpu_capacity):
        """Launch a Docker container to represent a node or simulate if Docker is unavailable"""
        # Check if node already exists
        if node_id in self.nodes:
            return False, f"Node {node_id} already exists"
            
        if not self.docker_available:
            # Simulate node creation instead of using Docker
            print(f"Docker unavailable. Simulating node: {node_id}")
            self.nodes[node_id] = {
                "container_id": f"sim-container-{node_id}",
                "cpu_capacity": cpu_capacity,
                "cpu_available": cpu_capacity,
                "pods": []
            }
            return True, f"simulated-{node_id}"
        
        # Docker is available, try to create the container
        try:
            container = self.client.containers.run(
                "ubuntu", 
                command="sleep infinity",
                detach=True,
                name=f"kube_sim_{node_id}",
                remove=True
            )
            self.nodes[node_id] = {
                "container_id": container.id,
                "cpu_capacity": cpu_capacity,
                "cpu_available": cpu_capacity,
                "pods": []
            }
            return True, container.id
        except Exception as e:
            print(f"Error creating Docker container: {e}")
            print(traceback.format_exc())
            
            # Fallback to simulation
            self.nodes[node_id] = {
                "container_id": f"sim-container-{node_id}",
                "cpu_capacity": cpu_capacity,
                "cpu_available": cpu_capacity,
                "pods": []
            }
            return True, f"simulated-{node_id} (Docker error: {str(e)[:50]}...)"

    def list_nodes(self):
        return self.nodes