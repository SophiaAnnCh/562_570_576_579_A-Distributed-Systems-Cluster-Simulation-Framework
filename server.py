from flask import Flask, request, jsonify, render_template
from scheduler import Scheduler
from node import Node
import os
import threading
import time

app = Flask(__name__, template_folder=os.path.abspath('templates'))
scheduler = Scheduler()

# Store Node objects that send heartbeats
node_objects = {}

# Global flag for repair thread
repair_thread_running = True

def update_node_objects_with_pod(pod_id, node_id):
    """Update Node objects to reflect pod assignment"""
    # Remove pod from all nodes first
    for node in node_objects.values():
        node.remove_pod(pod_id)
    
    # Add pod to the assigned node
    if node_id and node_id in node_objects:
        node_objects[node_id].add_pod(pod_id)
        print(f"Updated Node object: Pod {pod_id} added to node {node_id}")

def cluster_repair_thread():
    """Background thread to check cluster health and reschedule pods"""
    global repair_thread_running
    
    while repair_thread_running:
        try:
            # Check health and reschedule pods if needed
            rescheduled_pods = scheduler.check_and_repair_cluster()
            
            # Update node objects with rescheduled pods
            for pod_id, pod_info in rescheduled_pods.items():
                new_node = pod_info.get('new_node')
                if new_node:
                    update_node_objects_with_pod(pod_id, new_node)
                    print(f"Repair thread: Pod {pod_id} rescheduled to node {new_node}")
        except Exception as e:
            print(f"Error in repair thread: {e}")
        
        # Sleep for a while
        time.sleep(5)  # Check every 5 seconds

# Start the repair thread
repair_thread = threading.Thread(target=cluster_repair_thread, daemon=True)
repair_thread.start()

@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.json
    node_id = data.get('node_id')
    cpu_capacity = data.get('cpu_capacity', 100)  # Default 100 CPU
    if not node_id:
        return jsonify({"error": "node_id is required"}), 400

    success, message = scheduler.add_node(node_id, cpu_capacity)
    if success:
        # Create a Node object that will send heartbeats to the health monitor
        health_monitor = scheduler.health_manager.get_health_monitor()
        node_objects[node_id] = Node(node_id, cpu_capacity=cpu_capacity, health_monitor=health_monitor)
        return jsonify({"message": f"Node {node_id} added with {cpu_capacity} CPU"}), 201
    else:
        return jsonify({"error": message}), 400

@app.route('/list_nodes', methods=['GET'])
def list_nodes():
    cluster_status = scheduler.get_cluster_status()
    return jsonify(cluster_status)

@app.route('/schedule_pod', methods=['POST'])
def schedule_pod():
    data = request.json
    pod_id = data.get('pod_id')
    cpu_request = data.get('cpu_request', 10)  # Default 10 CPU
    
    if not pod_id:
        return jsonify({"error": "pod_id is required"}), 400
        
    assigned_node = scheduler.schedule_pod(pod_id, cpu_request)
    
    if assigned_node:
        # Update node objects with this pod assignment
        update_node_objects_with_pod(pod_id, assigned_node)
            
        return jsonify({
            "message": f"Pod {pod_id} scheduled on node {assigned_node}",
            "node": assigned_node
        }), 201
    else:
        return jsonify({"error": "Could not schedule pod - insufficient resources or unhealthy nodes"}), 400

@app.route('/remove_node', methods=['POST'])
def remove_node():
    data = request.json
    node_id = data.get('node_id')
    
    if not node_id:
        return jsonify({"error": "node_id is required"}), 400
        
    # Stop node heartbeat threads if node exists in object list
    if node_id in node_objects:
        node_objects[node_id].stop()
        del node_objects[node_id]
    
    # Remove node from scheduler components (this triggers pod rescheduling)
    success, message = scheduler.remove_node(node_id)
    
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400

@app.route('/get_rescheduled_pods', methods=['GET'])
def get_rescheduled_pods():
    """Get information about recently rescheduled pods"""
    rescheduled_pods = scheduler.get_rescheduled_pods()
    
    # Update node objects with rescheduled pods
    for pod_id, pod_info in rescheduled_pods.items():
        new_node = pod_info.get('new_node')
        if new_node:
            update_node_objects_with_pod(pod_id, new_node)
    
    return jsonify({
        "rescheduled_pods": rescheduled_pods
    })

@app.route('/get_pending_pods', methods=['GET'])
def get_pending_pods():
    """Get information about pods waiting for node resources"""
    pending_pods = scheduler.pod_scheduler.pending_pods
    
    return jsonify({
        "pending_pods": {
            pod_id: {
                "cpu_request": cpu_request
            } for pod_id, cpu_request in pending_pods.items()
        }
    })

@app.route('/')
def index():
    return render_template('index.html')

# Graceful shutdown handler to stop all node threads and repair thread
def shutdown_nodes():
    global repair_thread_running
    
    # Stop repair thread
    repair_thread_running = False
    if repair_thread.is_alive():
        repair_thread.join(1)  # Wait up to 1 second
    
    # Stop all node threads
    for node in node_objects.values():
        node.stop()

if __name__ == '__main__':
    # Make sure templates directory exists
    if not os.path.exists('templates'):
        os.makedirs('templates')
        
    # Create templates directory and copy index.html there
    with open('templates/index.html', 'w') as f:
        with open('index.html', 'r') as source:
            f.write(source.read())
    
    try:
        app.run(debug=True, host='0.0.0.0', port=8000)
    finally:
        # Ensure all node threads are stopped when the server shuts down
        shutdown_nodes()