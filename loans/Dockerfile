FROM python:3.12.3-slim

WORKDIR /app

COPY . /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5002

ENV FLASK_APP=loans.py

CMD ["python", "loans.py"]