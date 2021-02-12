from kubernetes import client, config
from kubernetes.client.rest import ApiException as K8sApiException
import json
import time
from pprint import pprint

GROUP = "cseelye.github.io"
VERSION = "v1alpha1"
NAMESPACE = "nodeinfo"

def main():

    try:
        config.load_incluster_config()
    except config.config_exception.ConfigException:
        try:
            config.load_kube_config()
        except config.config_exception.ConfigException:
            print("Could not load in-cluster or local configuration")
            exit(1)

    k8s_api = client.CustomObjectsApi()

    while True:

        cr_name = "nodeinfo-localhost"

        try:
            existing_cr = k8s_api.get_namespaced_custom_object(
                group=GROUP,
                version=VERSION,
                namespace=NAMESPACE,
                plural="nodeinfos",
                name=cr_name)
            print("Got existing NodeInfo CR")
        except K8sApiException as e:
            if e.status == 404:
                # CR was not found. This just means it has never been created
                existing_cr = None
            else:
                print("Error querying CR: {}".format(e))
                time.sleep(60)
                continue

        nodeinfo_spec = {
            "hostname": "localhost",
            "managementIP": "1.2.3.4",
            "cpuCoreCount": 2,
            "memoryBytes": 2199023255552
        }

        if existing_cr:
            nodeinfo = existing_cr
            nodeinfo["spec"] = nodeinfo_spec
            try:
                ret = k8s_api.replace_namespaced_custom_object(
                    group=GROUP,
                    version=VERSION,
                    namespace=NAMESPACE,
                    plural="nodeinfos",
                    name=cr_name,
                    body=nodeinfo
                )
                print("Updated NodeInfo CR")
                print(json.dumps(ret, sort_keys=True, indent=2))
            except K8sApiException as e:
                print("Error updating CR: {}".format(e))
        else:
            nodeinfo = {
                "apiVersion": "{}/{}".format(GROUP, VERSION),
                "kind": "NodeInfo",
                "metadata": {"name": cr_name},
                "spec": nodeinfo_spec
            }
            try:
                ret = k8s_api.create_namespaced_custom_object(
                    group=GROUP,
                    version=VERSION,
                    namespace=NAMESPACE,
                    plural="nodeinfos",
                    body=nodeinfo,
                )

                print("Created NodeInfo CR")
                print(json.dumps(ret, sort_keys=True, indent=2))
            except K8sApiException as e:
                print("Error creating CR: {}".format(e))
        
        time.sleep(20)

if __name__ == '__main__':
    main()
