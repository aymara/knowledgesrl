#!/bin/bash

SCRIPT=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT")

PYTHONPATH=$BASEDIR/../src python -m unittest discover $BASEDIR
python $BASEDIR/check_buildbot_scores.py
