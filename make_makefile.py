# Makes a makefile from a JSON object that validates the schema

import re
import json
from utils import TOOL_DICT
import logging
log = logging.getLogger('pipeline.' + __name__)

DEFAULT_ROOT = "text"

######################################
#    Different auxiliary functions   #
def is_str_str_tuple(t):
    """Is this object is a tuple of two strings?"""
    return (isinstance(t, tuple) and len(t) == 2
            and isinstance(t[0], basestring)
            and isinstance(t[1], basestring))


def linearise_Makefile(content):
    res = []
    for i in content:
        if isinstance(i, basestring):
            res.append(i)
        elif is_str_str_tuple(i):
            res.append("%s = %s" % (i[0], i[1]))
        elif isinstance(i, list):
            res += align_table([[k, "="] + v for (k, v) in i])
        else:
            raise TypeError(str(i) + " is neither string, tuple (of str * str) or list!")
    return '\n'.join(res)


def align_table(rows, empty="-"):
    max_row_len = max(map(len, rows) + [0])
    rows = [row + [empty] * (max_row_len - len(row)) for row in rows]
    cols = zip(*rows)
    col_widths = [max(map(len, col)) for col in cols]
    fmt = ' '.join('{%s:<%s}' % (ix, width)
                   for ix, width
                   in zip(xrange(len(cols)), col_widths))
    return [fmt.format(*row) for row in rows]


def makefile_comment(s):
    """Makes a string to a valid makefile comment"""
    return "\n".join(map(lambda l: "# " + l, s.split("\n")))


def add_parent(tag, parents):
    parents.append("token|" + tag)


def mk_xml_attr(tag, attr):
    return tag + ":" + attr


def mk_file_attr(tag, attr):
    return tag + "." + attr


def add_attribute(tag, attr, xml_cols, structs, columns, structural=False, filename=None, add_xml=True):
    filename = filename or tag
    xml_attr = mk_xml_attr(filename, attr)
    file_attr = mk_file_attr(tag, attr)
    struct_attr = mk_xml_attr(filename, attr)
    if add_xml:
        xml_cols.append((xml_attr, file_attr))
    if structural:
        structs.append((file_attr, struct_attr))
    else:
        columns.append((file_attr, struct_attr))


def make_token(settings, columns, xml_cols):
    """Fix word (token) segmentation. """
    ws = settings['word_segmenter']
    if ws == "default_tokenizer":
        ws = "better_word"
    if isinstance(ws, basestring):
        """Example:
            word_segmenter: "punkt_word"
        """
        return ([("token_chunk", "sentence"),
                 ("token_segmenter", ws)])
    else:
        """Example:
            word_segmenter: { tag: "w",
                              attributes: { pos: "msd", "language": null }
                            }
        """
        # Adds w -> token in xml
        xml_cols.append((ws['tag'], "token"))
        for e in ws['attributes']:
            key = e['key']
            replace = e['attribute']
            if replace != "custom":
                # Adds w:pos -> msd in xml
                if replace == "dephead":
                    replace += ".ref"
                xml_cols.append((mk_xml_attr(ws['tag'], key),
                                 mk_file_attr('token', replace)))
            else:
                # Adds w:language -> token.language in xml and
                #      token.language -> language in columns
                xml_cols.append((mk_xml_attr(ws['tag'], key),
                                 mk_file_attr('token', key)))
                columns.append((mk_file_attr('token', key), key))
        return [makefile_comment("Using tag " + ws['tag'] + " for words")]


def make_sentence(settings, parents, xml_cols, structs, columns):
    """Extract info from sentence_segmentation. """
    if settings['sentence_segmentation'].get("sentence_segmenter"):
        sentence_segmenter = settings['sentence_segmentation']["sentence_segmenter"]
        if sentence_segmenter == "default_tokenizer":
            sentence_segmenter = "punkt_sentence"
    else:
        sentence_segmenter = settings['sentence_segmentation']
    if settings['sentence_segmentation'].get('sentence_chunk'):
        sentence_chunk = settings['sentence_segmentation']['sentence_chunk']
    else:
        sentence_chunk = None
    return add_segmenter(sentence_segmenter, "sentence", sentence_chunk, parents, xml_cols, structs, columns)


