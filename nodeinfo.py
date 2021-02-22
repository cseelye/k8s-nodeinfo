from kubernetes import client, config
from kubernetes.client.rest import ApiException as K8sApiException
import json
import os
from pathlib import Path
import subprocess
import time

GROUP = "cseelye.github.io"
VERSION = "v1alpha1"
NAMESPACE = "nodeinfo"
PLURAL = "nodeinfos"
FIELD_MANAGER = "NodeInfo DaemonSet"
REFRESH_PERIOD = 20
HOST_DIR = Path("/host")

def check_required():
    allgood = True
    env_vars = ["HOST_NODE_NAME"]
    for varname in env_vars:
        if not varname in os.environ.keys():
            print("Missing env var {}".format(varname))
            allgood = False
    
    host_mounts = [HOST_DIR / "sys", HOST_DIR / "etc", HOST_DIR / "proc", HOST_DIR / "dev"]
    for mountpoint in host_mounts:
        if not mountpoint.exists():
            print("Missing host mount {}".format(mountpoint))
            allgood = False

    if not allgood:
        exit(1)

def get_or_create_nodeinfo(cr_api, hostname):
    # Look for an existing CR for this node
    try:
        nodeinfo_current =  cr_api.get_namespaced_custom_object(
            group=GROUP,
            version=VERSION,
            namespace=NAMESPACE,
            plural=PLURAL,
            name=hostname)
        print("Found existing NodeInfo CR for {}".format(hostname))
        return nodeinfo_current
    except K8sApiException as e:
        if e.status == 404:
            # CR was not found. This means it has not been created yet
            pass
        else:
            raise

    # If the CR does not exist already, create it
    nodeinfo = {
        "apiVersion": "{}/{}".format(GROUP, VERSION),
        "kind": "NodeInfo",
        "metadata": {"name": hostname},
        "spec": {}
    }
    print("Creating NodeInfo CR for {}".format(hostname))
    nodeinfo_current = cr_api.create_namespaced_custom_object(
        group=GROUP,
        version=VERSION,
        namespace=NAMESPACE,
        plural=PLURAL,
        field_manager=FIELD_MANAGER,
        body=nodeinfo,
    )
    print("Successfully created NodeInfo CR for {}".format(hostname))
    return nodeinfo_current

def update_nodeinfo_status(cr_api, hostname, nodeinfo_current):
    print("Updating NodeInfo CR status for {}".format(hostname))
    ret = cr_api.replace_namespaced_custom_object_status(
            group=GROUP,
            version=VERSION,
            namespace=NAMESPACE,
            plural=PLURAL,
            field_manager=FIELD_MANAGER,
            name=hostname,
            body=nodeinfo_current
    )
    print("Successfully updated NodeInfo CR status for {}".format(hostname))
    return ret

def discover_status():
    # Discover info about the host system
    # Use ansible facts to discover info about the host, using its "chroot" connector
    # and using container volumes from the host sys, proc, etc

    # Just hardcoded for the moment

    return {
            "hostname": os.environ.get("HOST_NODE_NAME", "unknown"),
            "managementIP": "1.1.1.1",
            "isVirtual": True,
            "cpuCount": 16,
            "memoryBytes": 68719476736,
            "drives": [
                {
                    "name": "sdb",
                    "model": "Virtual disk",
                    "rotational": True,
                    "serial": "6000c2949b7a7cdf3309e46c98d1fc27",
                    "sizeBytes": 8589934592,
                    "vendor": "VMware"
                },
                {
                    "name": "sdc",
                    "model": "Virtual disk",
                    "rotational": True,
                    "serial": "6000c290ecb3294723e7095e4a5c605f",
                    "sizeBytes": 107374182400,
                    "vendor": "VMware"
                },
                {
                    "name": "sdd",
                    "model": "Virtual disk",
                    "rotational": True,
                    "serial": "6000c295212e50f29a0d1d0ea427bcc0",
                    "sizeBytes": 107374182400,
                    "vendor": "VMware"
                }
            ],
            "nics": [
                {
                    "name": "ens192",
                    "ipAddresses": [
                        "1.1.1.1/24"
                    ],
                    "mtu": 1500,
                    "speedMb": 10000,
                    "type": "ether"
                },
                {
                    "name": "ens224",
                    "ipAddresses": [
                        "2.2.2.2/23"
                    ],
                    "mtu": 1500,
                    "speedMb": 10000,
                    "type": "ether"
                }
            ]
        }

def main():

    # Check that this container was launched with the required env and volumes
    check_required()

    # First try in-cluster (we are running in a pod in k8s),
    # then try local config file (we are running as a local script)
    try:
        config.load_incluster_config()
        print("Loaded in-cluster config")
    except config.config_exception.ConfigException:
        try:
            config.load_kube_config()
            print("Loaded local kube config")
        except config.config_exception.ConfigException:
            print("Could not load in-cluster or local configuration")
            exit(1)
    cr_api = client.CustomObjectsApi()

    # The name of this NodeInfo instance is the host node name
    hostname = os.environ.get("HOST_NODE_NAME", "unknown")

    # Get or create the NodeInfo CR for this host
    try:
        nodeinfo_current = get_or_create_nodeinfo(cr_api, hostname)
    except K8sApiException as e:
        print("Error querying NodeInfo CR for {}: {}".format(hostname, e))
        return

    # Update the CR status with the discovered information from the host
    nodeinfo_current["status"] = discover_status()
    try:
        nodeinfo_updated = update_nodeinfo_status(cr_api, hostname, nodeinfo_current)
        print(json.dumps(nodeinfo_updated, indent=2, sort_keys=True))
    except K8sApiException as e:
        print("Error updating CR status for {}: {}".format(hostname, e))
        return

if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            print("Unhandled exception: {}".format(e))
        
        time.sleep(REFRESH_PERIOD)
