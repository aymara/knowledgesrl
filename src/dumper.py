#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pickle
import sys
import os


def dump(filename, annotated_frames):
    os.makedirs('dump', exist_ok=True)
    with open("dump/"+filename, "wb") as picklefile:
        pickle.dump(annotated_frames, picklefile)
    print('Dumped to dump/{}'.format(filename))

def diff_all(data1, data2):
    for slot_data1, slot_data2 in zip(data1, data2):
        if slot_data1 != slot_data2:
            assert slot_data1['gold_fn_frame'] == slot_data2['gold_fn_frame']
            frame = slot_data1['gold_fn_frame']
            print()

            print("Frame {} ({})".format(frame.frame_name, frame.predicate.lemma))
            print(frame.filename.stem)
            print(frame.sentence)
            for slot1, slot2 in zip(slot_data1['slots'], slot_data2['slots']):
                print("  * {}".format(slot1['text']))
                print("    {} should in {}".format(slot1['found_roles'], slot1['wanted_roles']))
                print("    {} should in {}".format(slot2['found_roles'], slot2['wanted_roles']))

if __name__ == "__main__":
    status = True

    if len(sys.argv) >= 2:
        filename1 = sys.argv[1]
        filename2 = sys.argv[2]
    else:
        print("Syntax : dump.py file1 file2")

    print(filename1)
    with open("dump/"+filename1, "rb") as picklefile:
        data1 = pickle.load(picklefile)
    print(filename2)
    with open("dump/"+filename2, "rb") as picklefile:
        data2 = pickle.load(picklefile)

    diff_all(data1, data2)
    print("That was the list of differences between {} and {}.".format(filename1, filename2))
