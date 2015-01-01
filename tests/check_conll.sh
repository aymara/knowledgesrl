#!/bin/bash

SCRIPT=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT")

$BASEDIR/../src/main.py --conll_input $BASEDIR/../data/spec_lima/jamaica_in.conll --conll_output /tmp/jamaica_out_auto.conll

diff $BASEDIR/../data/spec_lima/jamaica_out_auto.conll /tmp/jamaica_out_auto.conll
