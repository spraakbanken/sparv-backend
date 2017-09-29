# svn checkout https://svn.spraakdata.gu.se/repos/sparv/backend/

echo "Creating venv for backend"
cd html/app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements
deactivate
cp activate_this.py venv/bin/activate_this.py

echo "Checking out necessary parts of the pipeline"
cd ../../data
mkdir pipeline
svn checkout --depth empty https://svn.spraakdata.gu.se/sb-arkiv/tools/annotate
svn update --set-depth infinity makefiles
svn update --set-depth infinity python
svn update --set-depth infinity bin
svn update --set-depth infinity models

echo "Building pipeline models"
cd pipeline/models
make all
make space

echo "Checking out catapult"
cd ..
svn checkout https://svn.spraakdata.gu.se/repos/sparv/catapult
cd catapult
make
echo "Creating venv for catapult"
python3 -m venv venv
pip install -r requirements
deactivate


# Run backend with venv/bin/gunicorn -b 0.0.0.0:58444 index
