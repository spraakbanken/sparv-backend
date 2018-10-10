# -*- coding: utf-8 -*-

from __future__ import print_function
from utils import TOOL_DICT
from collections import OrderedDict
import json
import logging

log = logging.getLogger('pipeline.' + __name__)


def make_schema(lang, mode, minify=False):
    """Build settings schema json."""

    # Get analysis mode from TOOL_DICT
    analysis = TOOL_DICT.get(lang, "sv")

    schema = OrderedDict([
        ("struct_tag", struct_tag),
        ("struct_tag_simple", struct_tag_simple),
        ("title", "Corpus pipeline makefile settings"),
        ("title_sv", "Makefilsinställningar till korpusimportkedjan"),
        ("documentation", "Settings that generate the Makefile for the corpus pipeline"),
        ("type", "object"),
        ("properties", OrderedDict([
            ("corpus", corpus),
            ("lang", lang_prop(lang)),
            ("textmode", textmode_prop(mode)),
            ("word_segmenter", word_segmenter(mode, analysis)),
            ("sentence_segmentation", sentence_segmentation(mode, analysis)),
            ("paragraph_segmentation", paragraph_segmentation(mode, analysis)),
            ("root", root(mode)),
            ("extra_tags", extra_tags(mode)),
            ("positional_attributes", positional_attributes(lang, analysis)),
            ("named_entity_recognition", named_entity_recognition(lang)),
            ("text_attributes", text_attributes(lang))
        ]))
    ])
    # Remove entries with None values
    [i for i in remove_nones(schema)]

    if minify:
        # Remove entries from json which are note valid
        # according to https://tools.ietf.org/html/draft-wright-json-schema-validation-00
        for k in ["title_sv", "description_sv", "class", "documentation"]:
            [i for i in remove_key(k, schema)]
    else:
        # Add list with object order to all OrderedDicts
        [i for i in add_order(schema)]

    return schema


struct_tag = {
    "title": "Structural element tag",
    "title_sv": "Strukturellt-element-tagg",
    "description": "A tag for a structral element",
    "description_sv": "En tagg för ett strukturellt element",
    "type": "object",
    "properties": OrderedDict([
        ("tag", {
            "title": "Tag",
            "title_sv": "Tagg",
            "description": "The identifer of the tag in the XML",
            "description_sv": "Taggens identifierare i XML:en",
            "type": "string"
        }),
        ("attributes", {
            "title": "Structural attributes",
            "title_sv": "Strukturella attribut",
            "description": "The attributes of this tag in the XML",
            "description_sv": "Attribut inom den taggen som ska fångas in från XML:en",
            "type": "array",
            "default": [],
            "items": {
                "title": "Structural attribute",
                "title_sv": "Strukturellt attribut",
                "type": "string"
            }
        })
    ])
}

struct_tag_simple = {
    "title": "Costum attribute tag",
    "title_sv": "Egen attribut-tagg",
    "description": "Attribute tag which segmentation is based on",
    "description_sv": "Attribut-tagg som segmenteringen är baserad på",
    "type": "string"
}

corpus = {
    "title": "Corpus name",
    "title_sv": "Korpusnamn",
    "description": "The corpus identifier",
    "description_sv": "Korpusidentifierare",
    "default": "untitled",
    "type": "string"
}


def lang_prop(lang):
    # This property will be hidden in the form
    # because the enum contains only one value
    return {
        "title": "Analysis mode",
        "title_sv": "Analysmode",
        "default": lang,
        "enum": [lang],
        "type": "string"
    }


def textmode_prop(mode):
    # This property will be hidden in the form
    # because the enum contains only one value
    return {
        "title": "Text input mode",
        "title_sv": "Textläge",
        "description": "Input format for the pipeline",
        "description_sv": "Indataformatet till importkedjan",
        "default": mode,
        "enum": [mode],
        "type": "string"
    }


