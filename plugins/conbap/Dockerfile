# ConBAP (Luo et al., J. Chem. Inf. Model. 2024) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/conbap:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.10 + CPU PyTorch 2.3.1 + PyG 2.5.3 + torch_scatter/torch_cluster + RDKit + PyMOL (conda-forge)
RUN micromamba create -y -n conbap -c conda-forge \
      python=3.10 "pytorch=2.3.1=cpu*" "libtorch=2.3.1=cpu*" pytorch_scatter pytorch_cluster "pytorch_geometric=2.5.3" \
      numpy=1.26.4 pandas=2.2.3 scipy=1.15.2 scikit-learn=1.5.2 networkx=3.4.2 "matplotlib=3.10.*" biopython=1.85 \
      rdkit=2025.03.6 pymol-open-source=3.1.0 tqdm requests pip \
 && micromamba clean --all --yes
ENV ENV_NAME=conbap
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- GVP-GNN, pinned commit, without its atom3d dependency (not used by ConBAP)
RUN pip install --no-cache-dir --no-deps "git+https://github.com/drorlab/gvp-pytorch.git@316eea7cd6446dd928e5975634152ec3b28e65f5"

# --- ConBAP code and trained checkpoints (in the repository), pinned commit + MD5 checks
ARG CB_REPO=https://github.com/ld139/ConBAP.git
ARG CB_COMMIT=494817a5207f9bfeba681b1d239898545088789c
USER root
RUN mkdir -p /opt/ConBAP /opt/conbap /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/ConBAP /opt/conbap /data
USER $MAMBA_USER
RUN git clone "$CB_REPO" /opt/ConBAP \
 && git -C /opt/ConBAP checkout "$CB_COMMIT" \
 && echo "0048d622b60c7df895215259659d5f90  /opt/ConBAP/unsupervised/model/20240111_193210_ConBAP_repeat3/model/contrastive_no_filtered.pt" | md5sum -c - \
 && echo "0256bb84bdf87fb2f0671f0acbd33358  /opt/ConBAP/supervised/model/20231007_111336_ConBAP_repeat0/model/epoch-292, train_loss-0.1220, train_rmse-0.3493, valid_rmse-1.1663, valid_pr-0.7788.pt" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_conbap.py test_1a30.py /opt/conbap/

WORKDIR /data
CMD ["python", "/opt/conbap/predict_conbap.py", "-h"]
