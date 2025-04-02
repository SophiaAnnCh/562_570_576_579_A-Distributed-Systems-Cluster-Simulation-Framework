from flask import Flask, request, jsonify
from node_manager import NodeManager

app = Flask(__name__)
node_manager = NodeManager()

@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.json
    node_id = data.get('node_id')
    cpu_capacity = data.get('cpu_capacity', 2)  # Default 2 CPU
    if not node_id:
        return jsonify({"error": "node_id is required"}), 400

    node_manager.add_node(node_id, cpu_capacity)
    return jsonify({"message": f"Node {node_id} added with {cpu_capacity} CPU"}), 201

@app.route('/list_nodes', methods=['GET'])
def list_nodes():
    return jsonify(node_manager.list_nodes())

if __name__ == '__main__':
    app.run(debug=True)
