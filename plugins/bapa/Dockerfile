# BAPA (Seo et al., BMC Bioinformatics 2021) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/bapa:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates g++ make \
 && rm -rf /var/lib/apt/lists/*

# --- rf-extract (RF-Score v3 features, used for the Vina terms). The original repository
#     (HongjianLi/RF-Score) is no longer on GitHub; this fork gives the same values.
ARG RF_REPO=https://github.com/lachrymator/RF-Score.git
ARG RF_COMMIT=8d05430bccdbd29f1f8247cb7e8939ee6967b6a5
RUN git clone "$RF_REPO" /opt/RF-Score \
 && git -C /opt/RF-Score checkout "$RF_COMMIT" \
 && cd /opt/RF-Score && make bin/rf-extract \
 && cp bin/rf-extract /usr/local/bin/ \
 && rm -rf /opt/RF-Score/.git /opt/RF-Score/obj
USER $MAMBA_USER

# --- Python 3.6 + Open Babel 2.4.1 + TensorFlow 1.12 (CPU), as the authors
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba create -y -f /tmp/environment.yml \
 && micromamba clean --all --yes
ENV ENV_NAME=bapa
ENV TF_CPP_MIN_LOG_LEVEL=2
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- BAPA code and trained network (in the repository), pinned commit + MD5 checks
ARG REPO=https://github.com/Blue1993/BAPA.git
ARG COMMIT=e53a2f9596647e6f3bfd2861960e19b3963b32b1
USER root
RUN mkdir -p /opt/BAPA /opt/bapa /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/BAPA /opt/bapa /data
USER $MAMBA_USER
RUN git clone "$REPO" /opt/BAPA \
 && git -C /opt/BAPA checkout "$COMMIT" \
 && cd /opt/BAPA/module \
 && echo "8f33149ef5647678b837d76de4d07ccc  network/BAPA_network.data-00000-of-00001" | md5sum -c - \
 && echo "0e58a3212977894aea457d34797fd4d5  network/BAPA_network.index" | md5sum -c - \
 && echo "6902b59208fdeb655d8a9de55797dbf8  network/BAPA_network.meta" | md5sum -c - \
 && echo "492deb69cf7788a25aea1bbff59dbb29  normalized_parameters.pkl" | md5sum -c - \
 && echo "8f227c550f689083db7a8cd2d5fa24b1  selected_descriptors_list.pkl" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_bapa.py test_1a30.py /opt/bapa/

WORKDIR /data
CMD ["python", "/opt/bapa/predict_bapa.py", "-h"]
