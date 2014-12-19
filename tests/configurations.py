configurations = [
    ('gold', [],                                                                (71.11, 54.66)),
    ('gold + passive', ['--passivize'],                                         (73.52, 57.20)),
    ('gold + wordnetrestr', ['--wordnet-restrictions'],                         (71.64, 54.80)),
    ('gold + semrestr', ['--semantic-restrictions'],                            (75.84, 68.31)),
    ('gold + passivize + semrestr', ['--semantic-restrictions', '--passivize'], (78.38, 70.99)),
    ('gold + proba', ['--model=predicate_slot'],                                (71.84, 58.57)),
    ('gold + bootstrap', ['--bootstrap'],                                       (73.63, 69.41)),
    ('gold + bootstrap + passive + semrestr', ['--passivize', '--bootstrap', '--semantic-restrictions'], (79.41, 75.24)),

    ('argid', ['--argument-identification'],                                                                (42.92, 29.95)),
    ('argid + passive', ['--argument-identification', '--passivize'],                                       (44.28, 30.98)),
    ('argid + semrestr', ['--argument-identification', '--semantic-restrictions'],                          (43.75, 35.71)),
    ('argid + passive + semrestr', ['--argument-identification', '--passivize', '--semantic-restrictions'], (45.10, 36.88)),
    ('argid + proba', ['--argument-identification', '--model=predicate_slot'],                              (43.25, 31.52)),
    ('argid + bootstrap', ['--argument-identification', '--bootstrap'],                                     (44.63, 37.98)),
    ('argid + bootstrap + passive + semrestr', ['--argument-identification', '--bootstrap', '--passivize', '--semantic-restrictions'], (45.92, 39.22)),
]
