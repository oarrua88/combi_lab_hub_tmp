# MMPD-DTA (Wang et al., J. Chem. Inf. Model. 2025) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/mmpd_dta:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.10 + CPU PyTorch 2.3.1 + PyG 2.5.3 + RDKit 2023.09.6 (conda-forge)
RUN micromamba create -y -n mmpd_dta -c conda-forge \
      python=3.10 "pytorch=2.3.1=cpu*" "libtorch=2.3.1=cpu*" "pytorch_geometric=2.5.3" \
      numpy=1.26.4 networkx=3.4.2 rdkit=2023.09.6 \
 && micromamba clean --all --yes
ENV ENV_NAME=mmpd_dta
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- MMPD-DTA code + trained model (both in the repository, pinned commit, MD5 check)
#     and the authors' test2016.pt (from data/processed/data.zip), used by the 1a30 test
ARG MMPD_REPO=https://github.com/zhc-moushang/MMPD-DTA.git
ARG MMPD_COMMIT=69926361c8155fdd40ea2aef7df0aa3fd7de1353
USER root
RUN mkdir -p /opt/MMPD-DTA /opt/mmpd_dta /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/MMPD-DTA /opt/mmpd_dta /data
USER $MAMBA_USER
RUN git clone "$MMPD_REPO" /opt/MMPD-DTA \
 && git -C /opt/MMPD-DTA checkout "$MMPD_COMMIT" \
 && echo "366d95ccc2f7fdf87ae70746cb03ce39  /opt/MMPD-DTA/result/best/best_model.pt" | md5sum -c - \
 && python -c "import zipfile; zipfile.ZipFile('/opt/MMPD-DTA/data/processed/data.zip').extract('test2016.pt', '/opt/MMPD-DTA/data/processed')" \
 && echo "a1e8f977283476ec8b301aa444e493ac  /opt/MMPD-DTA/data/processed/test2016.pt" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_mmpd_dta.py test_1a30.py /opt/mmpd_dta/

WORKDIR /data
CMD ["python", "/opt/mmpd_dta/predict_mmpd_dta.py", "-h"]
