#!/usr/bin/env python3

import subprocess
import os
import re

from configurations import configurations

os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.chdir('../src')

for label, options, scores in configurations:
    print('{}...'.format(label), end='', flush=True)
    output = subprocess.check_output(['python', '-m', 'main'] + options)

    final_stats = False
    for line in output.decode('utf-8').split('\n'):
        if line.startswith('## Evaluation'):
            final_stats = True
        elif final_stats and line.startswith('Overall when role mapping applies'):
            str_scores = re.search('([0-9.]+)% F1, ([0-9.]+)% accuracy', line).groups()
            f1_score, accuracy_score = float(str_scores[0]), float(str_scores[1])

    wanted_f1, wanted_accuracy = scores
    if wanted_f1 == f1_score and wanted_accuracy == accuracy_score:
        print(' ok!'.format(label))
    else:
        print(' failed! {} f1, {} accuracy'.format(label, wanted_f1 - f1_score, wanted_accuracy - accuracy_score))

