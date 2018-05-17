# Introduction
Sparv is [Språkbanken's](https://spraakbanken.gu.se/eng) annotation tool and
contains a corpus import pipeline and a web service including a web interface.
Sparv's API is available at [`[SBURL]`]([SBURL]).

This documentation is for API version [VERSION].


# Queries for Annotating Texts
Queries to the web service can be sent as a simple GET request:

[`[SBURL]?text=En+exempelmening+till+nättjänsten`]([SBURL]?text=En+exempelmening+till+nättjänsten)

POST requests are also supported using the same address. This can be useful for longer texts.
Here is an example using curl:

```.bash
curl -X POST --data-binary text="En exempelmening till nättjänsten" [SBURL]
```

The response from the POST request is the same as for the above GET request. See [default query](#default-query) for more details.

It is also possible to upload text or XML files using curl:

```.bash
curl -X POST -F files[]=@/path/to/file/myfile.txt [SBURL]upload?
```

In this case the response is a download link to a zip file containing the annotation.


# Settings
The web service supports some costum settings, e.g. it lets you chose
between different tokenizers on word, sentence, and paragraph level
and you can define which annotations should be generated. Via the settings you
can also chose the language of your input and you can define whether your input
is in xml or plain text.

These settings are provided as a JSON object to the `settings` variable.
This object must satisfy the JSON schema available at the following adress:

[`[SBURL]schema?language=sv&mode=plain`]([SBURL]schema?language=sv&mode=plain)

The schema holds default values for all the attributes. The use of the settings
variable is therefore optional.

A request which only generates a dependency analysis could look like this:

[`[SBURL]?text=Det+trodde+jag+aldrig.&settings={"positional_attributes":{"dependency_attributes":["ref","dephead","deprel"],"lexical_attributes":[],"compound_attributes":[]}}`]([SBURL]?text=Det+trodde+jag+aldrig.&settings={"positional_attributes":{"dependency_attributes":["ref","dephead","deprel"],"lexical_attributes":[],"compound_attributes":[]}})

Or as a POST request using curl:

```.bash
curl -X POST -g --data-binary text="Det trodde jag aldrig." '[SBURL]?settings={"positional_attributes":{"dependency_attributes":["ref","dephead","deprel"],"lexical_attributes":[],"compound_attributes":[]}}'
```

If you are not sure how to define the settings variable you can check the [example settings](#example-settings)
or you can get help from the [frontend](https://spraakbanken.gu.se/sparv) by clicking
`Show JSON Settings` under `Show advanced settings`. This will generate
the JSON object for the chosen settings which is sent in the `settings` variable.

The makefile which is generated for a certain set of settings can be viewed by
sending a `makefile` query:

[`[SBURL]makefile?settings={"positional_attributes":{"dependency_attributes":["ref","dephead","deprel"],"lexical_attributes":[],"compound_attributes":[]}}`]([SBURL]makefile?settings={"positional_attributes":{"dependency_attributes":["ref","dephead","deprel"],"lexical_attributes":[],"compound_attributes":[]}})


# Joining a Build
At the top of the XML response you can find a hash number inside the `build`-tag.
This hash can be used to join an earlier build.

The following request is used for joining the build from the first example of this documentation:

[`[SBURL]join?hash=57fce7e430c7ab4dd83d5244b566dade92595db2`]([SBURL]join?hash=57fce7e430c7ab4dd83d5244b566dade92595db2)

The response contains the chosen settings, the original text and of course the
result of the annotation. See [join](#join) for more details.

# Analysing other Languages

The default analysis language is Swedish but Sparv
also supports other languages. The language is specified by supplying
a two-letter language code to the `language` parameter.

This is an example for an analysis of a German sentence:

[`[SBURL]?text=Nun+folgt+ein+deutscher+Beispielsatz.&language=de`]([SBURL]?text=Nun+folgt+ein+deutscher+Beispielsatz.&language=de)

The following table shows the languages that are currently supported and the tools
that are used to analyse them:

Language      |Code      |Analysis Tool
:-------------|:---------|:-------------
Bulgarian     |bg        |TreeTagger
Catalan       |ca        |FreeLing
Dutch         |nl        |TreeTagger
Estonian      |et        |TreeTagger
English       |en        |FreeLing
French        |fr        |FreeLing
Finnish       |fi        |TreeTagger
Galician      |gl        |FreeLing
German        |de        |FreeLing
Italian       |it        |FreeLing
Latin         |la        |TreeTagger
Norwegian     |no        |FreeLing
Polish        |pl        |TreeTagger
Portuguese    |pt        |FreeLing
Romanian      |ro        |TreeTagger
Russian       |ru        |FreeLing
Slovak        |sk        |TreeTagger
Slovenian     |sl        |FreeLing
Spanish       |es        |FreeLing

Different kinds of settings are supported for different languages, depending on which tool
is used for the analysis. Please use the [frontend](https://spraakbanken.gu.se/sparv)
if you want to check which options there are for a certain language.
Alternatively you can check the JSON schema for the language you want to analyse by sending a schema request, e.g.:

[`[SBURL]schema?language=de`]([SBURL]schema?language=de)


# Progress Information

By adding the flag `incremental=true` to your usual query you can
receive more information on how your analysis is being processed.
An example query could look like this:

`[SBURL]?text=Nu+med+inkrementell+information&incremental=true`


The resulting XML will contain the following extra tags:

```.xml
<increment command="" step="0" steps="27"/>
<increment command="sb.segment" step="1" steps="27"/>
<increment command="sb.segment" step="2" steps="27"/>
<increment command="sb.number --position" step="3" steps="27"/>
<increment command="sb.segment" step="4" steps="27"/>
<increment command="sb.annotate --span_as_value" step="5" steps="27"/>
<increment command="sb.annotate --text_spans" step="6" steps="27"/>
<increment command="sb.parent --children" step="7" steps="27"/>
<increment command="sb.parent --parents" step="8" steps="27"/>
<increment command="sb.parent --parents" step="9" steps="27"/>
<increment command="sb.parent --parents" step="10" steps="27"/>
<increment command="sb.number --position" step="11" steps="27"/>
<increment command="sb.hunpos" step="12" steps="27"/>
<increment command="sb.number --relative" step="13" steps="27"/>
<increment command="sb.annotate --select" step="14" steps="27"/>
<increment command="sb.saldo" step="15" steps="27"/>
<increment command="sb.readability --lix" step="16" steps="27"/>
<increment command="sb.readability --ovix" step="17" steps="27"/>
<increment command="sb.readability --nominal_ratio" step="18" steps="27"/>
<increment command="sb.compound" step="19" steps="27"/>
<increment command="sb.wsd" step="20" steps="27"/>
<increment command="sb.malt" step="21" steps="27"/>
<increment command="sb.sentiment" step="22" steps="27"/>
<increment command="sb.annotate --select" step="23" steps="27"/>
<increment command="sb.annotate --select" step="24" steps="27"/>
<increment command="sb.annotate --chain" step="25" steps="27"/>
<increment command="sb.cwb --export" step="26" steps="27"/>
<increment command="" step="27" steps="27"/>
```

Note that this information will only be displayed if your query is run for the first time.
The progress information is not available for older builds.

# Available calls

## api
Shows this API documentation.

* **methods:** `GET`
* **example:** [`[SBURL]api`]([SBURL]api)

## default query
When provided with the text parameter this call handles text input and runs the Sparv analysis.

* **methods:** `GET`, `POST`
* **parameters:**
    * `text`
    * `settings`, default: settings returned from `[SBURL]schema`
    * `language`, default: `sv`
    * `mode`, default: `plain`
    * `incremental`, default: `False`
* **examples:**
    * [`[SBURL]?text=En+exempelmening+till+nättjänsten`]([SBURL]?text=En+exempelmening+till+nättjänsten)
    * `curl -X POST --data-binary text="En exempelmening till nättjänsten" [SBURL]`
* **result:**

```.xml
<result>
  <build hash="57fce7e430c7ab4dd83d5244b566dade92595db2"/>
  <corpus link="https://ws.spraakbanken.gu.se/ws/sparv/v2/download?hash=57fce7e430c7ab4dd83d5244b566dade92595db2">
    <text lix="54.00" ovix="inf" nk="inf">
      <paragraph>
        <sentence id="8f7-84d">
          <w pos="DT" msd="DT.UTR.SIN.IND" lemma="|en|" lex="|en..al.1|" sense="|den..1:-1.000|en..2:-1.000|" complemgram="|" compwf="|" sentiment="0.6799" ref="1" dephead="2" deprel="DT">En</w>
          <w pos="NN" msd="NN.UTR.SIN.IND.NOM" lemma="|exempelmening|" lex="|" sense="|" complemgram="|exempel..nn.1+mening..nn.1:1.309e-08|" compwf="|exempel+mening|" ref="2" deprel="ROOT">exempelmening</w>
          <w pos="PP" msd="PP" lemma="|till|" lex="|till..pp.1|" sense="|till..1:-1.000|" complemgram="|" compwf="|" sentiment="0.5086" ref="3" dephead="2" deprel="ET">till</w>
          <w pos="NN" msd="NN.UTR.SIN.DEF.NOM" lemma="|nättjänst|nättjänsten|" lex="|" sense="|" complemgram="|nät..nn.1+tjänst..nn.2:6.298e-11|nät..nn.1+tjänst..nn.1:6.298e-11|nätt..av.1+tjänst..nn.1:1.140e-12|nätt..av.1+tjänst..nn.2:1.140e-12|nät..nn.1+tjäna..vb.1+sten..nn.2:2.303e-27|nät..nn.1+tjäna..vb.1+sten..nn.1:2.303e-27|nätt..av.1+tjäna..vb.1+sten..nn.1:5.537e-28|nätt..av.1+tjäna..vb.1+sten..nn.2:5.537e-28|" compwf="|nät+tjänsten|nätt+tjänsten|nät+tjän+sten|nätt+tjän+sten|" ref="4" dephead="3" deprel="PA">nättjänsten</w>
        </sentence>
      </paragraph>
    </text>
  </corpus>
</result>
```

## status
Returns the status of existing builds.

* **methods:** `GET`
* **example:** [`[SBURL]status`]([SBURL]status)
* **result:**

```.xml
<status>
  <build hash="d91d063efb5a8439643147c7367e3a4ddad5ec63" status="Done" since="2018-05-11 18:48:32" accessed="2018-05-11 18:29:57" accessed-secs-ago="326021.5"/>
  <build hash="736e99a73b5c9fdc1d284397a8790df17afe3214-f" status="Done" since="2018-05-11 18:49:57" accessed="2018-05-11 15:38:19" accessed-secs-ago="336318.9"/>
  <build hash="57fce7e430c7ab4dd83d5244b566dade92595db2" status="Done" since="2018-05-11 18:48:45" accessed="2018-05-15 11:47:15" accessed-secs-ago="4582.9"/>
</status>
```


## ping
Pings the backend, responds with the status of the catapult.

* **methods:** `GET`
* **example:** [`[SBURL]ping`]([SBURL]ping)
* **result:**

```.xml
<catapult time="0.0063">PONG</catapult>
```

## schema
Returns the json schema generated from the provided parameters.

* **methods:** `GET`
* **parameters:**
    * `language`, default: `sv`
    * `mode`, default: `plain`
* **example:** [`[SBURL]schema?language=sv&mode=plain`]([SBURL]schema?language=sv&mode=plain)
* **result:** json schema for the given language and text mode


## makefile
Returns the Makefile generated from the provided parameters.

* **methods:** `GET`, `POST`
* **parameters:**
    * `language`, default: `sv`
    * `mode`, default: `plain`
    * `settings`
    * `incremental`, default: `False`
* **examples:**             
    * [`[SBURL]makefile?settings={"positional_attributes":{"dependency_attributes":["ref","dephead","deprel"],"lexical_attributes":[],"compound_attributes":[]}}`]([SBURL]makefile?settings={"positional_attributes":{"dependency_attributes":["ref","dephead","deprel"],"lexical_attributes":[],"compound_attributes":[]}})
    * `curl -g -X POST '[SBURL]makefile?settings={"positional_attributes":{"dependency_attributes":["ref","dephead","deprel"],"lexical_attributes":[],"compound_attributes":[]}}'`
* **result:**

```.makefile
include $(SPARV_MAKEFILES)/Makefile.config
corpus = untitled
original_dir = original

vrt_columns_annotations = word ref dephead.ref deprel
vrt_columns             = word ref dephead     deprel

vrt_structs_annotations = sentence.id paragraph.n text text.lix text.ovix text.nk
vrt_structs             = sentence:id paragraph   text text:lix text:ovix text:nk

xml_elements    = text
xml_annotations = text

token_chunk = sentence
token_segmenter = better_word

sentence_chunk = paragraph
sentence_segmenter = punkt_sentence

paragraph_chunk = text
paragraph_segmenter = blanklines

include $(SPARV_MAKEFILES)/Makefile.rules
```

## upload
Handles file uploads and runs the analysis.

* **methods:** `POST`
* **parameters:**
    * `language`, default: `sv`
    * `mode`, default: `plain`
    * `email`
    * `files`
    * `settings`
* **example:** `curl -X POST -F files[]=@/path/to/file/myfile.txt [SBURL]upload?`
* **result:** a download link to a zip file containing the annotation

## download
Handles download of result files.

* **methods:** `GET`
* **parameters:**
    * hash
* **example:** `[SBURL]download?hash=a0c3861b251a595c83859c6cf4c595e8c71ad8da-f`
* **result:** a zip file containing the annotation

## join
Joins an existing build.

* **methods:** `GET`, `POST`
* **parameters:**
    * `language`, default: `sv`
    * `mode`, default: `plain`
    * `hashnumber`
    * `incremental`, default: `False`
* **examples:**
    * [`[SBURL]join?hash=57fce7e430c7ab4dd83d5244b566dade92595db2`]([SBURL]join?hash=57fce7e430c7ab4dd83d5244b566dade92595db2)
    * `curl -X POST '[SBURL]join?hash=57fce7e430c7ab4dd83d5244b566dade92595db2'`
* **result:**

```.xml
<result>
    <settings>{
      "root": {
        "attributes": [],
        "tag": "text"
      },
      "text_attributes": {
        "readability_metrics": [
          "lix",
          "ovix",
          "nk"
        ]
      },
      "word_segmenter": "default_tokenizer",
      "positional_attributes": {
        "lexical_attributes": [
          "pos",
          "msd",
          "lemma",
          "lex",
          "sense"
        ],
        "compound_attributes": [
          "complemgram",
          "compwf"
        ],
        "dependency_attributes": [
          "ref",
          "dephead",
          "deprel"
        ],
        "sentiment": [
          "sentiment"
        ]
      },
      "sentence_segmentation": {
        "sentence_chunk": "paragraph",
        "sentence_segmenter": "default_tokenizer"
      },
      "paragraph_segmentation": {
        "paragraph_segmenter": "blanklines"
      },
      "lang": "sv",
      "textmode": "plain",
      "named_entity_recognition": [],
      "corpus": "untitled"
      }
      </settings>
      <original>&lt;text&gt;En exempelmening till nättjänsten&lt;/text&gt;</original>
      <build hash='57fce7e430c7ab4dd83d5244b566dade92595db2'/>
      <corpus link='https://ws.spraakbanken.gu.se/ws/sparv/v2/download?hash=57fce7e430c7ab4dd83d5244b566dade92595db2'>
        <text lix="54.00" ovix="inf" nk="inf">
          <paragraph>
            <sentence id="8f7-84d">
              <w pos="DT" msd="DT.UTR.SIN.IND" lemma="|en|" lex="|en..al.1|" sense="|den..1:-1.000|en..2:-1.000|" complemgram="|" compwf="|" sentiment="0.6799" ref="1" dephead="2" deprel="DT">En</w>
              <w pos="NN" msd="NN.UTR.SIN.IND.NOM" lemma="|exempelmening|" lex="|" sense="|" complemgram="|exempel..nn.1+mening..nn.1:1.309e-08|" compwf="|exempel+mening|" ref="2" deprel="ROOT">exempelmening</w>
              <w pos="PP" msd="PP" lemma="|till|" lex="|till..pp.1|" sense="|till..1:-1.000|" complemgram="|" compwf="|" sentiment="0.5086" ref="3" dephead="2" deprel="ET">till</w>
              <w pos="NN" msd="NN.UTR.SIN.DEF.NOM" lemma="|nättjänst|nättjänsten|" lex="|" sense="|" complemgram="|nät..nn.1+tjänst..nn.2:6.298e-11|nät..nn.1+tjänst..nn.1:6.298e-11|nätt..av.1+tjänst..nn.1:1.140e-12|nätt..av.1+tjänst..nn.2:1.140e-12|nät..nn.1+tjäna..vb.1+sten..nn.2:2.303e-27|nät..nn.1+tjäna..vb.1+sten..nn.1:2.303e-27|nätt..av.1+tjäna..vb.1+sten..nn.1:5.537e-28|nätt..av.1+tjäna..vb.1+sten..nn.2:5.537e-28|" compwf="|nät+tjänsten|nätt+tjänsten|nät+tjän+sten|nätt+tjän+sten|" ref="4" dephead="3" deprel="PA">nättjänsten</w>
            </sentence>
          </paragraph>
        </text>
      </corpus>
      </result>
```

## cleanup
Removes builds that are finished and haven't been accessed within the
timeout (7 days). Requires `secret_key` parameter in query.

* **methods:** `GET`
* **parameters:**
    * `secret_key`
* **example:** `[SBURL]cleanup?secret_key=supersekretkey`
* **result:**

```.xml
<message>
    <removed hash="1e1c4cdb04d593f1526ae21dd3908cfa7e6ca805"/>
    <removed hash="34dfdc2538023e44e7892ee9ac7f1071c6349544"/>
    <removed hash="2cac2b20734661dca6c388c46153aff79380d6d8"/>
</message>
```

Or if there are no old builds:

```.xml
<message>No hashes to be removed.</message>
```



## cleanup/errors
Removes builds that are finished and haven't been accessed within the timeout (7 days) and
the builds with status Error. Requires `secret_key` parameter in query.

* **methods:** `GET`
* **parameters:**
    * `secret_key`
* **example:** `[SBURL]cleanup/errors?secret_key=supersekretkey`
* **result:**

```.xml
<message>
    <removed hash="1e1c4cdb04d593f1526ae21dd3908cfa7e6ca805"/>
    <removed hash="34dfdc2538023e44e7892ee9ac7f1071c6349544"/>
    <removed hash="2cac2b20734661dca6c388c46153aff79380d6d8"/>
</message>
```

Or if there are no builds with status Error:

```.xml
<message>No hashes to be removed.</message>
```

## cleanup/forceall
Removes all the existing builds. Requires `secret_key` parameter in query.

* **methods:** `GET`
* **parameters:**
    * `secret_key`
* **example:** `[SBURL]cleanup/forceall?secret_key=supersekretkey`
* **result:**

```.xml
<message>
    <removed hash="1e1c4cdb04d593f1526ae21dd3908cfa7e6ca805"/>
    <removed hash="34dfdc2538023e44e7892ee9ac7f1071c6349544"/>
    <removed hash="2cac2b20734661dca6c388c46153aff79380d6d8"/>
</message>
```

Or if there are no builds:

```.xml
<message>No hashes to be removed.</message>
```


# Example settings

Swedish plain text input (default mode):

    settings={
        "corpus": "exempelkorpus",
        "lang": "sv",
        "textmode": "plain",
        "word_segmenter": "default_tokenizer",
        "sentence_segmentation": {
            "sentence_chunk": "paragraph",
            "sentence_segmenter": "default_tokenizer"
        },
        "paragraph_segmentation": {
            "paragraph_segmenter": "blanklines"
        },
        "positional_attributes": {
            "lexical_attributes": [
                "pos",
                "msd",
                "lemma",
                "lex",
                "sense"
            ],
            "compound_attributes": [
                "complemgram",
                "compwf"
            ],
            "dependency_attributes": [
                "ref",
                "dephead",
                "deprel"
            ],
            "sentiment": [
                "sentiment"
            ]
        },
        "named_entity_recognition": [],
        "text_attributes": {
            "readability_metrics": [
                "lix",
                "ovix",
                "nk"
            ]
        }
    }


Swedish with xml input:

    settings={
        "corpus": "exempelkorpus",
        "lang": "sv",
        "textmode": "xml",
        "word_segmenter": "default_tokenizer",
        "sentence_segmentation": {
            "tag": "s",
            "attributes": [
                "number"
            ]
        },
        "paragraph_segmentation": {
            "tag": "p",
            "attributes": [
                "name"
            ]
        },
        "root": {
            "tag": "text",
            "attributes": [
                "title"
            ]
        },
        "extra_tags": [
            {
                "tag": "chapter",
                "attributes": [
                    "name"
                ]
            }
        ],
        "positional_attributes": {
            "lexical_attributes": [
                "pos",
                "msd",
                "lemma",
                "lex",
                "sense"
            ],
            "compound_attributes": [
                "complemgram",
                "compwf"
            ],
            "dependency_attributes": [
                "ref",
                "dephead",
                "deprel"
            ],
            "sentiment": [
                "sentiment"
            ]
        },
        "named_entity_recognition": [],
        "text_attributes": {
            "readability_metrics": [
                "lix",
                "ovix",
                "nk"
            ]
        }
    }


English (analysed with FreeLing):

    settings={
        "corpus": "example",
        "lang": "en",
        "textmode": "xml",
        "root": {
            "tag": "text",
            "attributes": []
        },
        "extra_tags": [],
        "positional_attributes": {
            "lexical_attributes": [
                "pos",
                "msd",
                "lemma"
            ]
        },
        "text_attributes": {
            "readability_metrics": [
                "lix",
                "ovix",
                "nk"
            ]
        }
    }

Finnish (analysed with TreeTagger):

    settings={
        "corpus": "example",
        "lang": "fi",
        "textmode": "xml",
        "word_segmenter": "default_tokenizer",
        "sentence_segmentation": {
            "sentence_chunk": "paragraph",
            "sentence_segmenter": "default_tokenizer"
        },
        "paragraph_segmentation": {
            "paragraph_chunk": "text",
            "paragraph_segmenter": "blanklines"
        },
        "root": {
            "tag": "text",
            "attributes": [
                "title"
            ]
        },
        "extra_tags": [],
        "positional_attributes": {
            "lexical_attributes": [
                "pos",
                "msd",
                "lemma"
            ]
        },
        "text_attributes": {
            "readability_metrics": [
                "lix",
                "ovix",
                "nk"
            ]
        }
    }


Swedish development mode (Sparv labs):

    settings={
        "corpus": "exempelkorpus",
        "lang": "sv-dev",
        "textmode": "plain",
        "word_segmenter": "default_tokenizer",
        "sentence_segmentation": {
            "sentence_chunk": "paragraph",
            "sentence_segmenter": "default_tokenizer"
        },
        "paragraph_segmentation": {
            "paragraph_segmenter": "blanklines"
        },
        "positional_attributes": {
            "lexical_attributes": [
                "pos",
                "msd",
                "lemma",
                "lex",
                "sense"
            ],
            "compound_attributes": [
                "complemgram",
                "compwf"
            ],
            "dependency_attributes": [
                "ref",
                "dephead",
                "deprel"
            ],
            "lexical_classes": [
                "blingbring",
                "swefn"
            ],
            "sentiment": [
                "sentiment"
            ]
        },
        "named_entity_recognition": [
            "ex",
            "type",
            "subtype"
        ],
        "text_attributes": {
            "readability_metrics": [
                "lix",
                "ovix",
                "nk"
            ],
            "lexical_classes": [
                "blingbring",
                "swefn"
            ]
        }
    }
