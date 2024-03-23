#!/bin/bash
source /home/azureuser/baton-env/bin/activate
cd /home/azureuser/lemr-pipeline/python/baton/procedures
python3 -m apis.lemr.api /home/azureuser/lemr-pipeline/python/baton/configs/purpose-lemr-local.yaml

