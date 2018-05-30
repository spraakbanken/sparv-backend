FROM python:3.6
ADD app /app/
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["gunicorn", "--config", "gunicorn_config.py", "index"]