def word_segmenter(mode, analysis):
    if analysis == "fl":
        return None

    word_segmenter_tool = {
        "title": "Segmenter",
        "title_sv": "Segmenterare",
        "description": "Segmenter tool to use for words",
        "description_sv": "Modellen/verktyget som ska användas till ordsegmenteringen",
        "type": "string",
        "enum": ["whitespace", "linebreaks", "blanklines", "default_tokenizer"],
        "class": "typewriter"
    }

    word_segmenter_tag = {
        "title": "Word tag",
        "title_sv": "Ordtagg",
        "type": "object",
        "properties": OrderedDict([
            ("tag", {
                "title": "Tag",
                "title_sv": "Tagg",
                "description": "The identifer of the tag for words in the XML",
                "description_sv": "Identifieraren för ord-taggen i XML:en",
                "type": "string"
            }),
            ("attributes", {
                "title": "Positional attributes",
                "title_sv": "Positionella attribut",
                "description": "The identifer of the attributes of the word tags in the XML",
                "description_sv": "Attribut inom ord-taggen som ska fångas in",
                "type": "array",
                "default": [],
                "items": {
                    "title": "Positional attribute",
                    "title_sv": "Positionellt attribut",
                    "description": "A positional attribute in the word tag",
                    "description_sv": "Ett positionellt attribut i ordtaggen",
                    "type": "object",
                    "properties": {
                        "key": {
                            "title": "Key",
                            "title_sv": "Nyckel",
                            "description": "The name of the attribute in the XML",
                            "description_sv": "Attributets namn i XML:en",
                            "type": "string"
                        },
                        "attribute": {
                            "title": "Positional attribute",
                            "description": "Custom means that this is a new kind of positional attribute. Choosing any other means that it replaces what could otherwise be generated by a tool.",
                            "description_sv": "Välj 'nytt attribut' om det inte finns ett verktyg för den typen av analys. Om du väljer en av de andra alternativ så kommer det inte genereras en automatisk analys av samma typ.",
                            "type": "string",
                            "enum": ["custom", "pos", "msd", "lemma", "lex", "sense", "prefix", "suffix", "ref", "dephead", "deprel"],
                            "enum_loc": {
                                "en": {
                                    "custom": "custom attribute"
                                },
                                "sv": {
                                    "custom": "nytt attribut"
                                }
                            },
                            "style_enum": "dropdown"
                        }
                    }
                }
            })]
        )
    }

    if mode != "plain":
        segmenter_type = [word_segmenter_tool, word_segmenter_tag]
    else:
        segmenter_type = [word_segmenter_tool]

    return {
        "title": "Word segmentation",
        "title_sv": "Ordsegmentering",
        "description": "Word segmenter to use, or a tag optionally supplied with positional attributes",
        "description_sv": "Ordsegmenterare som ska användas, eller en tagg med valfria positionella attribut",
        "default": "default_tokenizer",
        "type": segmenter_type
    }


def sentence_segmentation(mode, analysis):
    if analysis == "fl":
        return None
    if mode != "plain":
        segmenter_type = [sentence_segmenter_tool(mode), struct_tag]
    else:
        segmenter_type = [sentence_segmenter_tool(mode)]

    return {
        "title": "Sentence segmentation",
        "title_sv": "Meningssegmentering",
        "description": "Sentence segmenter to use, or a tag supplied with optional sentence attributes",
        "description_sv": "Meningssegmenterare som ska användas, eller en tagg med valfria menings-attribut",
        "default": {"sentence_segmenter": "default_tokenizer",
                    "sentence_chunk": "paragraph"},
        "type": segmenter_type
    }


