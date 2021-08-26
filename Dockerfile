FROM ubuntu:latest

# install python to the container
RUN apt-get update
RUN apt-get install -y python3 \
    python3-pip

# run server as weak user for security
RUN useradd -m server
WORKDIR /home/server


# install required python packages
COPY server/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# open the server port
EXPOSE 5000
USER server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "25", "app:create_app()"]
