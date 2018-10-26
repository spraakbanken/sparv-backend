# Sparv Backend

There are several options for running the Sparv backend:

1. in a Docker environment
2. with gunicorn
3. with waitress (mostly for testing purposes)


## Prerequisites

* A Unix-like environment (e.g. Linux, OS X)
* [Python 3.4](http://python.org/) or newer
* [GNU Make](https://www.gnu.org/software/make/)

## Installation
* Clone this project and its submodules:
   ```
   git clone https://github.com/spraakbanken/sparv-backend.git
   cd sparv-backend
   git submodule init
   git submodule update
   ```

* Create config.py and adapt variables:
    ```
    cp app/config_default.py app/config.py
    ```

* Create directory for log files:
   ```
   mkdir logs
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

* Setup catapult submodule and build catalaunch:
    ```
    git submodule init
    git submodule update
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

* Adapt the variables in `sparv-catapult/config.sh` if necessary.

* Clone Sparv pipeline repo:
    ```
    mkdir -p "data/pipeline"
    git clone https://github.com/spraakbanken/sparv-pipeline.git data
    ```
* Follow the Sparv pipeline installation instructions. Use the catapult's venv
  as virtual environment inside the sparv-pipeline!

## Running the Sparv backend

1. With Docker:
    [add commands]

2. With gunicorn (you may want to adapt the settings in `gunicorn_config.py`):

    ```
    PATH_TO_BACKEND=`pwd`
    $PATH_TO_BACKEND/venv/bin/gunicorn --chdir $PATH_TO_BACKEND/app -c $PATH_TO_BACKEND/app/gunicorn_config.py app
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
