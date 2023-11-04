FROM python:3.12-bookworm
COPY . /app
RUN cd /app && python3 setup.py build install
ENTRYPOINT /bin/env crodump
