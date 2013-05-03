Ideas
=====

Word Sense Disambiguation
-------------------------

As (Brown et al, 2011) have shown in their "VerbNet Class Assignment as a WSD
task" paper, it's possible to have 88.7% accuracy when disambiguating VerbNet
classes for a specific verb (most frequent sense baseline of 73.8%). Would this
be a good way to prune out unwanted classes?

One issue is that existing approaches use supervised learning.

Selectional restriction detection
---------------------------------

VerbNet places selectional restrictions on thematic roles, but there's no
direct way to know if our FrameNet arguments respect those restrictions.
Detecting it automatically would be a good way to prune out unwanted arguments.


