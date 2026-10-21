# HAC-Net (Kyro, Brent & Batista, J. Chem. Inf. Model. 2023) - inference-only image for CombiLabHUB (CPU)
# Includes ChargeFW2 (the program behind the ACC2 web service), so pocket charges are
# computed offline:  python /opt/hacnet/test_1a30.py ... --charges chargefw2
# Build (from this folder):   docker build -t combilab/hacnet:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.10 + CPU PyTorch 2.3.1 + PyG 2.5.3 + Open Babel 3.1.1 + PyMOL (conda-forge)
RUN micromamba create -y -n hacnet -c conda-forge \
      python=3.10 "pytorch=2.3.1=cpu*" "libtorch=2.3.1=cpu*" "pytorch_geometric=2.5.3" \
      numpy=1.26.4 pandas=2.2.3 scipy=1.15.2 scikit-learn=1.5.2 "matplotlib=3.10.*" h5py ipython tqdm requests \
      biopandas=0.5.1 openbabel=3.1.1 pymol-open-source pip \
 && micromamba clean --all --yes
ENV ENV_NAME=hacnet
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-cache-dir --no-deps HACNet==1.4.3

# --- ChargeFW2 3.0.0 (EqEq charges, same program as ACC2), built from a pinned commit
ARG CFW2_REPO=https://github.com/sb-ncbr/ChargeFW2.git
ARG CFW2_COMMIT=579bf42e4328ad22d998318e78f85d7ea0425ba4
USER root
RUN mkdir -p /opt/HAC-Net /opt/hacnet /opt/chargefw2 /data /tmp/cfw2 \
 && chown -R $MAMBA_USER:$MAMBA_USER /opt/HAC-Net /opt/hacnet /opt/chargefw2 /data /tmp/cfw2
USER $MAMBA_USER
RUN micromamba create -y -n cfw2 -c conda-forge cmake make cxx-compiler libboost-devel "eigen=3.4" "nanoflann=1.6.1" \
      nlohmann_json "gemmi>=0.7.1,<0.8" \
 && git clone "$CFW2_REPO" /tmp/cfw2/src && git -C /tmp/cfw2/src checkout "$CFW2_COMMIT" \
 && cd /tmp/cfw2 && mkdir build && cd build \
 && micromamba run -n cfw2 cmake ../src -DCMAKE_PREFIX_PATH=/opt/conda/envs/cfw2 -DCMAKE_INSTALL_PREFIX=/opt/chargefw2 \
      -DPYTHON_MODULE=OFF -DCMAKE_BUILD_TYPE=Release \
 && micromamba run -n cfw2 make -j2 && micromamba run -n cfw2 make install \
 && rm -rf /tmp/cfw2 && micromamba clean --all --yes \
 && /opt/chargefw2/bin/chargefw2 --help | head -1
ENV CHARGEFW2=/opt/chargefw2/bin/chargefw2

# --- HAC-Net repository (trained parameters + element_features.xml), pinned commit + MD5 checks
ARG HAC_REPO=https://github.com/gregory-kyro/HAC-Net.git
ARG HAC_COMMIT=def30e100ea9eeca3fafb0658823446b97e07ec2
RUN git clone "$HAC_REPO" /opt/HAC-Net \
 && git -C /opt/HAC-Net checkout "$HAC_COMMIT" \
 && cd /opt/HAC-Net/HACNet/parameter_files \
 && echo "7a16badb6abcdbf9075aea5f69b5acdf  CNN_parameters.pt" | md5sum -c - \
 && echo "dd12042a2b43aef2ba047e04116a9b07  GCN0_parameters.pt" | md5sum -c - \
 && echo "04f8f791e2c14e667ca09ba292cca390  GCN1_parameters.pt" | md5sum -c - \
 && echo "91df31324dd88524d5278d017f57e2dd  MLP_parameters.pt" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_hacnet.py test_1a30.py /opt/hacnet/

WORKDIR /data
CMD ["python", "/opt/hacnet/predict_hacnet.py", "-h"]
