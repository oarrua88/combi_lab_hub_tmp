# saCNN (Wang et al., IEEE BIBM 2021) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/sacnn:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.10 + CPU PyTorch 2.5.1 + RDKit + pdb2pqr/propka + mdtraj from conda-forge,
#     moleculekit 1.11.5 from PyPI. HTMD is not needed.
RUN micromamba create -y -n sacnn -c conda-forge \
      python=3.10 numpy=1.26.4 scipy=1.15.2 pandas=2.2.3 networkx=3.4.2 rdkit=2024.03.5 \
      pdb2pqr=3.6.1 propka=3.5.1 mdtraj=1.10.3 h5py "pytorch=2.5.1=cpu*" pip \
 && micromamba clean --all --yes
ENV ENV_NAME=sacnn
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-cache-dir moleculekit==1.11.5 biopython==1.88 matplotlib==3.10.9 msgpack==1.2.3

# --- saCNN code, trained checkpoint and example features (all in the repository), pinned commit + MD5 checks
ARG SACNN_REPO=https://github.com/xfcui/saCNN.git
ARG SACNN_COMMIT=3e42aa93796d32deab1d266f1f32113ef4254301
USER root
RUN mkdir -p /opt/saCNN /opt/sacnn /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/saCNN /opt/sacnn /data
USER $MAMBA_USER
RUN git clone "$SACNN_REPO" /opt/saCNN \
 && git -C /opt/saCNN checkout "$SACNN_COMMIT" \
 && echo "0418f265c1dc6758a4a76aae0ae7531c  /opt/saCNN/checkpoint/model.pkl" | md5sum -c - \
 && echo "ffcee2ab2523c4fd7fee7b9ebddb8a7b  /opt/saCNN/data/feature/3jvr.h5" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_sacnn.py test_1a30.py /opt/sacnn/

WORKDIR /data
CMD ["python", "/opt/sacnn/predict_sacnn.py", "-h"]
