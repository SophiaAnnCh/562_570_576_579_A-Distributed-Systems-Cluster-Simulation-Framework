from flask import Flask, request, jsonify, render_template
from scheduler import Scheduler
from node import Node
import os

app = Flask(__name__, template_folder=os.path.abspath('templates'))
scheduler = Scheduler()

# Store Node objects that send heartbeats
node_objects = {}

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
        # Add pod to the Node object for tracking (if it exists)
        if assigned_node in node_objects:
            node_objects[assigned_node].add_pod(pod_id)
            
        return jsonify({
            "message": f"Pod {pod_id} scheduled on node {assigned_node}",
            "node": assigned_node
        }), 201
    else:
        return jsonify({"error": "Could not schedule pod - insufficient resources or unhealthy nodes"}), 400

@app.route('/')
def index():
    return render_template('index.html')

# Graceful shutdown handler to stop all node threads
def shutdown_nodes():
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