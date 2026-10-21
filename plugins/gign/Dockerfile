# GIGN (Yang et al., J. Phys. Chem. Lett. 2023) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/gign:1.0 .
# See INSTALL.md, section B, for how to run it.
# The image holds the environment shared by GIGN and EHIGN-PLA.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.10 + CPU PyTorch 2.3.1 + RDKit + PyMOL + Open Babel from conda-forge.
#     dgl 2.2.1 has no Linux wheel on PyPI; the conda-forge build needs PyTorch 2.3.1
#     and lists tensorflow as a dependency it does not use here, so it is installed
#     with --no-deps after its real dependencies.
RUN micromamba create -y -n gign -c conda-forge \
      python=3.10 "pytorch=2.3.1=cpu*" "libtorch=2.3.1=cpu*" numpy=1.26.4 pandas=2.2.3 scipy=1.15.2 \
      scikit-learn=1.5.2 networkx=3.4.2 rdkit=2025.03.6 pymol-open-source=3.1.0 openbabel=3.1.1 \
      psutil pydantic pyyaml requests tqdm metis=5.1.1 liburing=2.7 pip \
 && micromamba install -y -n gign -c conda-forge --no-deps "dgl=2.2.1=py310h039f8d5_2" \
 && micromamba clean --all --yes
ENV ENV_NAME=gign
ENV DGLBACKEND=pytorch
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-cache-dir --no-deps torchdata==0.8.0 \
 && pip install --no-cache-dir torch_geometric==2.5.3

# --- GIGN (Yang et al., J. Phys. Chem. Lett. 2023) code and trained checkpoints (in the repository), pinned commit + MD5 checks
ARG REPO=https://github.com/guaguabujianle/GIGN.git
ARG COMMIT=ef514d326202d71b0674ae20e95456454bf10c6e
USER root
RUN mkdir -p /opt/GIGN /opt/gign /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/GIGN /opt/gign /data
USER $MAMBA_USER
RUN git clone "$REPO" /opt/GIGN \
 && git -C /opt/GIGN checkout "$COMMIT" \
 && cd /opt/GIGN/GIGN/model \
 && echo "b50f62d129b36c7ae2b4c22f214f2e57  20221121_074758_GIGN_repeat0/model/epoch-532, train_loss-0.1162, train_rmse-0.3408, valid_rmse-1.1564, valid_pr-0.7813.pt" | md5sum -c - \
 && echo "2789d71b97862ea1663b630de6fec6e5  20221121_085711_GIGN_repeat1/model/epoch-418, train_loss-0.1271, train_rmse-0.3566, valid_rmse-1.1479, valid_pr-0.7858.pt" | md5sum -c - \
 && echo "66fb93ebe5a51d33715e6e4e458e939c  20221121_095752_GIGN_repeat2/model/epoch-190, train_loss-0.2342, train_rmse-0.4840, valid_rmse-1.1620, valid_pr-0.7813.pt" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_gign.py test_1a30.py /opt/gign/

WORKDIR /data
CMD ["python", "/opt/gign/predict_gign.py", "-h"]
