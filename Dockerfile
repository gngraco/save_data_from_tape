FROM python:3.8-alpine

# Creating folder
RUN mkdir /opt/save_data_from_tape
COPY . /opt/save_data_from_tape
WORKDIR /opt/save_data_from_tape

# Installing dependencies
RUN apk update
RUN apk add --no-cache tzdata py3-pip python3-dev git

# Set the timezone
ENV TZ=America/Fortaleza
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# To install requirements.txt
RUN pip install --no-cache-dir wheel

# Installing Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Cleaning cache
RUN apk del git && rm -rf /var/cache/apk/*

RUN adduser -S -G tape tape
USER tape

# Setting entrypoint
CMD ["-u", "/opt/save_data_from_tape/main.py"]
ENTRYPOINT [ "python3" ]
