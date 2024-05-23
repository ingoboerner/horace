#!/bin/bash

#Download the corpora
averell download disco2_1
#averell download disco3
averell download adso
averell download adso100
averell download plc
averell download gongo
averell download 4b4v
averell download ecpa
averell download mel
averell download bibit
#averell download czverse
averell download stichopt

# Start the process
python horace/main.py -i corpora/ -o out/