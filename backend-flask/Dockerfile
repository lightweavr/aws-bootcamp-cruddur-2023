FROM 017145807427.dkr.ecr.us-west-2.amazonaws.com/ecr-public/docker/library/python:3.11-alpine

WORKDIR /backend-flask

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV FRONTEND_URL="*" BACKEND_URL="*"

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567", "--debug"]
