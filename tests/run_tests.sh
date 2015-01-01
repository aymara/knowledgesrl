#!/bin/bash

SCRIPT=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT")

# unit tests
#PYTHONPATH=$BASEDIR/../src python -m unittest discover $BASEDIR

# scores on FrameNet for various configurations
#python $BASEDIR/check_buildbot_scores.py

# single file test
$BASEDIR/check_conll.sh
