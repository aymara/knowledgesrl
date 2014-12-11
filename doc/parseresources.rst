Resources parsing
=================

VerbNet parsing
---------------

The parsing of VerbNet is done by the ``verbnetreader`` module. It
reads every XML file in our modified VerbNet data/verbnet, each of
which represents a VerbNet root class and all its subclasses.

For each frame found in every class and subclasses of a file, a
``VerbnetOfficialFrame`` object is instanciated and associated with every
member verb of the class and its subclasses.

The difficult part is to build the structure and the role list of the
``VerbnetOfficialFrame``, that is, to convert the ``primary`` attribute of the
``DESCRIPTION`` element to an acceptable list of syntactic elements (that is,
compatible with FrameNet annotations), and to retrieve the roles of the
elements that have one.

The following operations are applied to the elements of the ``primary``
attribute:

* everything that is after a "." or a "-" is removed (for instance, NP.theme
  becomes NP, S-Quote becomes S)
* adverbs are removed from the structure (not handled yet)
* "v" is replaced by "V" (no distinction between transitive and
  non-transitive verbs needed)
* "a/b" is interpreted as [a or b].
* every preposition is made explicit. That means that "S_INF" is replaced with
  "to S" and more importantly, "PP" is replaced by "prep NP".
* every "PP S_ING" is converted to "prep S_ING" (and not "prep NP S_ING")
  
In order to know which preposition can be used in a PP, which is not always
explicit in the primary structure, we look into the ``SYNTAX`` element of the
frame. The information can take three different forms :

* a ``LEX`` element, which ``value`` attribute is the only acceptable
  preposition,
* a ``PREP`` element with a ``value`` attribute, which is the only acceptable
  preposition,
* a ``PREP`` element whitout ``value`` attribute, but which contains
  selective restrictions data. In this case, the ``type`` attribute of the
  SELRESTRS/SELRESTR element gives us the preposition classe, and
  ``verbnetprepclasses`` lists the corresponding prepositions.

Sometimes, keywords (prepositions or what/who/it/...) whom presence cannot be
deduced from the primary structure appear in the ``SYNTAX`` element. That is
why for every element of the primary structure, we have to find the position of
the matching element of the ``SYNTAX`` and add any keywords that occured
between this position and the previous one to our final structure if it was not
present in the primary structure. Note that case it is also possible to find
keywords in the primary structure and not in the ``SYNTAX``, so a parsing based
on the ``SYNTAX`` is not necessarily a better idea.

The resulting structure is the list of everything that will have an importance
in the frame matching, that is NP, V, S and also every required preposition
(which, as, ...). Those emplacements are represented by strings unless there
are several possibilities (for instance, when a class of preposition can
introduced a NP). In that case, the element is represented by the set of every
acceptable string.

We use two sources of informations to build the role list:

* the ``value`` attributes of the elements of ``SYNTAX`` where it is present
* everything that is after a "." in the primary structure. For instance, we
  extract "theme" in "NP.theme". We make sure that the extracted role is one
  of the possible role listed in the ``THEMROLES`` element (after some case
  modifications), to avoid extracting every "attribute" of "PP.attribute".
    
Conflicts can occur between the sources of information. For instance, in
``calibrate_cos-45.6``, reading the structure of the frame ``NP.attribute V
NP.extent`` leads to the conclusion that there are two slots with the role
``Attribute`` and ``Extent``. In the ``SYNTAX`` element, another NP with a
``Patient`` role is present between the first NP and the verb. For those cases,
as the final structure comes mainly from the primary structure, we trust the
roles found in the primary element, and the second element keeps an ``Extent``
role.

FrameNet parsing
----------------

Fulltext corpus data
````````````````````

The parsing of FrameNet mainly consists in instanciating ``FrameInstance``
objects from FrameNet's XML corpus. After all steps described below, the frame
occurrence is translated into a ``VerbnetFrameOccurrence``, an object close
enough to ``VerbnetOfficialFrame`` to allow for frame matching: the data that
needs to be inferred is not present in ``VerbnetFrameOccurrence``.

