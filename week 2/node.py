import time
from threading import Thread

class Node:
    def __init__(self, node_id, cpu_capacity, health_monitor):
        self.node_id = node_id
        self.cpu_capacity = cpu_capacity
        self.pods = []
        self.health_monitor = health_monitor
        self.running = True
        
        # Start heartbeat thread
        self.heartbeat_thread = Thread(target=self._send_heartbeat)
        self.heartbeat_thread.start()
    
    def _send_heartbeat(self):
        while self.running:
            self.health_monitor.receive_heartbeat(self.node_id)
            time.sleep(5)  # Send heartbeat every 5 seconds
    
    def add_pod(self, pod_id):
        self.pods.append(pod_id)
    
    def stop(self):
        self.running = False
        self.heartbeat_thread.join()