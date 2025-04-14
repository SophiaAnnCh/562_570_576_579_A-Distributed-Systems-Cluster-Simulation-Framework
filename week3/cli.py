import argparse
import requests
import json
import time
import os
import sys

# Base URL for API
BASE_URL = "http://localhost:5000"

def add_node(args):
    """Add a node to the cluster"""
    response = requests.post(f"{BASE_URL}/add_node", json={
        "node_id": args.node_id,
        "cpu_capacity": args.cpu_capacity
    })
    
    if response.status_code == 201:
        print(f"✓ Success: {response.json().get('message')}")
    else:
        print(f"✗ Error: {response.json().get('error')}")

def list_nodes(args):
    """List all nodes in the cluster with their status"""
    response = requests.get(f"{BASE_URL}/list_nodes")
    
    if response.status_code == 200:
        nodes = response.json()
        if not nodes:
            print("No nodes found in the cluster.")
            return
            
        print("\n=== Cluster Status ===")
        for node_id, node_info in nodes.items():
            health_status = node_info.get("health", "Unknown")
            health_symbol = "✓" if health_status == "Healthy" else "✗"
            
            print(f"\nNode: {node_id} [{health_symbol} {health_status}]")
            print(f"├── Container ID: {node_info.get('container_id', 'N/A')[:12]}")
            print(f"├── CPU Capacity: {node_info.get('cpu_capacity', 'N/A')}")
            print(f"├── CPU Available: {node_info.get('cpu_available', 'N/A')}")
            print(f"└── Pods: {', '.join(node_info.get('pods', [])) or 'None'}")
    else:
        print(f"✗ Error: Could not retrieve node list")

def schedule_pod(args):
    """Schedule a pod on the cluster"""
    response = requests.post(f"{BASE_URL}/schedule_pod", json={
        "pod_id": args.pod_id,
        "cpu_request": args.cpu_request
    })
    
    if response.status_code == 201:
        data = response.json()
        print(f"✓ Success: {data.get('message')}")
    else:
        print(f"✗ Error: {response.json().get('error')}")

def main():
    parser = argparse.ArgumentParser(description="Kubernetes-like Cluster CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add node command
    node_parser = subparsers.add_parser("add-node", help="Add a node to the cluster")
    node_parser.add_argument("node_id", help="Unique ID for the node")
    node_parser.add_argument("--cpu", dest="cpu_capacity", type=int, default=100, 
                            help="CPU capacity of the node (default: 100)")
    
    # List nodes command
    list_parser = subparsers.add_parser("list-nodes", help="List all nodes in the cluster")
    
    # Schedule pod command
    pod_parser = subparsers.add_parser("schedule-pod", help="Schedule a pod on the cluster")
    pod_parser.add_argument("pod_id", help="Unique ID for the pod")
    pod_parser.add_argument("--cpu", dest="cpu_request", type=int, default=10, 
                           help="CPU request for the pod (default: 10)")
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == "add-node":
        add_node(args)
    elif args.command == "list-nodes":
        list_nodes(args)
    elif args.command == "schedule-pod":
        schedule_pod(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()