# DeepRLI (Lin et al., Digital Discovery 2025) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/deeprli:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.10 + CPU PyTorch 2.3.1 + RDKit 2023.09 from conda-forge.
#     dgl 2.2.1 has no Linux wheel on PyPI; the conda-forge build needs PyTorch 2.3.1
#     and lists tensorflow as a dependency it does not use, so it is installed with
#     --no-deps after its real dependencies (same recipe as plugins/eggnn).
RUN micromamba create -y -n deeprli -c conda-forge \
      python=3.10 "pytorch=2.3.1=cpu*" "libtorch=2.3.1=cpu*" numpy=1.26.4 pandas=2.2.3 scipy=1.15.2 \
      rdkit=2023.09.6 networkx=3.4.2 psutil pydantic pyyaml requests tqdm metis=5.1.1 liburing=2.7 pip \
 && micromamba install -y -n deeprli -c conda-forge --no-deps "dgl=2.2.1=py310h039f8d5_2" \
 && micromamba clean --all --yes
ENV ENV_NAME=deeprli
ENV DGLBACKEND=pytorch
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-cache-dir --no-deps torchdata==0.8.0

# --- DeepRLI code (pinned commit) and trained model (GitHub release v1.0.2, MD5 check)
ARG DEEPRLI_REPO=https://github.com/fairydance/DeepRLI.git
ARG DEEPRLI_COMMIT=9d6e73993edded01de57b765da42fe58463c670a
ARG MODEL_URL=https://github.com/fairydance/DeepRLI/releases/download/v1.0.2/trained_model.state_dict.pth
USER root
RUN mkdir -p /opt/DeepRLI /opt/deeprli /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/DeepRLI /opt/deeprli /data
USER $MAMBA_USER
RUN git clone "$DEEPRLI_REPO" /opt/DeepRLI \
 && git -C /opt/DeepRLI checkout "$DEEPRLI_COMMIT" \
 && curl -fsSL -o /opt/DeepRLI/trained_model.state_dict.pth "$MODEL_URL" \
 && echo "334ada642693c0f68a8b0305e77f0a29  /opt/DeepRLI/trained_model.state_dict.pth" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_deeprli.py test_1a30.py /opt/deeprli/

WORKDIR /data
CMD ["python", "/opt/deeprli/predict_deeprli.py", "-h"]
