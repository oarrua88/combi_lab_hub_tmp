# EHIGN-PLA (Yang et al., 2024) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/ehign_pla:1.0 .
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

# --- EHIGN-PLA (Yang et al., 2024) code and trained checkpoints (in the repository), pinned commit + MD5 checks
ARG REPO=https://github.com/guaguabujianle/EHIGN_PLA.git
ARG COMMIT=dfd88256318c1a35c7c7adb5534f0c706d9a16f3
USER root
RUN mkdir -p /opt/EHIGN_PLA /opt/ehign_pla /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/EHIGN_PLA /opt/ehign_pla /data
USER $MAMBA_USER
RUN git clone "$REPO" /opt/EHIGN_PLA \
 && git -C /opt/EHIGN_PLA checkout "$COMMIT" \
 && cd /opt/EHIGN_PLA/model \
 && echo "4b0beacc9c4f052e87b9b8d2425c17b0  20230120_135757_EHIGN_repeat0/model/epoch-144, train_loss-0.5772, train_rmse-0.7598, valid_rmse-1.1799, valid_pr-0.7718.pt" | md5sum -c - \
 && echo "efacfb7ad8345205e659f0437c3d48e5  20230120_143536_EHIGN_repeat1/model/epoch-213, train_loss-0.3377, train_rmse-0.5811, valid_rmse-1.1502, valid_pr-0.7866.pt" | md5sum -c - \
 && echo "c4829175b75b69024ff4c3a2f3fe769f  20230120_152442_EHIGN_repeat2/model/epoch-299, train_loss-0.2268, train_rmse-0.4763, valid_rmse-1.1450, valid_pr-0.7868.pt" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_ehign_pla.py test_1a30.py /opt/ehign_pla/

WORKDIR /data
CMD ["python", "/opt/ehign_pla/predict_ehign_pla.py", "-h"]
