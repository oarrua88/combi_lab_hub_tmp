# OnionNet-2 (Wang et al., 2021) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/onionnet2:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

# --- System tools needed only at build time (git to fetch the code, curl for the model)
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python environment: versions from the OnionNet-2 README (TensorFlow 2.3, scikit-learn 0.22.1) + Open Babel
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba create -y -f /tmp/environment.yml && micromamba clean --all --yes
ENV ENV_NAME=onionnet2
ENV TF_CPP_MIN_LOG_LEVEL=2
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- OnionNet-2 source code, pinned to a fixed commit
ARG ON_REPO=https://github.com/zchwang/OnionNet-2.git
ARG ON_COMMIT=79e84dd2683d9cb307d3775fa6b4f2e4531486ce
USER root
RUN mkdir -p /opt/OnionNet-2 /opt/onionnet2 /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/OnionNet-2 /opt/onionnet2 /data
USER $MAMBA_USER
RUN GIT_LFS_SKIP_SMUDGE=1 git clone "$ON_REPO" /opt/OnionNet-2 \
 && git -C /opt/OnionNet-2 checkout "$ON_COMMIT"

# --- Trained model (Zenodo record 10728089, 885 MB), verified by MD5
ARG MODEL_URL=https://zenodo.org/records/10728089/files/62shell_saved-model.h5?download=1
ARG MODEL_MD5=52eb7563a867b5ee22f505070922cc6c
RUN curl -fL --retry 3 -o /opt/OnionNet-2/models/62shell_saved-model.h5 "$MODEL_URL" \
 && echo "$MODEL_MD5  /opt/OnionNet-2/models/62shell_saved-model.h5" | md5sum -c -

# --- CombiLabHUB scripts: batch prediction, installation test and references
COPY --chown=$MAMBA_USER:$MAMBA_USER predict_onionnet2.py test_1a30.py /opt/onionnet2/
COPY --chown=$MAMBA_USER:$MAMBA_USER reference /opt/onionnet2/reference

WORKDIR /data
CMD ["python", "/opt/onionnet2/predict_onionnet2.py", "-h"]
