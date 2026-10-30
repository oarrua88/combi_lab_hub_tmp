# AutoDock Vina (Trott & Olson 2010) - score-only image for CombiLabHUB (CPU)
# Two engines: Vina 1.1.2 + MGLTools 1.5.7 (CASF-2016 protocol, default in the test) and the official
# Vina 1.2.5 binary + Open Babel 3.1.1 (the Windows engine, also included to compare).
# Build (from this folder):   docker build -t combilab/autodock_vina:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Two environments: autodock_vina (Python 3.10 + Open Babel 3.1.1 + Vina 1.1.2 from bioconda) and mgltools (Python 2.7)
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml environment_mgltools.yml /tmp/
RUN micromamba create -y -f /tmp/environment.yml \
 && micromamba install -y -n autodock_vina -c conda-forge -c bioconda autodock-vina=1.1.2 \
 && micromamba create -y -f /tmp/environment_mgltools.yml \
 && micromamba clean --all --yes
ENV ENV_NAME=autodock_vina
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- Official Vina 1.2.5 binary (GitHub release v1.2.5), MD5 checked
ARG VINA125_URL=https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_linux_x86_64
USER root
RUN mkdir -p /opt/vina125 /opt/autodock_vina /data \
 && curl -fsSL -o /opt/vina125/vina "$VINA125_URL" \
 && echo "a1a5d276535db56db71f94f403b8939e  /opt/vina125/vina" | md5sum -c - \
 && chmod +x /opt/vina125/vina \
 && chown -R $MAMBA_USER:$MAMBA_USER /opt/autodock_vina /data
USER $MAMBA_USER
RUN vina --version && /opt/vina125/vina --version
ENV MGLPY=/opt/conda/envs/mgltools/bin/python \
    MGLUTIL=/opt/conda/envs/mgltools/MGLToolsPckgs/AutoDockTools/Utilities24

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_autodock_vina.py test_1a30.py /opt/autodock_vina/

WORKDIR /data
CMD ["python", "/opt/autodock_vina/predict_autodock_vina.py", "-h"]
