Evaluation
==========

Evaluation is done on FrameNet and is the main reason as to why we're using
FrameNet annotated text. Basically, once the algorithm has assigned VerbNet
roles to syntactic chunks, we check that they are correct by mapping the manual
FrameNet annotation to VerbNet annotations.

Initial mappings
----------------

FrameNet verbs to possible Verbnet classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A number of FrameNet lexical units verbs don't appear in VerbNet, here is the
full list:

{'there be': 111, 'should': 66, 'do': 60, 'become': 58, 'may': 36, 'carry out':
21, 'ratify': 19, 'might': 19, 'lead_(to)': 19, 'deploy': 18, 'have to': 18,
'discuss': 15, 'arrest': 14, 'must': 14, 'cite': 13, 'set up': 8, 'belong': 8,
'have got': 8, 'reprocess': 7, 'decide': 7, 'born': 7, 'violate': 7,
'research': 7, 'utilise': 7, 'let': 6, 'refuse': 6, 'weaponize': 5, 'go on': 5,
'undergo': 5, 'lack': 4, 'make sure': 4, 'sentence': 4, 'end up': 4,
'forecast': 4, 'result_(in)': 4, 'invade': 4, 'process': 4, 'bring about': 4,
'vow': 4, 'renew': 4, 'defeat': 4, 'overthrow': 3, 'knock down': 3,
'talk_(to)': 3, 'drag on': 3, 'complement': 3, 'modify': 3, 'rape': 3,
'deserve': 3, 'come to a end': 2, 'comply': 2, 'tend': 2, 'thwart': 2,
'progress': 2, 'locate': 2, 'flight-test': 2, 'bring_together': 2,
'abide_((by))': 2, 'account': 2, 'defect': 2, 'restart': 2, 'contravene': 2,
'disable': 2, 'hold off': 2, 'resemble': 2, 'backstitch': 2, 'perpetrate': 2,
'bomb': 1, 'forget': 1, 'reinvigorate': 1, 'step up': 1, 'be_supposed_(to)': 1,
'cut short': 1, 'shield': 1, 'piece together': 1, 'get up': 1, 'wreak': 1,
'rebuff': 1, 'inhabit': 1, 'opt': 1, 'advocate': 1, 'birth': 1, 'quiet_down':
1, 'embark': 1, 'govern': 1, 'point (to)': 1, 'spit up': 1, 'contradict': 1,
'give_out': 1, 'propel': 1, 'sit down': 1, 'reinforce': 1, 'screw up': 1, 'make
up': 1, 'plead': 1, 'best': 1, 'educate': 1, 'emplace': 1, 'diddle': 1,
'besiege': 1, 'postpone': 1, 'dry up': 1, 'redirect': 1, 'fire off': 1, 'obey':
1, 'carry on': 1, 'distinguish': 1, 'substantiate': 1, 'set fire to': 1,
'equal': 1, 'ought to': 1, 'evoke': 1, 'smoke': 1, 'go away': 1, 'break out':
1, 'put an end to': 1, 'mouth': 1, 'authorize': 1, 'set off': 1, 'give rise':
1, 'count (on)': 1, 'disobey': 1, 'memorise': 1, 'bolster': 1, 'put together':
1, 'come together': 1, 'subvert': 1, 'sit up': 1, 'master': 1, 'meet with': 1,
'set out': 1, 'flight test': 1, 'descend_(on)': 1, 'reign': 1, 'ford': 1,
'lunge': 1, 'go_((through))': 1, 'sum up': 1, 'overrun': 1, 'word': 1, 'look
back': 1, 'back out': 1, 'turn out': 1, 'endanger': 1, 'take to the air': 1,
'jeopardise': 1, 'usher in': 1, 'come up': 1, 'attract': 1, 'proscribe': 1,
'jot down': 1, 'refute': 1, 'rout': 1, 'revisit': 1, 'ride_out': 1, 'answer':
1, 'lock up': 1, 'farm': 1, 'absorb': 1, 'await': 1, 'cater': 1, 'get ready':
1, 'come_(across)': 1, 'work together': 1, 'stymie': 1, 'remedy': 1, 'contact':
1, 'reshape': 1}

Observations:

 * We're happy that auxiliaries such as may, do, and should are present, since
   we don't want to deal with them.
 * This stems from one of VerbNet's most important design decision: only
   include frequent English verbs, which leads to a very useful lexicon for
   NLP. This explain why're we're missing out on a few long-tail verbs.
 * Indeed, 50% of occurrences come from 10% of verbs
 * 30% of verbs are particle verbs (that's not too much).
 * What's the difference between point (to) and abide ((by))?

FrameNet-VerbNet mapping
^^^^^^^^^^^^^^^^^^^^^^^^

This is done by using an existing VN-FN mapping provided by VerbNet. This
mapping is a possible source of errors but looks quite robust.

Frame-matching
--------------

Two metrics are of interest here: how precise our matchings are, and what
matching we missed.

Probability model
-----------------

TODO: Include the bias-variance analysis and link to it from "Ideas".

Bootstrapping
-------------

We still need to know how concerned we are with this, since it doesn't appear in 2005.
