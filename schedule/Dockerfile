FROM python:3.12-alpine
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY schedule .
COPY env.py .

CMD ["python","-u","schedule.py"]
