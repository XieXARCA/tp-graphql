FROM python:3.12-alpine
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY booking .
COPY env.py .

CMD ["python","-u","booking.py"]
