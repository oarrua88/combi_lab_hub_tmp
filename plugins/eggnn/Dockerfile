# egGNN (Jiao et al., IEEE BIBM 2021) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/eggnn:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates libcurl4 \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.10 + CPU PyTorch 2.3.1 + RDKit from conda-forge.
#     dgl 2.2.1 has no Linux wheel on PyPI; the conda-forge build needs PyTorch 2.3.1
#     and lists tensorflow as a dependency it does not use here, so it is installed
#     with --no-deps after its real dependencies.
RUN micromamba create -y -n eggnn -c conda-forge \
      python=3.10 "pytorch=2.3.1=cpu*" "libtorch=2.3.1=cpu*" numpy=1.26.4 pandas=2.2.3 scipy=1.15.2 \
      rdkit=2025.03.6 networkx=3.4.2 psutil pydantic pyyaml requests tqdm metis=5.1.1 liburing=2.7 pip \
 && micromamba install -y -n eggnn -c conda-forge --no-deps "dgl=2.2.1=py310h039f8d5_2" \
 && micromamba clean --all --yes
ENV ENV_NAME=eggnn
ENV DGLBACKEND=pytorch
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-cache-dir --no-deps torchdata==0.8.0 \
 && pip install --no-cache-dir dgllife==0.3.2 hyperopt==0.2.7 scikit-learn==1.5.2

# --- egGNN code and trained checkpoints (both in the repository), pinned commit + MD5 checks
ARG EGGNN_REPO=https://github.com/xfcui/egGNN.git
ARG EGGNN_COMMIT=5c66443e2bd5b4a9e8301db960cd58fb69db10a6
USER root
RUN mkdir -p /opt/egGNN /opt/eggnn /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/egGNN /opt/eggnn /data
USER $MAMBA_USER
RUN git clone "$EGGNN_REPO" /opt/egGNN \
 && git -C /opt/egGNN checkout "$EGGNN_COMMIT" \
 && echo "4f8bd6d4e50adfe7dddf5e9f40146ad8  /opt/egGNN/egGNN/checkpoint/16-8596.sav" | md5sum -c - \
 && echo "e3def659ae76cc2e91123bf731d3a6cf  /opt/egGNN/egGNN/checkpoint/16-8412.sav" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_eggnn.py test_1a30.py /opt/eggnn/

WORKDIR /data
CMD ["python", "/opt/eggnn/predict_eggnn.py", "-h"]
