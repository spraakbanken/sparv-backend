#!/bin/bash

# Check out backend from:
# svn checkout https://svn.spraakdata.gu.se/repos/sparv/backend/ .
set -x

echo "Creating venv for backend"
cd "html/app"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cp activate_this.py venv/bin/activate_this.py

echo "Checking out necessary parts of the pipeline"
cd "../../data/"
mkdir pipeline
cd "pipeline"
svn checkout --depth empty https://svn.spraakdata.gu.se/sb-arkiv/tools/annotate .
svn update --set-depth infinity makefiles python bin models

echo "Building pipeline models"
cd "models"
make all
make space

echo "Checking out catapult"
cd "../"
svn checkout https://svn.spraakdata.gu.se/repos/sparv/catapult
cd "catapult"
make
echo "Creating venv for catapult"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate


# Run backend with:
# PATH_TO_BACKEND/html/app/venv/bin/gunicorn --chdir PATH_TO_BACKEND/html/app -c PATH_TO_BACKEND/html/app/gunicorn_config.py index

# Setup cronjob:
# MAILTO=""
# 1 0 * * * curl https://ws.spraakbanken.gu.se/ws/sparv/v2/cleanup?secret_key=
