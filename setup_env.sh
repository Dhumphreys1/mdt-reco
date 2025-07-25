uv venv
source .venv/bin/activate
#if you add it to a python header, add it here!
#uv pip install numpy
#uv pip install pandas
#uv pip install pyyaml
#uv pip install matplotlib
uv pip install scipy
uv pip install numba
uv pip install -e. --group dev