def make_paragraph(settings, text, parents, xml_cols, structs, columns):
    """Extract info from paragraph_segmentation. """
    if settings.get('paragraph_segmentation') != "none":
        # add the structural attribute paragraph.n if there is segmentation
        structs.append(('paragraph.n', 'paragraph'))
        if settings['paragraph_segmentation'].get("paragraph_segmenter"):
            paragraph_segmenter = settings['paragraph_segmentation']['paragraph_segmenter']
        else:
            paragraph_segmenter = settings['paragraph_segmentation']
        if settings['paragraph_segmentation'].get('paragraph_chunk'):
            paragraph_chunk = settings['paragraph_segmentation']['paragraph_chunk']
            if paragraph_chunk == "root":
                paragraph_chunk = text
        else:
            paragraph_chunk = None
        return add_segmenter(paragraph_segmenter, "paragraph", paragraph_chunk, parents, xml_cols, structs, columns)
    else:
        return add_segmenter("none", "paragraph", None, parents, xml_cols, structs, columns)


def add_segmenter(setting, name, chunk, parents, xml_cols, structs, columns):
    """For sentence and paragraph segmentation. """
    if setting == "none":
        return [makefile_comment("No segmentation for " + name)]
    if isinstance(setting, basestring):
        res = [(name + "_chunk", chunk),
               (name + "_segmenter", setting)]
        return res
    else:
        """Example
            sentence_segmenter: { tag: "s",
                                  attributes: ["mood", "id"]
                                }
        """
        xml_cols.append((setting['tag'], name))
        add_parent(name, parents)
        for attr in setting['attributes']:
            add_attribute(setting['tag'], attr,
                          xml_cols,
                          structs,
                          columns,
                          structural=True,
                          filename=name)
        return [makefile_comment("Using tag " + setting['tag'] + " for " + name)]
######################################