def sentence_segmenter_tool(mode):
    sentence_chunk = {
        "title": "Pre-defined attribute",
        "title_sv": "Fördefinerad attribut",
        "type": "string",
        "enum": ["text", "paragraph"],
        "class": "typewriter"
    }

    if mode != "plain":
        chunk_type = [sentence_chunk, struct_tag_simple]
    else:
        chunk_type = [sentence_chunk]

    return {
        "title": "Segmenter",
        "title_sv": "Segmenterare",
        "default": "default_tokenizer",
        "type": "object",
        "properties": OrderedDict([
            ("sentence_segmenter", {
                "title": "Segment by",
                "title_sv": "Segmentera med",
                "description": "Segmenter tool to use for sentences",
                "description_sv": "Modellen/verktyget som ska användas till meningssegmenteringen",
                "type": "string",
                "default": "default_tokenizer",
                "enum": ["whitespace", "linebreaks", "blanklines", "default_tokenizer", "punctuation"],
                "class": "typewriter"
            }),
            ("sentence_chunk", {
                "title": "Sentence chunk",
                "title_sv": "Meningschunk",
                "description": "Chunk which the sentence segmentation should be based on",
                "description_sv": "Chunk som meningssegmenteringen ska baseras på",
                "default": "paragraph",
                "type": chunk_type
            })
        ])
    }


def paragraph_segmentation(mode, analysis):
    if analysis == "fl":
        return None

    no_segmentation = {
        "title": "No segmentation",
        "title_sv": "Ingen segmentering",
        "description": "Use this if there are no sensible paragraphs in the text",
        "description_sv": "Använd detta alternativ om det inte finns några rimliga stycken i texten",
        "type": "string",
        "default": "none",
        "enum": ["none"]
    }

    if mode != "plain":
        segmenter_type = [paragraph_segmenter_tool(mode), struct_tag, no_segmentation]
    else:
        segmenter_type = [paragraph_segmenter_tool(mode), no_segmentation]

    return {
        "title": "Paragraph segmentation",
        "title_sv": "Styckessegmentering",
        "description": "Paragraph segmenter to use, or a tag supplied with optional structural attributes",
        "description_sv": "Styckessegmenterare som ska användas, eller en tagg med valfria strukturella attribut",
        "default": {"paragraph_segmenter": "blanklines",
                    "paragraph_chunk": "root"} if mode != "plain" else {"paragraph_segmenter": "blanklines"},
        "type": segmenter_type
    }


def paragraph_segmenter_tool(mode):
    return {
        "title": "Segmenter",
        "title_sv": "Segmenterare",
        "default": "blanklines",
        "type": "object",
        "properties": {
            "paragraph_segmenter": {
                "title": "Segment by",
                "title_sv": "Segmentera med",
                "description": "Segmenter tool to use for paragraphs",
                "description_sv": "Modellen/verktyget som ska användas till styckessegmenteringen",
                "type": "string",
                "default": "blanklines",
                "enum": ["whitespace", "linebreaks", "blanklines"],
                "class": "typewriter"
            },
            "paragraph_chunk": {
                "title": "Paragraph chunk",
                "title_sv": "Styckeschunk",
                "description": "Chunk which the paragraph segmentation is based on",
                "description_sv": "Chunk som styckessegmenteringen är baserad på",
                "default": "root",
                "type": [
                    {
                        "title": "Document element",
                        "title_sv": "Dokumentelement",
                        "type": "string",
                        "enum": ["root"],
                        "class": "typewriter"
                    },
                    {"$ref": "#/struct_tag_simple"}
                ]
            } if mode != "plain" else None
        }
    }


def root(mode):
    if mode != "plain":
        return {
            "title": "Document element",
            "title_sv": "Dokumentelement",
            "description": "The name of the document element, with optional attributes",
            "description_sv": "Namnet på dokumentelementet, med valfria attribut",
            "default": {
                "tag": "text",
                "attributes": []
            },
            "type": [
                {"$ref": "#/struct_tag"}
            ]
        }
    else:
        return None


