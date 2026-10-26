# T-ALPHA (Kyro et al., J. Chem. Inf. Model. 2025) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/t_alpha:1.0 .
# Downloads about 2.3 GB from Zenodo during the build and keeps only the CASF-2016 model and
# feature file (about 440 MB). See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.11 + CPU PyTorch 2.5.1 + PyG 2.6.1 + torch_cluster (conda-forge); g++/cmake for pykeops,
#     which compiles its kernels the first time they run. The rest as in the authors' requirements.txt.
RUN micromamba create -y -n talpha -c conda-forge \
      python=3.11 "pytorch=2.5.1=cpu*" "libtorch=2.5.1=cpu*" pytorch_cluster "pytorch_geometric=2.6.1" \
      numpy=2.2.0 pandas=2.2.3 scipy=1.14.1 scikit-learn=1.6.0 h5py=3.12.1 "matplotlib=3.10.0" \
      gxx_linux-64 cmake make pip \
 && micromamba clean --all --yes
ENV ENV_NAME=talpha
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-cache-dir pytorch-lightning==2.4.0 lightning-utilities==0.11.9 torchmetrics==1.6.0 \
      pykeops==2.2.3 keopscore==2.2.3

# --- T-ALPHA code (pinned commit), trained model and CASF-2016 features (Zenodo 14510963), MD5 checks
ARG TALPHA_REPO=https://github.com/gregory-kyro/T-ALPHA.git
ARG TALPHA_COMMIT=f9973d1966b61986178ab4370c73e46b4401d140
ARG ZENODO=https://zenodo.org/records/14510963/files
USER root
RUN mkdir -p /opt/T-ALPHA /opt/talpha_data /opt/t_alpha /data \
 && chown -R $MAMBA_USER:$MAMBA_USER /opt/T-ALPHA /opt/talpha_data /opt/t_alpha /data
USER $MAMBA_USER
RUN git clone "$TALPHA_REPO" /opt/T-ALPHA \
 && git -C /opt/T-ALPHA checkout "$TALPHA_COMMIT" \
 && rm -rf /opt/T-ALPHA/.git
RUN cd /opt/talpha_data \
 && curl -fsSL -o mp.tar.gz "$ZENODO/model_parameters.tar.gz?download=1" \
 && echo "16f1b83b90b9c2b84a0960bbbf3365da  mp.tar.gz" | md5sum -c - \
 && tar -xzf mp.tar.gz model_parameters/CASF.ckpt && rm mp.tar.gz \
 && curl -fsSL -o tf.tar.gz "$ZENODO/test_files.tar.gz?download=1" \
 && echo "68cc4568df39f72f5e3beb3562131a41  tf.tar.gz" | md5sum -c - \
 && tar -xzf tf.tar.gz test_files/CASF_crystal.h5 && rm tf.tar.gz \
 && echo "704f963c2fe2f8363e4cc06fd4a2f304  model_parameters/CASF.ckpt" | md5sum -c - \
 && echo "b853bbf8dd86edfd8c8f01e95bdf08aa  test_files/CASF_crystal.h5" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_t_alpha.py test_1a30.py /opt/t_alpha/

# Run the test once at build time: it checks the image and leaves the pykeops kernels compiled
# (otherwise every new container would compile them again).
RUN python -W ignore /opt/t_alpha/test_1a30.py --talpha-dir /opt/T-ALPHA --data-dir /opt/talpha_data

WORKDIR /data
CMD ["python", "/opt/t_alpha/predict_t_alpha.py", "-h"]
