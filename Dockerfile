FROM tiangolo/uwsgi-nginx-flask:python3.6
COPY ./requirements /app/requirements/
COPY ./requirements.txt /app/
COPY ./supersummariser /app/supersummariser/
COPY ./migrations /app/migrations/
COPY ./autoapp.py /app/main.py
WORKDIR /app
RUN pip install -r requirements.txt
