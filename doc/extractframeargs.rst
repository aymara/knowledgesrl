Frames and arguments extractions
================================

Our aim is to be able to create a SRL program that takes raw text as input.
This means that we need to find a way to extract the verbal frames and
arguments from a text for which we only have the syntactic annotations of the
MST parser.

Frame extraction
----------------

Verb extraction
```````````````

As always, we are only interested in verbal frames which predicate is in
VerbNet.
Finding verbs is not very complex, since they are the words to which our
parser attribute one of the following part-of-speech:
  * *VB*: base form (as 'eat' in 'He should eat')
  * *VBD*: past tense
  * *VBG*: gerund
  * *VBN*: past participle
  * *VBP*: present tense
  * *VBZ*: third personn of present
  * *MD*: modal verb

Note : these tags are different from those of the fulltext annotations. The
reason for this is unclear, and this only concerns verbs part-of-speech. As
we are not currently using a part-of-speech tagger, our parser takes those POS
annotation as input, after conversion of verbal POS into the more standard tags
listed above, which are those which were used in the parser training data.

Parsing errors can already introduce some mistakes at this point, since our
parser can fail at distinguishing some verbs from nouns.

We do not want to keep every of those extracted verbs. Auxiliary verbs (as 
"has" and "been"' in "He has been working") must be discarded. We can do this
by discarding every occurence that belongs to a small list of verbs (like 
"have", "be" or "do"), but we might lose some intersting occurence of "have".
Another solution to identify auxiliary verbs is to look for verbs which have
at least one child bound to them by a *VC* (Verb Chain) relation and which are 
not modal verbs (because construction as "I can eat an apple" seem to result in
two frames in the FrameNet fulltext annotations, so we should not discard "can"
in this sentence).

We also need to determine what to do with isolated gerunds and past participles.
They tend to be annotated in FrameNet, but we are not sure that they
are compatible with the frame structures that exist in VerbNet.

Infinitive form
```````````````

In order to find the VerbNet entries associated with a verb, we need to find its
infinitive form. Our solution for that is to use WordNet, and more specifically
the *morphy* method of *nltk.corpus.wordnet*. This is done in a separate python2
script, since *nltk* is not compatible with python3 yet.

Arguments extraction
--------------------

Finding arguments
`````````````````

Once we found a predicate, we can look for candidate argument nodes. This is
done by exploring the subtree of the syntactic tree that starts at the predicate
nodes. Our parser output is not well-fitted for applying the extraction method
of Swier and Stevenson 2005 since it is dependency based and not constituency
based. Our current method is to look for node in the subtree with a deprel that
is either:
  * SBJ or LGS for subject
  * OBJ or OPRD for objects
  * BNF, DTV or PRD

We also stop exploring the subtree at each node which contains a verb, because
arguments that we might find under this node are much more likely to relate to
this verb rather than the verb at the top node of the subtree.

This results in the extraction of very few PP: there are probably other
dependency relations that should be extracted.

POS conversions
```````````````

We want to use the part-of-speeches of our arguments for the building of the
frame's VerbNet structure (like "NP V that S"). The conversion from the MST
output part-of-speech tags to the more limited VerbNet tags (NP, S,
ADV and keywords) is based on 
http://www.comp.leeds.ac.uk/ccalas/tagsets/upenn.html. The exhaustive list of
conversions is part of the code of argguesser. Some of them, like the conversion
of the IN tag which can be either attributed to a preposition or a
subordinating conjunction require complex operations which are hard-coded in the
*_get_phrase_type* method of this module.


Evaluation
----------

The frames and arguments extractions should be evaluated conjointly if we do not
want to have to answer questions like "Do we penalize the extraction of a frame
that is not in the annotated corpus but for which we did not find any argument?"

Another question is whether we should evaluate the argument extraction process
before or after the frame-matching, if we consider that arguments for which the
frame-matching finds no possible roles are discarded.

Currently, we only retrieve 1142 of the 10347 arguments of the fulltext corpus.
One factor for this is that there are two missing file in framenet_parsed:
  * ANC__110CYL070.xml
  * NTI__BWTutorial_chapter1.xml
  
Moreover, we retrieve 1912 arguments that do not match any argument of the
fulltext corpus. According partial credit for some arguments would probably be
a good idea. We need to choose how: do we trust our headword extraction system
enough to say that a partial match is an extracted argument that has the same
headword as an annotated argument, or do we use a longuest-common-substring
approach? The first approach carries a risk of artificially boosting the
results, since the headword extraction is itself based on the MST output.

