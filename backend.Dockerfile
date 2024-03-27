FROM ubuntu:22.04
EXPOSE 80

RUN ln -snf /usr/share/zoneinfo/$CONTAINER_TIMEZONE /etc/localtime && echo $CONTAINER_TIMEZONE > /etc/timezone

RUN apt-get update
RUN apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

ENV HOME="/root"
WORKDIR ${HOME}
RUN apt-get install -y git
RUN git clone --depth=1 https://github.com/pyenv/pyenv.git .pyenv
ENV PYENV_ROOT="${HOME}/.pyenv"
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"

ENV PYTHON_VERSION=3.12.1
RUN pyenv install ${PYTHON_VERSION}
RUN pyenv global ${PYTHON_VERSION}

RUN pip install fastapi uvicorn[standard] requests python-dotenv pymilvus pymongo[srv] gradio sseclient-py websockets
RUN pip install torch --index-url https://download.pytorch.org/whl/cu118
RUN pip install transformers bitsandbytes accelerate optimum 

WORKDIR /app
ENV HF_HOME=./.cache

COPY ./download_model.py ./

RUN python download_model.py

COPY ./src ./src
COPY ./public ./public
COPY ./config ./config
COPY ./.env .
COPY ./main.py .

CMD [ "python", "-m", "uvicorn", "main:app", "--log-config=config/logger.yaml", "--port", "80", "--host", "0.0.0.0" ]  
# CMD ["ls", "./.cache"]