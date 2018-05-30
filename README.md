# sparv-backend

There are several options for running the Sparv backend:

1. in a Docker environment
2. with gunicorn
3. with waitress (mostly for testing purposes)

## Installation

* Create config.py and adapt variables:
    ```
    cp app/config_default.py app/config.py
    ```

* Create python virtual environment for backend (not needed when using Docker)
    ```
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
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

1. With Docker:
    [add commands]

2. With gunicorn (you may want to adapt the settings in `gunicorn_config.py`):

    ```
    PATH_TO_BACKEND=`pwd`
    $PATH_TO_BACKEND/app/venv/bin/gunicorn --chdir $PATH_TO_BACKEND/app -c $PATH_TO_BACKEND/app/gunicorn_config.py app
    ```

3. With waitress (run with python3):
    ```
    PATH_TO_BACKEND=`pwd`
    python $PATH_TO_BACKEND/app.py
    ```

## Setup cronjob for cleaning up old builds

```
MAILTO=""
1 0 * * * curl [URL-TO-SPARV-BACKEND]/cleanup?secret_key=
```
