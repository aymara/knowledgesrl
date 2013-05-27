Ideas
=====

Improvements can happen in three main directions:
 * find an actual possible class when there is not possible match,
 * be more selective when choosing potential VerbNet classes,
 * or implement a more informative probability model.

The most important improvement is the first one - it also means we have to
frame our problem in terms of coverage, which the litterature didn't do yet.

Finding new matches
-------------------

An error analysis is needed to understand where the errors come from: is it
because the phrase types from VerbNet are too restrictive? Or is the reason
clausal subjects? Clausal objects that are not handled correctly in VerbNet due
to Levin legacy (Levin classes didn't handle clauses, VerbNet has put them at
the end, but they're not well integrated) ?

Restricting potential VerbNet classes
-------------------------------------

Word Sense Disambiguation
^^^^^^^^^^^^^^^^^^^^^^^^^

As (Brown et al, 2011) have shown in their "VerbNet Class Assignment as a WSD
task" paper, it's possible to have 88.7% accuracy when disambiguating VerbNet
classes for a specific verb (most frequent sense baseline of 73.8%). Would this
be a good way to prune out unwanted classes?

One issue is that existing approaches use supervised learning.

Selectional restriction detection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

VerbNet places selectional restrictions on thematic roles, but there's no
direct way to know if our FrameNet arguments respect those restrictions.
Detecting it automatically would be a good way to prune out unwanted arguments.

Informative probability model
-----------------------------

Three simple models are used in (Swier and Stevenson, 2005) - so simple that
our analysis show that two of them suffer from high bias. After 10% of the
corpus is seen, they're no longer informative. The third one is more
informative but doesn't improve with more data (TODO include analysis from
Guilhem).

One option is to continue in the direction of probability models: try to find
more informative ones by including more linguistically-motivated data.

Another option is to use a probabilistic model which would allow us to modelize
correctly the back-off procedure from (Swier and Stevenson, 2004).

The last option is to fully go the supervised route: use features and models
from supervised litterature using our initial frame-matching data.
