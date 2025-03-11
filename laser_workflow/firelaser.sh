#! /bin/bash 
# Assume that meerk40t is installed at the same level as gds factory.
echo Loading $1
cd ../meerk40t/
. venv/bin/activate
python3 meerk40t.py -a $1


