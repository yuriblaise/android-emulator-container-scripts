exec  >> /proc/1/fd/1
#Set the version of python
echo "Starting PyEnv + Culebra install script"
# ~/.pyenv/versions/3.7.3/bin/python3.7
PYTHON_VERSION=3.7.3
echo "Python Version ${PYTHON_VERSION}"
#Set of all dependencies needed for pyenv to work on Ubuntu
apt-get update && apt-get install -y --no-install-recommends make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget ca-certificates curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev mecab-ipadic-utf8 git
# Set-up necessary Env vars for PyEnv /root/.pyenv/bin/pyenv
PYENV_ROOT=/root/.pyenv
PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH


curl https://pyenv.run | bash
pyenv update && mkdir -p avc-workdir && cd avc-workdir
echo yes | pyenv install -v $PYTHON_VERSION
pyenv global $PYTHON_VERSION
pyenv rehash

# ~/.pyenv/versions/3.7.3/bin/pip
pip install --upgrade pip && pip install --upgrade pillow &&pip3 install --pre androidviewclient --upgrade