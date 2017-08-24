<style>
    body {
      margin-top: 2em;
      margin-left: 2em;
      font-family: Consolas, monaco, monospace;
      }
    p {
      color: RoyalBlue;
      font-family: Verdana, Helvetica, sans-serif;
      }
    h1, h2, h3 {
      font-family: Verdana, Helvetica, sans-serif;
    }
    body > ul > li {
        margin-bottom: 2em;
        color: RoyalBlue;
        list-style-type: disc;
    }
    body > ul > li > ul {
        color: black;
    }
    ul {
        list-style-type: circle;
    }
</style>


# Sparv API

Read Sparv's API documentation:
<https://spraakbanken.gu.se/eng/research/infrastructure/sparv/webservice>


## Available queries

* /api
    * description: Shows this short API description.
    * methods: GET

* /
    * description: Handles text input and runs the analysis.
    * methods: GET, POST
    * params:
        * language, default: sv
        * mode, default: plain
        * text, default: ''
        * settings
        * incremental, default: False

* /status
    * description: Returns the status of existing builds.
    * methods: GET

* /ping
    * description: Pings the backend, responds with the status of the catapult.
    * methods: GET

* /schema
    * description: Returns the json schema generated from the parameters provided.
    * methods: GET
    * params:
        * language, default: sv
        * mode, default: plain

* /makefile
    * description: Returns the Makefile generated from the parameters provided.
    * methods: GET, POST
    * params:
        * language, default: sv
        * mode, default: plain
        * settings
        * incremental, default: False

* /upload
    * description: Handles upload of files and runs the analysis.
    * methods: GET, POST
    * params:
        * language, default: sv
        * mode, default: plain
        * email, default: ''
        * files
        * settings

* /download
    * description:
    * methods: GET
    * params:
        * hash, default: ''

* /join
    * description: Joins an existing build.
    * methods: GET, POST
    * params:
        * language, default: sv
        * mode, default: plain
        * hashnumber, default: ''
        * incremental, default: False

* /cleanup
    * description: Removes builds that are finished and haven't been accessed within the timeout (7 days).
      Requires secret_key parameter in query.
    * methods: GET
    * params:
        * secret_key, default: ''

* /cleanup/errors
    * description: Removes builds that are finished and haven't been accessed within the timeout (7 days) and
    the builds with status Error. Requires secret_key parameter in query.
    * methods: GET
    * params:
        * secret_key, default: ''

* /cleanup/forceall
    * description: Removes all the existing builds. Requires secret_key parameter in query.
    * methods: GET
    * params:
        * secret_key, default: ''


## Example settings

Swedish plain text input (default mode):
```
settings={
    "corpus":"untitled",
    "lang":"sv",
    "textmode":"plain",
    "word_segmenter":"default_tokenizer",
    "sentence_segmentation":{
        "sentence_segmenter":"default_tokenizer",
        "sentence_chunk":"paragraph"
        },
    "paragraph_segmentation":{
        "paragraph_segmenter":"blanklines",
        "paragraph_chunk":"root"
        },
    "root":{
        "tag":"text",
        "attributes":[]
        },
    "extra_tags":[],
    "positional_attributes":{
        "dependency_attributes":["ref","dephead","deprel"],
        "lexical_attributes":["pos","msd","lemma","lex","saldo"],
        "compound_attributes":["prefix","suffix"]
        }
    }
```

Swedish with xml input:
```
settings={
    "corpus":"exempelkorpus",
    "lang":"sv",
    "textmode":"xml",
    "word_segmenter":"default_tokenizer",
    "sentence_segmentation":{
        "tag":"s",
        "attributes":["number"]
        },
    "paragraph_segmentation":{
        "tag":"p",
        "attributes":["name"]
        },
    "root":{
        "tag":"text",
        "attributes":["title"]
        },
    "extra_tags":[
        {
            "tag":"chapter",
            "attributes":["name"]
            }
        ],
    "positional_attributes":{
        "lexical_attributes":["pos","msd","lemma","lex","saldo"],
        "compound_attributes":["prefix","suffix"],
        "dependency_attributes":["ref","dephead","deprel"]
        }
    }
```

English:
```
settings={
    "corpus":"untitled",
    "lang":"en",
    "textmode":"plain",
    "positional_attributes":{
        "lexical_attributes":["pos","msd","lemma"]
        },
    "text_attributes":{
        "readibility_metrics":["lix","ovix","nk"]
        }
    }
```

Swedish development mode (Sparv labs):
```
settings={
    "corpus":"untitled",
    "lang":"sv-dev",
    "textmode":"plain",
    "word_segmenter":"default_tokenizer",
    "sentence_segmentation":{
        "sentence_segmenter":"default_tokenizer",
        "sentence_chunk":"paragraph"
        },
    "paragraph_segmentation":{
        "paragraph_segmenter":"blanklines",
        "paragraph_chunk":"root"
        },
    "root":{
        "tag":"text",
        "attributes":[]
        },
    "extra_tags":[],
    "positional_attributes":{
        "dependency_attributes":["ref","dephead","deprel"],
        "lexical_attributes":["pos","msd","lemma","lex","sense"],
        "compound_attributes":["complemgram","compwf"]
        },
    "named_entity_recognition":["ex","type","subtype"],
    "text_attributes":{
        "readibility_metrics":["lix","ovix","nk"]
        }
    }
```
