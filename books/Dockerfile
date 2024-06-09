FROM python:3.12.3-slim
WORKDIR ./app
COPY ./requirements.txt ./app
RUN pip install -r requirements.txt
COPY . .
EXPOSE 80
ENV FLASK_APP=books.py
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5001"]