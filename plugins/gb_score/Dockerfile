# GB-Score (Rayka et al., 2022) - inference-only image for CombiLabHUB
# Build (from this folder):   docker build -t combilab/gb-score:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

# --- System tools needed only at build time (git to fetch the code, curl for the model)
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python environment: versions listed in the GB-Score README (Python 3.8.8, scikit-learn 0.24.1)
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba create -y -f /tmp/environment.yml && micromamba clean --all --yes
ENV ENV_NAME=gb-score
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- GB-Score source code, pinned to a fixed commit
ARG GB_REPO=https://github.com/miladrayka/GB_Score.git
ARG GB_COMMIT=b543f0b24358640c6ce4505c1679788f9b01d054
USER root
RUN mkdir -p /opt/GB_Score /opt/gb_score /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/GB_Score /opt/gb_score /data
USER $MAMBA_USER
RUN git clone "$GB_REPO" /opt/GB_Score \
 && git -C /opt/GB_Score checkout "$GB_COMMIT"

# --- Trained model (Figshare 10.6084/m9.figshare.16912150, 620 MB), verified by MD5
ARG MODEL_URL=https://ndownloader.figshare.com/files/31280212
ARG MODEL_MD5=90ce46593c302792086ed402ebf93921
RUN curl -fL --retry 3 -o /opt/GB_Score/gb_score.joblib "$MODEL_URL" \
 && echo "$MODEL_MD5  /opt/GB_Score/gb_score.joblib" | md5sum -c -

# --- CombiLabHUB scripts: prediction, CASF helper, installation test and references
COPY --chown=$MAMBA_USER:$MAMBA_USER predict_gb_score.py prepare_casf.py test_1a30.py /opt/gb_score/
COPY --chown=$MAMBA_USER:$MAMBA_USER reference /opt/gb_score/reference

# Outputs are written to the current folder: mount your results folder at /data
WORKDIR /data
CMD ["python", "/opt/gb_score/predict_gb_score.py", "-h"]
