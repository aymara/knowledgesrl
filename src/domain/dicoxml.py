"""
Helpers to manage the way dicoinfo and dicoenviro are represented as XML
"""


def deindent_text(sentence_text):
    """
    Deindent text found in the indent XML files.

    'Long   sentence\n      cut' would become 'Long   sentence cut'
    """

    mode = 'keep'
    last_real_char = ''
    origin_sentence = ''

    for c in sentence_text:
        if c == '\n':
            mode = 'throw away'
        else:
            if mode == 'keep':
                origin_sentence += c
                last_real_char = c
            elif mode == 'throw away':
                if c != ' ':
                    mode = 'keep'
                    if last_real_char != '':
                        origin_sentence += ' '
                    origin_sentence += c
                    last_real_char = c

    return origin_sentence


def get_all_text(elem, get_tail=False):
    if elem is None:
        return ''

    all_text = elem.text if elem.text else ''

    for c in elem:
        all_text += get_all_text(c, get_tail=True)

    if get_tail:
        all_text += elem.tail if elem.tail else ''
    else:
        all_text = deindent_text(all_text)

    return all_text

