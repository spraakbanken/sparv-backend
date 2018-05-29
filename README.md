# sparv-backend

## Installation

* Create config.py and adapt variables:
    ```
    cp app/config_default.py app/config.py
    ```

* Create python virtual environment for backend:
    ```
    python3 -m venv app/venv
    source app/venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    cp app/activate_this.py app/venv/bin/activate_this.py
    ```

## Installation of additional components

* Clone catapult repo and build catalaunch:
    ```
    git clone https://github.com/spraakbanken/sparv-catapult.git
    make -C sparv-catapult
    ```

* Create venv for catapult:
    ```
    python3 -m venv sparv-catapult/venv
    source sparv-catapult/venv/bin/activate
    pip install --upgrade pip
    pip install -r sparv-catapult/requirements.txt
    deactivate
    ```

* Clone Sparv pipeline repo:
    ```
    mkdir -p "data/pipeline"
    git clone https://github.com/spraakbanken/sparv-pipeline.git data
    ```
* Follow the Sparv pipeline installation instructions.

## Running the Sparv backend

```
PATH_TO_BACKEND=`pwd`
$PATH_TO_BACKEND/app/venv/bin/gunicorn --chdir $PATH_TO_BACKEND/app -c $PATH_TO_BACKEND/app/gunicorn_config.py app
```

## Setup cronjob for cleaning up old builds

```
MAILTO=""
1 0 * * * curl [URL-TO-SPARV-BACKEND]/cleanup?secret_key=
```
