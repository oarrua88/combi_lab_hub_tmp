# GraphscoreDTA (Wang et al., Bioinformatics 2023) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/graphscoredta:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.10 + CPU PyTorch 2.3.1 + conda-forge DGL 2.2.1 (same recipe as the egGNN plugin)
RUN micromamba create -y -n gsdta -c conda-forge \
      python=3.10 "pytorch=2.3.1=cpu*" "libtorch=2.3.1=cpu*" numpy=1.26.4 pandas=2.2.3 scipy=1.15.2 \
      networkx=3.4.2 psutil pydantic pyyaml requests tqdm metis=5.1.1 liburing=2.7 pip \
 && micromamba install -y -n gsdta -c conda-forge --no-deps "dgl=2.2.1=py310h039f8d5_2" \
 && micromamba clean --all --yes
ENV ENV_NAME=gsdta
ENV DGLBACKEND=pytorch
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN pip install --no-cache-dir --no-deps torchdata==0.8.0

# --- GraphscoreDTA code + trained models (in the repository), pinned commit + MD5 checks,
#     and the authors' pre-processed CASF-2016 graphs (GitHub release "Data")
ARG GS_REPO=https://github.com/CSUBioGroup/GraphscoreDTA.git
ARG GS_COMMIT=d7d1230fb33d803f5c8f86e66c1598ab4d7ea68d
ARG GRAPHS_URL=https://github.com/CSUBioGroup/GraphscoreDTA/releases/download/Data/all_in_one_graph_test2016.bin
USER root
RUN mkdir -p /opt/GraphscoreDTA /opt/graphscoredta /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/GraphscoreDTA /opt/graphscoredta /data
USER $MAMBA_USER
RUN git clone "$GS_REPO" /opt/GraphscoreDTA \
 && git -C /opt/GraphscoreDTA checkout "$GS_COMMIT" \
 && echo "428d508d75994a853f75fd0cc9c3c4da  /opt/GraphscoreDTA/model/modelp.pth" | md5sum -c - \
 && curl -sSL -o /opt/GraphscoreDTA/test_set/all_in_one_graph_test2016.bin "$GRAPHS_URL" \
 && echo "a8c2ad64c46c2f13a6702a0856bde044  /opt/GraphscoreDTA/test_set/all_in_one_graph_test2016.bin" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_graphscoredta.py test_1a30.py /opt/graphscoredta/

WORKDIR /data
CMD ["python", "/opt/graphscoredta/test_1a30.py", "--gs-dir", "/opt/GraphscoreDTA"]
