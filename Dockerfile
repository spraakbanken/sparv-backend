FROM python:3.6
ADD app /app/
ADD requirements.txt app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
ENV PYTHONPATH "${PYTONPATH}:/app"
CMD ["gunicorn", "--config", "gunicorn_config.py", "app"]
