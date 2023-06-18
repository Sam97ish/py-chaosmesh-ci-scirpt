# Chaos Mesh Python CI Script

This is a python script that I used to deploy choas mesh components into
my test cluster.

## USAGE
```bash
usage: init-chaos-test [-h] -e EXP [-ns NS] [-l LABEL]

Launches a preconfigured chaos-mesh experiment.

optional arguments:
  -h, --help            show this help message and exit
  -e EXP, --experiment EXP
                        The yaml/json experiment to launch.
  -ns NS, --namespace NS
                        The target namespace
  -l LABEL, --label LABEL
                        The label of the pod to be killed. Example app=checkout.
```