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
VerbNet.  Finding verbs is not very complex, since they are the words to which
our parser attribute one of the following part-of-speech:
  * *VB*: base form (as 'eat' in 'He should eat')
  * *VBD*: past tense
  * *VBG*: gerund
  * *VBN*: past participle
  * *VBP*: present tense
  * *VBZ*: third personn of present
  * *MD*: modal verb

Note : these tags are different from those of the fulltext annotations. The
reason for this is unclear, and this only concerns verbs part-of-speech. As we
are not currently using a part-of-speech tagger, our parser takes those POS
annotation as input, after conversion of verbal POS into the more standard tags
listed above, which are those which were used in the parser training data.

Parsing errors can already introduce some mistakes at this point, since our
parser can fail at distinguishing some verbs from nouns.

We do not want to keep every of those extracted verbs. Auxiliary verbs (as
"has" and "been"' in "He has been working") must be discarded. We can do this
by discarding every occurence that belongs to a small list of verbs (like
"have", "be" or "do"), but we might lose some intersting occurence of "have".
Another solution to identify auxiliary verbs is to look for verbs which have at
least one child bound to them by a *VC* (Verb Chain) relation and which are not
modal verbs (because construction as "I can eat an apple" seem to result in two
frames in the FrameNet fulltext annotations, so we should not discard "can" in
this sentence).

We also need to determine what to do with isolated gerunds and past
participles.  They tend to be annotated in FrameNet, but we are not sure that
they are compatible with the frame structures that exist in VerbNet.

Infinitive form
```````````````

In order to find the VerbNet entries associated with a verb, we need to find
its infinitive form. Our solution for that is to use WordNet, and more
specifically the ``morphy`` method of ``nltk.corpus.wordnet``. This is done in a
separate python2 script, since *nltk* is not compatible with python3 yet.

Note: the relation between could and can is added manually since Morphy
doesn't detect it. We would like to remove "can" since it's a modal not covered
by VerbNet, but it also means to fire ("She canned her secretary") and to
pocket, which are in VerbNet.

Error analysis
``````````````

Some of the extracted frames are not annotated in the fulltext corpus. In most
cases, this is because the annotations are not comprehensive. We analysed 50 of
those frame after commit 18615 and found the following other reasons for the 
lack of annotation in the corpus::

    Gérondif ou participe passé adjectival : 11
    Non verbe auquel le corpus fulltext donne une POS de verbe : 8
    Mauvais arbre syntaxique (=> auxiliaire non détecté comme tel) : 2
    
Because there is no simple way to know which of the extracted frames that do not
appear in the corpus should be considered as errors, we chose not to penalize
arguments extracted from those frames in the performances evaluation. 

Arguments extraction
--------------------

Standard method
```````````````

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

Heuristic method
````````````````

Another method based on (Lang & Lapata, 2011) has been implemented. It results
in the extraction of a greater proportion of the annotated arguments, but also
extracts much more junk arguments.

An analysis of incorrect extracted arguments and non-extracted correct arguments
has been done on 50 frames and the reason for each mistakes was noted. This was
done after commit 18615 ::

    Extraits incorrects :

        - argument non core : 10 (8 frames)
        - argument non core perturbant le frame matching : 3 (2 frames)
        - le prédicat n'est pas un verbe : 3 (2 frame)

        A cause des règles heuristiques (total : 12 arguments)
        - la règle 3 n'extrait pas un argument (souvent avec des gérondifs): 6 (6 frames)
        - le sujet est objet d'un autre verbe et donc pas extrait : 4 (4 frames)
        - erreur d'implémentation de la règle 6 (corrigée) : 2 (2 frames)

        A cause de l'arbre syntaxique (total : 8 arguments)
        - verbe rattaché au mauvais auxiliaire : 2 (2 frames)
        - subordonnée mal rattachée : 2 (2 frames)
        - construction "help (service somebody)" -> "help (service) (somebody)" : 1 (1 frame)
        - sujet pas marqué comme SBJ : 1 (1 frame)
        - argument adjoint rattaché à un autre verbe : 1 (1 frame)
        - structure trop complexe : 1 (1 frame)

    Non extraits annotés :

        - le prédicat n'est pas un verbe : 2 (2 frame)
        - prédicat isolé de ses arguments par des virgules : 2 (1 frame)
       
        A cause des règles heuristiques (total : 10 arguments)
        - le sujet est objet d'un autre verbe et donc pas extrait : 4 (4 frames)
        - plusieurs verbes pour un seul objet : 3 (2 frames)
        - un auxiliaire (jeté par la règle 4) se trouvait être un argument : 2 (2 frames)
        - non extraction du sujet d'un gérondif qualifiant un nom : 1 (1 frame)

         A cause de l'arbre syntaxique (total : 12 arguments)
        - objet pas rattaché au verbe : 7 (6 frames)
        - verbe rattaché au mauvais auxiliaire : 2 (2 frames)
        - sujet rattaché à un autre verbe : 1 (1 frame)
        - subordonnée rattachée à un mauvais verbe : 1 (1 frame)
        - adjoint rattaché à un autre verbe : 1 (1 frame)

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

