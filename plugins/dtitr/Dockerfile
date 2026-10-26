# DTITR (Monteiro et al., Comput. Biol. Med. 2022) - inference-only image for CombiLabHUB (CPU)
# Build (from this folder):   docker build -t combilab/dtitr:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM python:3.9-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates libxrender1 libxext6 \
 && rm -rf /var/lib/apt/lists/*

# --- Same pinned versions as environment.yml (TensorFlow 2.6.0 CPU)
RUN pip install --no-cache-dir \
      tensorflow-cpu==2.6.0 keras==2.6.0 tensorflow-estimator==2.6.0 tensorboard==2.6.0 \
      tensorflow-addons==0.14.0 typeguard==2.13.3 numpy==1.19.5 h5py==3.1.0 protobuf==3.20.3 \
      pandas==1.3.5 scipy==1.10.1 scikit-learn==0.24.2 matplotlib==3.6.3 seaborn==0.12.2 \
      periodictable==2.0.2 subword-nmt==0.3.8 rdkit-pypi==2022.9.5

# --- DTITR code, dictionaries and trained model (all in the repository), pinned commit, MD5 check
ARG DTITR_REPO=https://github.com/larngroup/DTITR.git
ARG DTITR_COMMIT=e8d53619a5351bbc8ee992041c91bf014629aa89
RUN git clone "$DTITR_REPO" /opt/DTITR \
 && git -C /opt/DTITR checkout "$DTITR_COMMIT" \
 && rm -rf /opt/DTITR/.git \
 && cd /opt/DTITR/model/dtitr_model \
 && echo "69c9aca0c415bb54c63a1c01c3a8da4e  .data-00000-of-00001" | md5sum -c - \
 && echo "a30a97cc47db04b22f908191a329e298  .index" | md5sum -c -

RUN useradd -m combilab && mkdir -p /opt/dtitr /data && chown combilab /data
COPY predict_dtitr.py test_1a30.py /opt/dtitr/
USER combilab
ENV TF_CPP_MIN_LOG_LEVEL=2

WORKDIR /data
CMD ["python", "/opt/dtitr/predict_dtitr.py", "-h"]
