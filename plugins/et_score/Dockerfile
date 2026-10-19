# ET-Score (Rayka et al., 2021) - inference-only image for CombiLabHUB
# Build (from this folder):   docker build -t combilab/et-score:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

# --- System tools needed only at build time (git to fetch the code, curl for the model)
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python environment: exact versions published by the ET-Score authors (Files.7z/environment.yml)
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba create -y -f /tmp/environment.yml && micromamba clean --all --yes
ENV ENV_NAME=et-score
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- ET-Score source code, pinned to a fixed commit
ARG ET_REPO=https://github.com/miladrayka/ET_Score.git
ARG ET_COMMIT=593b018f621a42b98b7dffd37931cb1c25257de7
USER root
RUN mkdir -p /opt/ET_Score /opt/et_score_test /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/ET_Score /opt/et_score_test /data
USER $MAMBA_USER
RUN git clone "$ET_REPO" /opt/ET_Score \
 && git -C /opt/ET_Score checkout "$ET_COMMIT"

# Upstream uses Windows-only paths (folder + "\\" + "*.mol2"); make them portable
COPY --chown=$MAMBA_USER:$MAMBA_USER patch_glob.py /opt/et_score_test/patch_glob.py
RUN python /opt/et_score_test/patch_glob.py /opt/ET_Score/generate_feature.py

# --- Trained model (Figshare 10.6084/m9.figshare.23684538, CC BY 4.0), verified by MD5
ARG MODEL_URL=https://ndownloader.figshare.com/files/41562135
ARG MODEL_MD5=c7c5865d085fee31ed6e978c9b66c39e
RUN curl -fL --retry 3 -o /opt/ET_Score/et_score.sav "$MODEL_URL" \
 && echo "$MODEL_MD5  /opt/ET_Score/et_score.sav" | md5sum -c -

# --- Installation test (CASF-2016 complex 1a30)
COPY --chown=$MAMBA_USER:$MAMBA_USER test_1a30.py /opt/et_score_test/test_1a30.py
COPY --chown=$MAMBA_USER:$MAMBA_USER reference /opt/et_score_test/reference

# Outputs (features.xlsx, prediction.xlsx) are written to the current folder: mount your results folder at /data
WORKDIR /data
CMD ["python", "/opt/ET_Score/predict.py", "-h"]