The FrameNet fulltext corpus in stored in XML files which contain many
``sentence`` elements, each of which contains one or more frames. The text of
the sentence can be found in the ``text`` attribute, and each frame-specific
data is embed in an ``annotationSet`` element.
 
Neither the predicate nor any argument is expressed as text: what we recover
are the offset of the first and last characters of them (with the convention
that the first character's offset is 0).

* the frame's name can be recovered in the ``frameName`` attribute of the
  ``annotationSet`` element
* the predicate's lemma can be recovered in the ``luName`` attribute of the
  ``annotationSet`` element
* the predicate's start and end can be recovered in the ``layer`` element
  which name is ``Target``
* the arguments' starts, ends and correct roles can be recovered in the
  ``layer`` element which name is ``FE`` (Frame Elements)
* the arguments' phrase types can be recovered in the ``layer`` element which
  name is ``PT``. The only reliable sign that a ``label`` element in the PT
  ``layer`` refers to a given argument is that it has the same ``start`` and
  ``end`` attribute (ie, the order can differ).

Some arguments are marked as non-instanciated. In this case, the ``label``
element has an ``itype`` attribute, which value indicates the type of null
instanciation (this type is currently not taken into account). These arguments
are loaded into the frame structure but never used at any further point in the
program.

There are many other things that we have to be careful about:

* not every annotated frame is a verbal frame. All non-verbal frames are
  discarded. We used to identify verbal frames by checking that the
  ``luName`` attribute of the ``annotationSet`` element ends with ".v", but
  we realize that their are many cases were this yields strange results. We
  now use the part of speech annotations available in the PENN ``layer``,
  which can be equal to "MD", "VV", "VVD", "VVG", "VVN", "VVP" or "VVZ" for
  verbs.
* we need to attribute a sentence ID to every extracted frame, so that we can
  later recover syntactic data about it in the parsed corpus. Some sentences
  appears twice in the fulltext corpus, and there will be only one matching
  sentence in the parsed corpus. So the two identical sentence have to be
  given the same ID.
* some annotation sets are empty or incomplete. For these, the ``status``
  attribute of the ``annotationSet`` is set to ``UNANN``.
* 14 argument lack a matching phrase type label. In this case, we are forced
  to discard the frame.
* there are sometimes multiple layers of annotations with overlapping
  arguments. This is not a problem as long are every layer is fully
  annotated, which is not always the case. In 120 cases, a secondary layer
  lacks phrase type data.
* 35 frames do not contain any instanciated arguments. They are discarded
  during the frame-matching process.
* In 4 frames, the predicate itself is an argument. In this case, it is
  marked as non-instanciated by the FrameNet reader module.
* there is one frame whose name is "Test35" that needs to be discarded
* there is one frame for which the predicate data are missing
  
Also, the 705 frames which predicate cannot be found in any VerbNet class are
discarded.

LU corpus
`````````

The ``framenetreader`` module is also able to parse the Lexical Units corpus.
The task is nearly the same, except that the sentences are embed into
``subCorpus`` elements, and that the predicate's lemma and the frame's name
depend on the file and are therefore not specified in the frame data.  They can
be retrieved as the ``name`` and ``frame`` attribute of the file's root
element.

Core arguments
``````````````

The fulltext corpus lacks a way to distinguish core from non-core arguments.
Fortunately, the frame name is given for every frame, so what we have to do is
looking for this frame in the FrameNet frame index.

The list of core arguments for a frame is the set of every ``name`` attribute
of ``FE`` elements which ``coreType`` attribute is "Core" or "Core-Unexpressed"
in the frame XML file.

For efficiency reasons, the list of every frames' core arguments is computed at
the beginning of the script by the framenetcoreargs module.

There are no cases of mismatch of frame names or role names between the
fulltext corpus and the FrameNet frame index, except the discarded "Test35"
frame.
