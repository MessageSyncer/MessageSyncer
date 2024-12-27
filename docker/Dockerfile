FROM python:3.11.9-slim
WORKDIR /MessageSyncer
RUN apt-get update && apt-get install -y git 

COPY . /MessageSyncer
RUN bash ./tool/setup.sh --no-dev
EXPOSE 11589
CMD [ "python", "MessageSyncer.py" ]