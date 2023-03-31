FROM python:3.11-alpine

WORKDIR /backend-flask

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV FLASK_DEBUG=1
ENV FRONTEND_URL="*" BACKEND_URL="*"

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567"]
