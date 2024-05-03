#!/usr/bin/env python3

import aymara.lima
import argparse
import sys


def main():  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--language",
        type=str,
        default="ud-eng",
        help="set the language to initialize",
    )
    parser.add_argument(
        "-p",
        "--pipeline",
        type=str,
        default="deepud",
        help="set the pipeline to initialize",
    )
    parser.add_argument(
        "file",
        type=str,
        help="the file to analyze",
    )
    args = parser.parse_args()
    nlp = aymara.lima.Lima(args.language, args.pipeline)
    with open(args.file) as text_file:
        text = text_file.read()
        r = nlp(text)
        print(repr(r))
    sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()

