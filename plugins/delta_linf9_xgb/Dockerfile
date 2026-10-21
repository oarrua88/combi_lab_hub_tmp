# delta_LinF9_XGB (Yang & Zhang, J. Chem. Inf. Model. 2022) - inference-only image for CombiLabHUB (CPU)
# Contains smina (in the repository), MSMS, MGLTools and AlphaSpace2, so it runs on Windows through Docker.
# Build (from this folder):   docker build -t combilab/delta_linf9_xgb:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Two environments: dlinf9 (Python 3.8) and mgltools (Python 2.7)
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml environment_mgltools.yml /tmp/
RUN micromamba create -y -f /tmp/environment.yml \
 && micromamba create -y -f /tmp/environment_mgltools.yml \
 && micromamba clean --all --yes
ENV ENV_NAME=dlinf9
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- delta_LinF9_XGB code, smina binaries and trained models (in the repository), pinned commit + MD5 checks
ARG DL_REPO=https://github.com/cyangNYU/delta_LinF9_XGB.git
ARG DL_COMMIT=54ae79584f7e22f5af3e28625b9f387f0b74cc0f
USER root
RUN mkdir -p /opt/delta_LinF9_XGB /opt/delta_linf9_xgb /data \
 && chown -R $MAMBA_USER:$MAMBA_USER /opt/delta_LinF9_XGB /opt/delta_linf9_xgb /data
USER $MAMBA_USER
RUN git clone "$DL_REPO" /opt/delta_LinF9_XGB \
 && git -C /opt/delta_LinF9_XGB checkout "$DL_COMMIT" \
 && cd /opt/delta_LinF9_XGB \
 && echo "2d0cf016d2176bd771e2982c519b9f60  software/smina.static" | md5sum -c - \
 && echo "4d33f4c3ff9c044eda689fc959aee765  software/smina_feature" | md5sum -c - \
 && echo "6bde159de18b9f601437f42683bdf468  saved_model/mod_1.pickle.dat" | md5sum -c - \
 && echo "bff2365e0bc46018a0b552b9d04474cc  saved_model/mod_10.pickle.dat" | md5sum -c - \
 && chmod +x software/smina.static software/smina_feature \
 && pip install --no-cache-dir --no-deps software/AlphaSpace2_2021.tar.gz
ENV ADT=/opt/conda/envs/mgltools/bin/prepare_receptor4.py

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_delta_linf9_xgb.py pdb_to_xyzr.py test_1a30.py /opt/delta_linf9_xgb/

WORKDIR /data
CMD ["python", "/opt/delta_linf9_xgb/predict_delta_linf9_xgb.py", "-h"]