def extra_tags(mode):
    if mode != "plain":
        return {
            "title": "Extra structural elements",
            "title_sv": "Ytterligare strukturella element",
            "description": "Additional structural elements in the XML",
            "description_sv": "Ytterligare strukturella element i XML:en",
            "type": "array",
            "default": [],
            "items": {
                "$ref": "#/struct_tag"
            }
        }
    else:
        return None


def positional_attributes(lang, analysis):
    if lang == "sv-dev":
        lexical_attrs = ["pos", "msd", "lemma", "lex", "sense"]
        compound_attrs = default_compound_attrs = ["complemgram", "compwf"]
        dependency_attributes = ["ref", "dephead", "deprel"]
        lexical_classes = ["blingbring", "swefn"]
        sentiment = ["sentiment", "sentimentclass"]
    elif analysis in ["sv", "sv-1800"]:
        lexical_attrs = ["pos", "msd", "lemma", "lex", "sense"]
        compound_attrs = ["complemgram", "compwf", "prefix", "suffix"]
        default_compound_attrs = ["complemgram", "compwf"]
        dependency_attributes = ["ref", "dephead", "deprel"]
        lexical_classes = None
        sentiment = ["sentiment", "sentimentclass"]
    else:  # analysis in ["fl", "tt"]
        lexical_attrs = ["pos", "msd", "lemma"]
        compound_attrs = default_compound_attrs = None
        dependency_attributes = None
        lexical_classes = None
        sentiment = None

    return {
        "title": "Positional attributes",
        "title_sv": "Positionella attribut",
        "description": "Positional attributes to generate in the analysis. Attributes already present in the word tag must not appear here again.",
        "description_sv": "Positionella attribut som ska genereras i analysen. Attribut som har valts under 'ordtagg' får inte förekomma här.",
        "type": "object",
        "default": OrderedDict([
            ("lexical_attributes", lexical_attrs),
            ("compound_attributes", default_compound_attrs),
            ("dependency_attributes", dependency_attributes),
            ("lexical_classes", lexical_classes),
            ("sentiment", sentiment)
        ]),
        "properties": OrderedDict([
            ("lexical_attributes", {
                "title": "Lexical analysis",
                "title_sv": "Lexikalanalys",
                "description": "Attributes for the lexical analysis",
                "description_sv": "Attribut för lexikalanalysen",
                "type": "array",
                "default": lexical_attrs,
                "items": {
                    "title": "Lexical attribute",
                    "type": "string",
                    "enum": lexical_attrs
                }
            }),

            ("compound_attributes", {
                "title": "Compound analysis",
                "title_sv": "Sammansättningsanalys",
                "description": "Attributes for the compound analysis",
                "description_sv": "Attribut för sammansättningsanalysen",
                "type": "array",
                "default": compound_attrs,
                "items": {
                    "title": "Compound attribute",
                    "type": "string",
                    "enum": compound_attrs
                }
            } if analysis in ["sv", "sv-dev", "sv-1800"] else None),

            ("dependency_attributes", {
                "title": "Dependency analysis",
                "title_sv": "Dependensanalys",
                "description": "Attributes for the dependency analysis",
                "description_sv": "Attribut för dependsanalysen",
                "type": "array",
                "default": dependency_attributes,
                "items": {
                    "title": "Dependency attribute",
                    "type": "string",
                    "enum": dependency_attributes
                }
            } if analysis in ["sv", "sv-dev", "sv-1800"] else None),

            ("lexical_classes", {
                "title": "Lexical classes",
                "title_sv": "Lexikala klasser",
                "description": "Attributes for lexical classes",
                "description_sv": "Attribut för lexikala klasser",
                "type": "array",
                "default": lexical_classes,
                "items": {
                    "title": "Lexical class attribute",
                    "type": "string",
                    "enum": lexical_classes
                }
            } if lang == "sv-dev" else None),

            ("sentiment", {
                "title": "Sentiment analysis",
                "title_sv": "Attitydanalys",
                "description": "Attributes for sentiment analysis",
                "description_sv": "Attribut för attitydanalysen",
                "type": "array",
                "default": sentiment,
                "items": {
                    "title": "Sentiment attribute",
                    "type": "string",
                    "enum": sentiment
                }
            } if lang in ["sv", "sv-dev", "sv-1800"] else None)
        ]),
    }


