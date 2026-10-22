# PointNet / PointTransformer (Wang et al., Brief. Bioinform. 2022) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/pointnet:1.0 .
# See INSTALL.md, section B, for how to run it.
# The image holds the whole pipeline: Open Babel + the authors' POINTNET program
# (Linux) to make the point clouds, and the 10 trained models.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

RUN micromamba create -y -n pointnet -c conda-forge \
      python=3.10 numpy=1.26.4 pandas=2.2.3 openbabel=3.1.1 \
      "pytorch=2.3.1=cpu*" "libtorch=2.3.1=cpu*" \
 && micromamba clean --all --yes
ENV ENV_NAME=pointnet
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- Point-Cloud code, POINTNET program and trained models (in the repository, ~500 MB), pinned commit + MD5 checks
ARG REPO=https://github.com/wyji001/Point-Cloud.git
ARG COMMIT=d1eae550bdaffbb877cb36a2a6e362d4dc625fe4
USER root
RUN mkdir -p /opt/PointCloud /opt/pointnet /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/PointCloud /opt/pointnet /data
USER $MAMBA_USER
RUN git clone "$REPO" /opt/PointCloud \
 && git -C /opt/PointCloud checkout "$COMMIT" \
 && rm -rf /opt/PointCloud/.git \
 && chmod +x /opt/PointCloud/POINTNET* \
 && cd /opt/PointCloud \
 && echo "2aaddebe49fd1d029a9e490ea447ade0  POINTNET" | md5sum -c - \
 && echo "3d3aa22b5d463afa410edb90442a1071  Model/PointTransformer（B）/0.819.pth" | md5sum -c - \
 && echo "06b2accb965eee68522be4c7618f70b9  Model/PointTransformer（B）/0.820.pth" | md5sum -c - \
 && echo "1459c86ddf53a1b8f1dc4b580cbd09fe  Model/PointTransformer（B）/0.821.pth" | md5sum -c - \
 && echo "3520b636819590300bbd2b8b3cad946f  Model/PointTransformer（B）/0.822.pth" | md5sum -c - \
 && echo "0dde813d2d3d2803145b21263041d19d  Model/PointTransformer（B）/0.827.pth" | md5sum -c - \
 && echo "dcc42ffdecd42389d7a805ba56975bd3  Model/PointNet（B）/0.764.pth" | md5sum -c - \
 && echo "6af6b4d085287e56fbfa471a868f7511  Model/PointNet（B）/0.787.pth" | md5sum -c - \
 && echo "dd113c80dd989eecd3e17c756fe72587  Model/PointNet（B）/0.788.pth" | md5sum -c - \
 && echo "b55676fcb3f3e9c804e56eb0c63c362d  Model/PointNet（B）/0.791.pth" | md5sum -c - \
 && echo "cfd480099688307dca8a8076ef7862a2  Model/PointNet（B）/0.794.pth" | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_pointnet.py test_1a30.py ref_1a30_cloud.txt /opt/pointnet/

WORKDIR /data
CMD ["python", "/opt/pointnet/predict_pointnet.py", "-h"]
