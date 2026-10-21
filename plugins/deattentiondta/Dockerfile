# DEAttentionDTA (2024) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/deattentiondta:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Python 3.10 + CPU PyTorch + Open Babel, all from conda-forge
RUN micromamba create -y -n deattentiondta -c conda-forge \
      python=3.10 "pytorch=2.3.1=cpu*" openbabel=3.1.1 numpy=1.26.4 pandas=2.2.3 \
 && micromamba clean --all --yes
ENV ENV_NAME=deattentiondta
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- DEAttentionDTA code, 10 fold models and pre-processed data (all in the repository), pinned commit + MD5 checks
ARG DEA_REPO=https://github.com/whatamazing1/DEAttentionDTA.git
ARG DEA_COMMIT=6a9618c0e93b2224797ab0067119be3d73e81a98
USER root
RUN mkdir -p /opt/DEAttentionDTA /opt/deattentiondta /data && chown -R $MAMBA_USER:$MAMBA_USER /opt/DEAttentionDTA /opt/deattentiondta /data
USER $MAMBA_USER
RUN git clone "$DEA_REPO" /opt/DEAttentionDTA \
 && git -C /opt/DEAttentionDTA checkout "$DEA_COMMIT" \
 && cd "/opt/DEAttentionDTA/src/model" \
 && printf '%s\n' \
      "7c9ce530d8d8858752668d827bc31027  Fold 1 best_model.ckpt" \
      "122ad4a28ea09cf3f6168aa0c9461908  Fold 2 best_model.ckpt" \
      "f446cbfcc6d88bfac09a41c7a56c8bc2  Fold 3 best_model.ckpt" \
      "895f192e69d9df518197cd916d8a9ea5  Fold 4 best_model.ckpt" \
      "2bf1dbe1567c84bd8b3663261b167e19  Fold 5 best_model.ckpt" \
      "0fb0d10c3be693479ee5fab97f577d34  Fold 6 best_model.ckpt" \
      "7cdc46d7df1026fe526b4002a4c29ca2  Fold 7 best_model.ckpt" \
      "13454ecee193d90834fa086e0873c8ac  Fold 8 best_model.ckpt" \
      "870c9d79f9fc0e67e845987cb369ca10  Fold 9 best_model.ckpt" \
      "c9df6afe748c2314b077f38132ae2bb5  Fold 10 best_model.ckpt" \
    | md5sum -c -

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_deattentiondta.py test_1a30.py /opt/deattentiondta/

WORKDIR /data
CMD ["python", "/opt/deattentiondta/predict_deattentiondta.py", "-h"]
