Resources parsing
=================

VerbNet parsing
---------------

The parsing of VerbNet is done by the *verbnetreader* module. It reads every XML file in data/verbnet3-2, each of which represents a VerbNet root class and all its subclasses.

For each frame found in every class and subclasses of a file, a *VerbNetFrame* object is instanciated and associated with every member verbs of the class or one of its subclasses.

The difficult part is to build the structure and the role list of the *VerbNetFrame*, that is, to convert the *primary* attribute of the *DESCRIPTION* element to an acceptable (that is, compatible with FrameNet annotations) list of syntactic elemenst, and to retrieve the roles of the elements that have one.

The following operations are applied to the elements of the *primary* attribute :
  * everything that is after a "." or a "-" is removed (for instance, NP.theme becomes NP, S-Quote becomes S)
  * adverbs are removed from the structure (not handled yet)
  * "v" is replaced by "V" (no distinction between transitive and non-transitive verbs needed)
  * "a/b" is interpreted as [a or b].
  * every keyword is made explicit. That means that "S_INF" is replaced by "to S" and more importantly, "PP" is replaced by "prep NP".
  
In order to know which preposition can be used in a PP, which is not always explicit in the primary structure, we look into the *SYNTAX* element of the frame. The information can take three different forms :
  * a *LEX* element, which *value* attribute is the only acceptable preposition
  * a *PREP* element whith a *value* attribute, which is the only acceptable preposition
  * a *PREP* element whitout *value* attribute, but which contains selective restrictions data. In this case, the *type* attribute of the SELRESTRS/SELREST element is the class of acceptable prepositions

The constructed structure is the list of everything that will have an importance in the frame matching, that is NP, V, S and also every required keywords (which, as, ...) and prepositions. Those emplacements are represented by string unless there are several possibilities (for instance, when a class of preposition can introduced a NP). In that case, the element is represented by the list of every acceptable string.

The role list is simpler to build. We just need to retrieve the *value* attribute of every element of *SYNTAX* which has such a *value* attribute, and is not a *VERB*, *LEX* or *PREP*.

FrameNet parsing
----------------
