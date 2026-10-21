# IGModel (Wang et al., Brief. Bioinform. 2024) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/igmodel:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.10 + CPU PyTorch 2.3.1 + conda-forge DGL 2.2.1 + RDKit + Open Babel 3.1.1 + spyrmsd
RUN micromamba create -y -n igmodel -c conda-forge \
      python=3.10 "pytorch=2.3.1=cpu*" "libtorch=2.3.1=cpu*" numpy=1.26.4 pandas=2.2.3 scipy=1.15.2 \
      rdkit=2025.09.5 openbabel=3.1.1 spyrmsd=0.9.0 \
      networkx=3.4.2 psutil pydantic pyyaml requests tqdm metis=5.1.1 liburing=2.7 pip \
 && micromamba install -y -n igmodel -c conda-forge --no-deps "dgl=2.2.1=py310h039f8d5_2" \
 && micromamba clean --all --yes
ENV ENV_NAME=igmodel
ENV DGLBACKEND=pytorch
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-cache-dir --no-deps torchdata==0.8.0

# --- IGModel code and trained models (both in the repository), pinned commit + MD5 checks
ARG IG_REPO=https://github.com/zchwang/IGModel.git
ARG IG_COMMIT=2703fc3a1a2cf45357d990a93141ddeda7f38587
USER root
RUN mkdir -p /opt/IGModel /opt/igmodel /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/IGModel /opt/igmodel /data
USER $MAMBA_USER
RUN git clone "$IG_REPO" /opt/IGModel \
 && git -C /opt/IGModel checkout "$IG_COMMIT" \
 && echo "f7f17e91249bed9c90b8a7201c4c2402  /opt/IGModel/models/saved_model.pth" | md5sum -c - \
 && echo "a3931cd4e2d3573a60f7b00e6f645d5e  /opt/IGModel/models/self-ref_model.pth" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_igmodel.py test_1a30.py /opt/igmodel/

WORKDIR /data
CMD ["python", "/opt/igmodel/predict_igmodel.py", "-h"]
