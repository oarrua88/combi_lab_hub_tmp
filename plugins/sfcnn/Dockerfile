# Sfcnn (Wang et al., 2022) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/sfcnn:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

# --- System tools needed only at build time (git to fetch the code)
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python environment: Python 3.8, TensorFlow 2.3 CPU, Open Babel 3.1.1
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba create -y -f /tmp/environment.yml && micromamba clean --all --yes
ENV ENV_NAME=sfcnn
ENV TF_CPP_MIN_LOG_LEVEL=2
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- Sfcnn source code and trained weights (both in the repository), pinned commit + MD5 check
ARG SFCNN_REPO=https://github.com/bioinfocqupt/Sfcnn.git
ARG SFCNN_COMMIT=30ba8f0f8d54e1860d8e4672beb5fb7920bf7b4d
ARG WEIGHTS_MD5=b1315396dfd1616b4be80fdaeff4a428
USER root
RUN mkdir -p /opt/Sfcnn /opt/sfcnn /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/Sfcnn /opt/sfcnn /data
USER $MAMBA_USER
RUN git clone "$SFCNN_REPO" /opt/Sfcnn \
 && git -C /opt/Sfcnn checkout "$SFCNN_COMMIT" \
 && echo "$WEIGHTS_MD5  /opt/Sfcnn/weights_22_112-0.0083.h5" | md5sum -c -

# --- CombiLabHUB scripts: batch prediction and installation test
COPY --chown=$MAMBA_USER:$MAMBA_USER predict_sfcnn.py test_1a30.py /opt/sfcnn/

WORKDIR /data
CMD ["python", "/opt/sfcnn/predict_sfcnn.py", "-h"]
