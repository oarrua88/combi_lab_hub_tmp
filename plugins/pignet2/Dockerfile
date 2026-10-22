# PIGNet2 (Moon et al., Digital Discovery 2024) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/pignet2:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.9 + RDKit 2022.03.4 (authors' version) + PyMOL + Open Babel + Dimorphite-DL,
#     CPU PyTorch 2.3.1 with torch_scatter / torch_sparse, all from conda-forge.
RUN micromamba create -y -n pignet2 -c conda-forge \
      python=3.9 numpy=1.22.4 pandas=1.4.3 scipy=1.7.3 scikit-learn=1.1.2 rdkit=2022.03.4 \
      pymol-open-source=2.5.0 openbabel=3.1.1 dimorphite-dl=1.3.2 \
      "pytorch=2.3.1=cpu*" "libtorch=2.3.1=cpu*" pytorch_scatter=2.1.2 pytorch_sparse=0.6.18 pip \
 && micromamba clean --all --yes
ENV ENV_NAME=pignet2
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-cache-dir torch_geometric==2.0.3 hydra-core==1.2.0 omegaconf==2.2.2 biopython==1.79 tqdm

# --- PIGNet2 code and the 4 trained models (in the repository), pinned commit + MD5 checks
ARG REPO=https://github.com/ACE-KAIST/PIGNet2.git
ARG COMMIT=f621aaaa9fe781e67763c8adbffff6faca6db95b
USER root
RUN mkdir -p /opt/PIGNet2 /opt/pignet2 /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/PIGNet2 /opt/pignet2 /data
USER $MAMBA_USER
RUN git clone "$REPO" /opt/PIGNet2 \
 && git -C /opt/PIGNet2 checkout "$COMMIT" \
 && cd /opt/PIGNet2/src/ckpt \
 && echo "5d0f378dc68caee224502348513b6f8f  pda_0.pt" | md5sum -c - \
 && echo "e5392f8dedcb05de4b8d45ad1bdf8592  pda_1.pt" | md5sum -c - \
 && echo "4ff275ddcaf2b02a99197979f846c35d  pda_2.pt" | md5sum -c - \
 && echo "e5ec13dcf8dadf8c5629cb43986cfdd2  pda_3.pt" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_pignet2.py test_1a30.py /opt/pignet2/

WORKDIR /data
CMD ["python", "/opt/pignet2/predict_pignet2.py", "-h"]
