Debug ressources
================

Sample of headwords extractions
-------------------------------

To get a sample of 100 headword extractions into a pickle file, use: ::

  ./headwordextractor.py -s 100 sample_file

Each sample contains three lines which are:
  * the real argument
  * the closest matching node of the syntactic tree of this sentence
  * the headword

Dump module
-----------

The dump module is a script which facilitate the visualisation of the impact of
a code modification or of an option on the results.

The --dump option allows the user to dump the state of the algorithm after the
frame-matching and after the probability model instead of displaying
statistics, and the dumper module can display the differences between two dump
files when called directly.

By default, only the differences that have an impact on the performance
statistics are displayed (ie, slots that have a good state like one_role_good
in one dump and a bad state like no_role in another). To display every
difference, use the ``--all`` option of dumper.py.

For instance, to see the exact differences between the slot and the slot-class
probability models: ::
  ./main.py --model=slot_class --dump test1
  ./main.py --model=slot --dump test2
  ./dumper.py test1 test2
  
Outputs: ::

    Differences after frame matching:
    Good -> bad:
    Bad -> good:


    Differences after probability model:
    Good -> bad:


    Sentence: The stimulus package will jumpstart the economy and make sure it
    does n't slide into recession again .
    Predicate: slide
    Argument: into recession
    Frame structure: ['NP', 'V', 'into', 'NP']
    Frame name: Motion
    Role list: {'Location'}
    Correct role: Goal (FrameNet) -> {'Location'} (VerbNet)
    Status: one_role_good

    Sentence: The stimulus package will jumpstart the economy and make sure it
    does n't slide into recession again .
    Predicate: slide
    Argument: into recession
    Frame structure: ['NP', 'V', 'into', 'NP']
    Frame name: Motion
    Role list: {'Result'}
    Correct role: Goal (FrameNet) -> {'Location'} (VerbNet)
    Status: one_role_bad



    Sentence: The stimulus package will jumpstart the economy and make sure it
    does n't slide into recession again .
    Predicate: slide
    Argument: into recession
    Frame structure: ['NP', 'V', 'into', 'NP']
    Frame name: Motion
    Role list: {'Location'}
    Correct role: Goal (FrameNet) -> {'Location'} (VerbNet)
    Status: one_role_good

    Sentence: The stimulus package will jumpstart the economy and make sure it
    does n't slide into recession again .
    Predicate: slide
    Argument: into recession
    Frame structure: ['NP', 'V', 'into', 'NP']
    Frame name: Motion
    Role list: {'Result'}
    Correct role: Goal (FrameNet) -> {'Location'} (VerbNet)
    Status: one_role_bad

    (...)

    Bad -> good:


    Sentence: But Jamaica is not simply turning blindly into a small version of
    its bigger brother .
    Predicate: turn
    Argument: into a small version of its bigger brother
    Frame structure: ['NP', 'V', 'into', 'NP']
    Frame name: Undergo_change
    Role list: {'Location'}
    Correct role: Final_category (FrameNet) -> {'Result'} (VerbNet)
    Status: one_role_bad

    Sentence: But Jamaica is not simply turning blindly into a small version of
    its bigger brother .
    Predicate: turn
    Argument: into a small version of its bigger brother
    Frame structure: ['NP', 'V', 'into', 'NP']
    Frame name: Undergo_change
    Role list: {'Result'}
    Correct role: Final_category (FrameNet) -> {'Result'} (VerbNet)
    Status: one_role_good



    Sentence: Right , yeah , I heard about that on the news , yeah .
    Predicate: hear
    Argument: about that
    Frame structure: ['NP', 'V', 'about', 'NP']
    Frame name: Perception_experience
    Role list: {'Theme'}
    Correct role: Phenomenon (FrameNet) -> {'Stimulus'} (VerbNet)
    Status: one_role_bad

    Sentence: Right , yeah , I heard about that on the news , yeah .
    Predicate: hear
    Argument: about that
    Frame structure: ['NP', 'V', 'about', 'NP']
    Frame name: Perception_experience
    Role list: {'Stimulus'}
    Correct role: Phenomenon (FrameNet) -> {'Stimulus'} (VerbNet)
    Status: one_role_good

