# knowledgesrl

Thank you for checking out knowledgrsrl, our knowledge-based semantic role
labeling implementation! Feel free to report GitHub issues for any question or
remarks you might have.

Main entry point is `knowledgesrl.py`.

To use it, install dependencies

```bash
$ pip install -r ./requirements.txt
```

Install also LIMA and/or SpaCy models:
```bash
$ lima_models -i eng
$ spacy download fr_core_news_md
```

To do SRL, you need a CoNLL representation of a text. Let's suppose it is in the file `in.txt`. To do that, you can use either LIMA:
```bash
$ lima in.conll > out.conll
```

Or SpaCy:
```bash
$ python run_spacy.py --input_file in.txt --model fr_core_news_md > in.conll
```

Then get SRL instructions with:

```bash
$ python src/knowledgesrl.py --help
```

For example, to annotate with FrameNet a French text, use a parser to generate a ConLL file and then run:

```bash
$ python src/knowledgesrl.py --language=fre --frame-lexicon=FrameNet --conll-input=in.conll
```

This will output the result to the terminal. Use the `--conll-output` flag to write to a file.

## [Read the docs!](https://knowledgesrl.readthedocs.org/en/latest/)

## License : AGPLv3

Copyright (C) 2013-2014 CEA LIST (Guilhem Pujol, Quentin Pradet and
contributors)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
