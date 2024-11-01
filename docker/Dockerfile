FROM python:3.10-slim
WORKDIR /MessageSyncer
RUN apt-get update && apt-get install -y git 

COPY . /MessageSyncer
EXPOSE 11589
WORKDIR /MessageSyncer/src
RUN pip install -r requirements.txt
CMD [ "python", "MessageSyncer.py" ]