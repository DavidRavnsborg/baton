#!/bin/bash
source /home/azureuser/baton-env/bin/activate
cd /home/azureuser/lemr-pipeline/python/baton
python procedures/lemr_check_submissions_run_geocoding.py configs/purpose-lemr-local.yaml
