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
            success = True
            message = f"simulated-{node_id}"
        else:
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
                success = True
                message = container.id
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
                success = True
                message = f"simulated-{node_id} (Docker error: {str(e)[:50]}...)"

        return success, message

    def list_nodes(self):
        return self.nodes
        
    def is_container_running(self, container_id):
        """Check if a Docker container is still running"""
        # If Docker is not available or the ID starts with "sim-", it's a simulated node
        if not self.docker_available or container_id.startswith("sim-"):
            return True
            
        try:
            # Try to get the container and check its status
            container = self.client.containers.get(container_id)
            return container.status == "running"
        except docker.errors.NotFound:
            # Container doesn't exist anymore
            return False
        except Exception as e:
            print(f"Error checking container status: {e}")
            # Assume container is down if we can't check
            return False
            
    def remove_node(self, node_id):
        """Remove a node from the manager and stop its container"""
        if node_id not in self.nodes:
            return False, f"Node {node_id} does not exist"
            
        container_id = self.nodes[node_id]["container_id"]
        
        # If using Docker and not a simulated container
        if self.docker_available and not container_id.startswith("sim-"):
            try:
                # Try to stop and remove the container
                container = self.client.containers.get(container_id)
                container.stop()
                container.remove()
                print(f"Stopped and removed container for node {node_id}")
            except docker.errors.NotFound:
                # Container already gone
                pass
            except Exception as e:
                print(f"Error removing container: {e}")
        
        # Remove node from internal state regardless of Docker operations
        del self.nodes[node_id]
        success = True
        message = f"Node {node_id} removed successfully"

        return success, message