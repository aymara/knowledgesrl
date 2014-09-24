#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import framenetreader
from pathlib import Path


semafor_file = Path("../data/semafor/all_evaluation.out")
semafor_corpus = Path("../data/fndata-1.5/fulltext/evaluation/")
semafor_pos = Path("../data/semafor/all_evaluation_pos")
#semafor_file = "../data/semafor/semafor_testset.out"
#semafor_corpus = "../data/semafor/testset/"
#semafor_pos = "../data/semafor/semafor_testset_pos"

reader = framenetreader.FulltextReader(
semafor_file, core_args_only = True, pos_file = semafor_pos,
keep_nonverbal = False)
semafor_frames = reader.frames
semafor_roles = [[y.role for y in x.args] for x in semafor_frames]

annotated_frames = []
for filename in sorted(semafor_corpus.glob('*.xml')):
    reader = framenetreader.FulltextReader(
        filename,
        core_args_only = True,
        keep_unannotated = True,
        keep_nonverbal = False)
    annotated_frames += reader.frames

num_annotated_frames = len(annotated_frames)
num_annotated_args = sum([len([y for y in x.args if y.instanciated]) for x in annotated_frames])

num_good, num_bad = 0, 0
num_correct, num_incorrect = 0, 0    

sentence_position = 0
last_sentence = ""

for frame in semafor_frames:
    if last_sentence != frame.sentence:
        sentence_found = True
        i = sentence_position
        while annotated_frames[i].sentence != frame.sentence:
            if i >= len(annotated_frames) - 1:
                sentence_found = False
                break
            i += 1
        if sentence_found:
            sentence_position = i

    last_sentence = frame.sentence    
    if not sentence_found: continue

    i = sentence_position
    frame_found = True
    while annotated_frames[i].predicate.begin != frame.predicate.begin:
        if (i >= len(annotated_frames) - 1
            or annotated_frames[i + 1].sentence != frame.sentence
        ):
            frame_found = False
            break
        i += 1
    if not frame_found:
        num_bad += len(frame.args)
        continue
    
    for arg in frame.args:
        arg_found = False
        for annotated_arg in annotated_frames[i].args:
            if annotated_arg.begin == arg.begin and annotated_arg.end == arg.end:
                arg_found = True
                num_good += 1
                if arg.role == annotated_arg.role:
                    num_correct += 1
                else:
                    num_incorrect += 1
                break
        if not arg_found:
            num_bad += 1

print(
    "Total arguments (corpus) : {} \n"
    "Idenfied correct arguments : {} \n"
    "Bad arguments : {} \n"
    "Good roles : {} \n"
    "Bad roles : {}"
    "\n".format(num_annotated_args, num_good, num_bad,
        num_correct, num_incorrect)
)

precision = num_correct / (num_good + num_bad)
recall = num_correct / num_annotated_args
f1 = 2 * (precision * recall) / (precision + recall)

print(
    "Precision : {:.2%} \n"
    "Recall : {:.2%} \n"
    "F1 : {:.2%} \n".format(
    precision, recall, f1)
)
