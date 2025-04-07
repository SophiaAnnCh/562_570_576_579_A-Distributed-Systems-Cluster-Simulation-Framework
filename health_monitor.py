import time
from threading import Thread, Lock

class HealthMonitor:
    def __init__(self):
        self.nodes_health = {}  # {node_id: last_heartbeat_time}
        self.heartbeat_timeout = 10  # seconds
        self.lock = Lock()
        self.running = True
        
        # Start monitoring thread
        self.monitor_thread = Thread(target=self._monitor_nodes)
        self.monitor_thread.start()
    
    def receive_heartbeat(self, node_id):
        with self.lock:
            self.nodes_health[node_id] = time.time()
    
    def _monitor_nodes(self):
        while self.running:
            with self.lock:
                current_time = time.time()
                failed_nodes = []
                
                for node_id, last_heartbeat in self.nodes_health.items():
                    if current_time - last_heartbeat > self.heartbeat_timeout:
                        failed_nodes.append(node_id)
                
                # Handle failed nodes
                for node_id in failed_nodes:
                    print(f"Node {node_id} has failed!")
                    # Implement recovery logic here
            
            time.sleep(5)  # Check every 5 seconds
    
    def stop(self):
        self.running = False
        self.monitor_thread.join()