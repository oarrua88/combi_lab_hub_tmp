# DeepBindGCN_RG (Zhang et al., 2023) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/deepbindgcn:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.10 + CPU PyTorch 2.3.1 + PyG 2.5.3 + RDKit (conda-forge)
RUN micromamba create -y -n deepbindgcn -c conda-forge \
      python=3.10 "pytorch=2.3.1=cpu*" "libtorch=2.3.1=cpu*" "pytorch_geometric=2.5.3" \
      numpy=1.26.4 pandas=2.2.3 networkx=3.4.2 scikit-learn=1.5.2 rdkit=2025.03.6 \
 && micromamba clean --all --yes
ENV ENV_NAME=deepbindgcn
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- DeepBindGCN code (pinned commit) + trained regression model (GitHub release v1.0.0, MD5 check)
ARG DBG_REPO=https://github.com/haiping1010/DeepBindGCN.git
ARG DBG_COMMIT=830a195df5be7edde2d8d6de8ff57d952532dde7
ARG MODEL_URL=https://github.com/haiping1010/DeepBindGCN/releases/download/v1.0.0/full_model_out2000_RG.model
USER root
RUN mkdir -p /opt/DeepBindGCN /opt/deepbindgcn /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/DeepBindGCN /opt/deepbindgcn /data
USER $MAMBA_USER
RUN git clone "$DBG_REPO" /opt/DeepBindGCN \
 && git -C /opt/DeepBindGCN checkout "$DBG_COMMIT" \
 && curl -sSL -o /opt/DeepBindGCN/DeepBindGCN_RG_example/full_model_out2000_RG.model "$MODEL_URL" \
 && echo "aaa694546e7cf41c9d2c3417df197d17  /opt/DeepBindGCN/DeepBindGCN_RG_example/full_model_out2000_RG.model" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_deepbindgcn.py test_1a30.py /opt/deepbindgcn/

WORKDIR /data
CMD ["python", "/opt/deepbindgcn/predict_deepbindgcn.py", "-h"]
