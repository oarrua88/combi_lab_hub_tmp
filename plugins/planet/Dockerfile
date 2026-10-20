# PLANET (ComputArtCMCG, 2023) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/planet:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.11; CPU-only PyTorch first (avoids the CUDA wheels), then the rest of environment.yml
RUN micromamba create -y -n planet -c conda-forge python=3.11 pip && micromamba clean --all --yes
ENV ENV_NAME=planet
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-cache-dir torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir numpy==1.26.4 scipy==1.11.4 pandas==2.1.4 scikit-learn==1.3.2 rdkit==2023.9.5 matplotlib==3.8.2 tqdm==4.66.1

# --- PLANET code, trained parameters and prepared CASF-2016 core set (all in the repository), pinned commit + MD5 checks
ARG PLANET_REPO=https://github.com/ComputArtCMCG/PLANET.git
ARG PLANET_COMMIT=2e49ae820ae9eb7427d12af1f4cbd03abeb92cdb
USER root
RUN mkdir -p /opt/PLANET /opt/planet /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/PLANET /opt/planet /data
USER $MAMBA_USER
RUN git clone "$PLANET_REPO" /opt/PLANET \
 && git -C /opt/PLANET checkout "$PLANET_COMMIT" \
 && echo "e9c74b412e99367865a1eeb9fbd95feb  /opt/PLANET/PLANET.param" | md5sum -c - \
 && echo "11259e3e37635600dbcab4d50308e7d4  /opt/PLANET/core.tar.bz2" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_planet.py test_1a30.py /opt/planet/

WORKDIR /data
CMD ["python", "/opt/planet/predict_planet.py", "-h"]
