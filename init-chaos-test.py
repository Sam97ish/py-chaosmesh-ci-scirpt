#!/usr/bin/python3.8

import json
from os import path
import random
import string
import yaml
import argparse
from kubernetes.client.rest import ApiException
from kubernetes import client, config
import logging

logging.DEBUG = 1

def select_pod(ns, label, k8s_api_v1):
    return k8s_api_v1.list_namespaced_pod(ns, label_selector=label)

def get_logs(label, ns):
    
    logs = {}

    try:
        k8s_api_v1 = client.CoreV1Api()
        
        ret = select_pod(ns, label, k8s_api_v1)
        #print(ret)
        for pod in ret.items:
            #print(pod)
            pod_name = pod.metadata.name
            log_resp = k8s_api_v1.read_namespaced_pod_log(name=pod_name, namespace=ns, container=label.split('=', 1)[1]) # assuming container name is same as label name.
            describe_resp = k8s_api_v1.list_namespaced_event(ns, field_selector=f'involvedObject.name={pod_name}')
            logging.debug('Retrived logs for pod {0}'.format(pod_name))
            logs[pod_name] = (log_resp, describe_resp)
    
        return logs
    except ApiException as e:
        logging.error('Found exception in reading the logs \n {0}'.format(e))


def write_logs(logs):

    for name, (log, describe) in logs.items():

        with open(path.join(path.dirname(__file__), '{0}_log'.format(name),), 'w') as log_file:
            log_file.write(log)
            logging.debug('Wrote logfile {0}_log'.format(name))

        with open(path.join(path.dirname(__file__), '{0}_describe'.format(name),), 'w') as describe_file:
            describe_file.write(str(describe.items))
            logging.debug('Wrote describefile {0}_describe'.format(name))        
        

def load_experiment(exp):

        with open(path.join(path.dirname(__file__), exp)) as exp_file:
            return yaml.safe_load(exp_file)

def kill_pod(label, ns, exp):

    write_logs(get_logs(label, ns))

    exp_yaml = load_experiment(exp)

    name = exp_yaml['metadata']['name']
    exp_yaml['metadata']['name'] = name+'-'+''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    exp_yaml['metadata']['namespace'] = ns
    exp_yaml['spec']['selector']['namespaces'] = [ns]
    exp_yaml['spec']['selector']['labelSelectors'] = {label.split('=', 1)[0]: label.split('=', 1)[1]}

    crd_api = client.CustomObjectsApi()

    group = exp_yaml['apiVersion'].split('/', 1)[0]
    version = exp_yaml['apiVersion'].split('/', 1)[1]
    plural = exp_yaml['kind'].lower()
    

    
    try:

        crd_chaos = crd_api.create_namespaced_custom_object(
            group, version, ns, plural, exp_yaml, _preload_content=False
        )
        return json.loads(crd_chaos.data)
    except ApiException as e:
        if e.status == 409:
            logging.debug("Custom resource object {0}/{1} already exists".format(group, version))
            return json.loads(e.body)
        else:
            raise Exception(
                "Failed to create custom resource object: '{0}' {1}".format(e.reason, e.body)
            )

def main():

    config.load_kube_config()

    parser = argparse.ArgumentParser(prog = 'init-chaos-test',
                    description = 'Launches a preconfigured chaos-mesh experiment.')
    parser.add_argument('-e', '--experiment', type=str, dest='exp', required=True,
                    help='The yaml/json experiment to launch.')
    parser.add_argument('-ns', '--namespace', type=str, dest='ns', default='default',
                    help='The target namespace')
    parser.add_argument('-l', '--label', type=str, dest='label',
                    help='The label of the pod to be killed. Example app=checkout.')

    args = parser.parse_args()
    
    resp = kill_pod(args.label, args.ns, args.exp)

    print('Created chaos pod with name "{0}" in namespace "{1}" with labelSelectors: "{2}"'
    .format(resp['metadata']['name'], resp['metadata']['namespace'], resp['spec']['selector']['labelSelectors']))

if __name__ == '__main__':
    main()