def named_entity_recognition(lang):
    if lang in ["sv", "sv-dev", "sv-1800"]:
        return {
            "title": "Named entity recognition",
            "title_sv": "Namntaggare",
            "description": "Structural attributes for named entity recognition",
            "description_sv": "Strukturella attribut for namnigenkänning",
            "default": ["ex", "type", "subtype"] if lang == "sv-dev" else [],
            "type": "array",
            "items": {
                "title": "Named entity attribute",
                "type": "string",
                "enum": ["ex", "type", "subtype"]
            }
        }
    else:
        return None


def text_attributes(lang):
    return {
        "title": "Text attributes",
        "title_sv": "Textattribut",
        "description": "Text attributes to generate in the analysis. Attributes already present under 'Document element > Structural attributes' must not appear here again.",
        "description_sv": "Textattribut som ska genereras i analysen. Attribut som har valts under 'Dokumentelement > Strukturella attribut' får inte förekomma här.",
        "type": "object",
        "default": OrderedDict([
            ("readability_metrics", ["lix", "ovix", "nk"]),
            ("lexical_classes", ["blingbring", "swefn"] if lang == "sv-dev" else None)
        ]),
        "properties": OrderedDict([
            ("readability_metrics", {
                "title": "Readability metrics",
                "title_sv": "Läsbarhetsvärden",
                "description": "Attributes for different readability metrics",
                "description_sv": "Attribut för olika sorters läsbarhetsvärden",
                "type": "array",
                "default": ["lix", "ovix", "nk"],
                "items": {
                    "title": "Readability attribute",
                    "type": "string",
                    "enum": ["lix", "ovix", "nk"]
                }
            }),
            ("lexical_classes", {
                "title": "Lexical classes (document)",
                "title_sv": "Lexikala klasser (dokument)",
                "description": "Attributes for lexical classes on document level",
                "description_sv": "Attribut för lexikala klasser på dokumentnivå",
                "type": "array",
                "default": ["blingbring", "swefn"],
                "items": {
                    "title": "Lexical class attribute",
                    "type": "string",
                    "enum": ["blingbring", "swefn"]
                }
            } if lang == "sv-dev" else None)
        ])
    }


def remove_nones(json_input, parent_key=None):
    """Recursively remove all keys which have value None."""
    if isinstance(json_input, dict):
        for k, v in list(json_input.items()):
            if v is None:
                json_input.pop(k)
            else:
                for child_val in remove_nones(v, k):
                    yield child_val
    elif isinstance(json_input, list):
        for item in json_input:
            if item is None:
                json_input.remove(item)
            for item_val in remove_nones(item, parent_key):
                yield item_val


def remove_key(key, json_input, parent_key=None):
    """Recursively remove all instances of 'key'."""
    if isinstance(json_input, dict):
        for k, v in list(json_input.items()):
            if k == key:
                json_input.pop(k)
            else:
                for child_val in remove_key(key, v, k):
                    yield child_val
    elif isinstance(json_input, list):
        for item in json_input:
            if item == key:
                json_input.remove(item)
            for item_val in remove_key(key, item, parent_key):
                yield item_val


def add_order(json_input):
    if isinstance(json_input, OrderedDict):
        json_input["order"] = []
        for k, v in json_input.items():
            if k != "order":
                json_input["order"].append(k)
            for child_val in add_order(v):
                yield child_val
    elif isinstance(json_input, dict):
        for k, v in json_input.items():
            for child_val in add_order(v):
                yield child_val


if __name__ == '__main__':
    # For testing purposes
    schema = make_schema("sv", "plain")
    print(json.dumps(schema, indent=4, separators=(',', ': '), ensure_ascii=False))