def make_Makefile(settings):
    """
        Construct a makefile from a dictionary of settings, which should be
        validated against the schema in settings_schema_*.json.
    """
    if settings.get('lang'):
        lang = settings.get('lang')
    else:
        lang = 'sv'
    analysis = TOOL_DICT[lang]

    # vrt_columns[_annotations] as column-by-column, initially with default settings

    if analysis == ("tt" or "fl"):
        columns = [('word', 'word'),
                   ('pos', 'pos'),
                   ('msd', 'msd'),
                   ('baseform', 'lemma')]

    elif analysis == "sv-dev":
        columns = [('word', 'word'),
                   ('pos', 'pos'),
                   ('msd', 'msd'),
                   ('baseform', 'lemma'),
                   ('lemgram', 'lex'),
                   ('sense', 'sense'),
                   ('complemgram', 'complemgram'),
                   ('lemprob', 'lemprob'),
                   ('compwf', 'compwf'),
                   ('ref', 'ref'),
                   ('dephead.ref', 'dephead'),
                   ('deprel', 'deprel')]

    else:
        columns = [('word', 'word'),
                   ('pos', 'pos'),
                   ('msd', 'msd'),
                   ('baseform', 'lemma'),
                   ('lemgram', 'lex'),
                   ('saldo', 'saldo'),
                   ('prefix', 'prefix'),
                   ('suffix', 'suffix'),
                   ('ref', 'ref'),
                   ('dephead.ref', 'dephead'),
                   ('deprel', 'deprel')]

    # vrt_structs[_annotations]
    structs = []

    # Remove positional attributes that should not be generated
    if lang in ["sv", "sv-dev", "sv-1800"]:
        columns = [c for c in columns if c[1] in settings['positional_attributes']['lexical_attributes']
                   or c[1] in settings['positional_attributes']['compound_attributes']
                   or c[1] in settings['positional_attributes']['dependency_attributes']]
    else:
        columns = [c for c in columns if c[1] in settings['positional_attributes']['lexical_attributes']]

    # Add obligatory word annotation
    columns.insert(0, ('word', 'word'))

    # The root tag
    text = settings['root']['tag']

    # Initial parents. All tags are assumed to have the root node as parent
    parents = []

    # xml_elements and xml_annotations as column-by-column
    xml_cols = []

    # custom rules (used for dephead.ref)
    custom_rules = []

    # Fix token segmentation
    if analysis != 'fl':
        token = make_token(settings, columns, xml_cols)
    else:
        token = []

    # Add named entity recognition attributes
    if settings.get('named_entity_recognition'):
        for i in settings.get('named_entity_recognition'):
            structs.append(("ne." + i, "ne:" + i))

    # Add the obligatory structural attribute sentence.id
    structs.append(('sentence.id', 'sentence:id'))

    # Fix sentence and paragraph segmentation
    if analysis != 'fl':
        sentence = make_sentence(settings, parents, xml_cols, structs, columns)
        paragraph = make_paragraph(settings, text, parents, xml_cols, structs, columns)
    else:
        sentence = []
        paragraph = []

    def add_structural_attributes(tag, attributes, add_xml=False, is_root=False):
        if add_xml:
            if is_root:
                xml_cols.append((tag, DEFAULT_ROOT))
            else:
                xml_cols.append((tag, tag))
        if len(attributes) > 0:
            add_parent(tag, parents)
            if is_root:
                filename = tag
                tag = DEFAULT_ROOT
            else:
                tag = tag
                filename = None
            for attr in attributes:
                add_attribute(tag, attr, xml_cols, structs, columns,
                              structural=True, filename=filename, add_xml=add_xml)

    # Extra tags
    if settings.get('extra_tags'):
        for t in settings['extra_tags']:
            add_structural_attributes(t['tag'], t['attributes'], add_xml=True)

    # Add text attributes
    if settings.get('text_attributes'):
        if "readibility_metrics" in settings['text_attributes']:
            add_structural_attributes(text, settings['text_attributes']['readibility_metrics'], is_root=True)

    # Add the root tag to xml and its attributes
    add_structural_attributes(text, settings['root']['attributes'], add_xml=True, is_root=True)

    # Add freeling xml annotations  # FreeLing
    if analysis == "fl":  # FreeLing
        xml_cols.extend([("s", "sentence"), ("w", "token"), ("w:pos", "token.pos"), ("w:msd", "token.msd"), ("w:lemma", "token.baseform")])  # FreeLing

    # Assemble the makefile
    rows = (["include $(SPARV_MAKEFILES)/Makefile.config",
            ("corpus", settings['corpus']),  # TODO: escaping of non-filename characters!
            ("original_dir", "original")
             ])

    # Add language and analysis mode if necessary
    if lang not in ["sv", "sv-dev", "sv-1800"]:
        rows.extend([("lang", lang),
                     ("analysis", analysis)])

    if lang == "sv-1800":
        rows.extend([("analysis", analysis)])

    rows.extend(["",
                 zip(["vrt_columns_annotations", "vrt_columns"], map(list, zip(*columns))),
                 "",
                 zip(["vrt_structs_annotations", "vrt_structs"], map(list, zip(*structs))),
                 "",
                 zip(["xml_elements", "xml_annotations"], map(list, zip(*xml_cols))),
                 ""])

    # Avoid missing parents warning for named entity recognition
    if settings.get('named_entity_recognition'):
        rows.extend([("ignore_missing_parents", "True"), ""])

    if analysis != 'fl':
        rows.extend(token + [""])
        rows.extend(sentence + [""])
        rows.extend(paragraph + [""])

    custom_rule_names = map(lambda t: t[0], custom_rules)
    if len(custom_rule_names) > 0:
        for custom in custom_rules:
            rows += [makefile_comment("Custom rule for " + custom[0] + ":"), custom[1], ""]

    # Add xml custom rule for freeling languages  # FreeLing
    if analysis == "fl":  # FreeLing
        custom_rule_names.append("xml")  # FreeLing

    if len(custom_rule_names) > 0:
        rows += [("custom_rules", ' '.join(custom_rule_names)), ""]

    rows.extend(["include $(SPARV_MAKEFILES)/Makefile.rules"])

    return rows


def makefile(d):
    """Wrapper function for make_Makefile."""
    return str(linearise_Makefile(make_Makefile(d)))


##########################################
if __name__ == '__main__':
    import sb.util

    def jsjson_to_json(s):
        """JavaScript JSON to JSON (as strings)"""
        def stringifyKeys(s):
            return re.sub(r'(\w+):', r'"\1":', s)

        return '\n'.join(filter(lambda l: "//" not in l,
                                map(stringifyKeys, s.split('\n'))))

    def json_to_Makefile(filename):
        """Make a makefile from a javascript json description in filename"""
        with open(filename, "r") as f:
            initial_json = f.read()

        settings = json.loads(jsjson_to_json(initial_json))

        sb.util.log.info("Writing Makefile...")
        with open("Makefile", "w") as f:
            f.write(makefile(settings))
        sb.util.log.info("... done!")

    sb.util.run.main(json_to_Makefile)
