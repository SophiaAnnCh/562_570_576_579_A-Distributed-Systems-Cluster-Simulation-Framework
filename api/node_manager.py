import docker

class NodeManager:
    def __init__(self):
        self.client = docker.from_env()
        self.nodes = {} 

    def add_node(self, node_id, cpu_capacity):
        """Launch a Docker container to represent a node"""
        container = self.client.containers.run(
            "ubuntu", 
            command="sleep infinity",
            detach=True,
            name=node_id
        )
        self.nodes[node_id] = {
            "container_id": container.id,
            "cpu_capacity": cpu_capacity,
            "pods": []
        }

    def list_nodes(self):
        return self.nodes
