# DeltaVinaRF20 (Wang & Zhang, J. Comput. Chem. 2017) - inference-only image for CombiLabHUB (CPU)
# Full pipeline with the authors' Python 2 code: MGLTools 1.5.7, vina4dv (Vina terms), Open Babel 2.4.1 + MSMS
# (buried SASA by pharmacophore type) and R randomForest (trained model rffit.rda).
# Build (from this folder):   docker build -t combilab/deltavinarf20:1.0 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Three environments: deltavinarf20 (Python 2.7 + Open Babel 2.4.1 + MSMS + R), mgltools (Python 2.7)
#     and vinabuild (g++ 12 + Boost 1.82, to compile vina4dv)
COPY --chown=$MAMBA_USER:$MAMBA_USER environment_pipeline.yml environment_mgltools.yml /tmp/
RUN micromamba create -y -f /tmp/environment_pipeline.yml \
 && micromamba create -y -f /tmp/environment_mgltools.yml \
 && micromamba create -y -n vinabuild -c conda-forge gxx_linux-64=12.4 libboost-devel=1.82 \
 && micromamba clean --all --yes
ENV ENV_NAME=deltavinarf20
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- deltavina code + trained model, and vina4dv; pinned commits + MD5 checks.
# vina4dv is compiled from source, as in the RFL-Score image: its prebuilt static binary crashes on kernels
# without vsyscall (WSL 2 of Docker Desktop). atmtypenumbers (MSMS 2.6.1 radii table, needed by pdb_to_xyzr)
# comes from the delta_LinF9_XGB repository (same group), pinned commit.
ARG DV_REPO=https://github.com/chengwang88/deltavina.git
ARG DV_COMMIT=612bbe7f8b854a583ab81f4f1357422b0c108c98
ARG VINA_REPO=https://github.com/chengwang88/vina4dv.git
ARG VINA_COMMIT=d8e4cd1b350200bf0e622721fd41102a4dbb5f5a
ARG ATM_URL=https://raw.githubusercontent.com/cyangNYU/delta_LinF9_XGB/54ae79584f7e22f5af3e28625b9f387f0b74cc0f/software/atmtypenumbers
USER root
RUN mkdir -p /opt/deltavina /opt/vina4dv /opt/deltavinarf20 /data \
 && chown -R $MAMBA_USER:$MAMBA_USER /opt/deltavina /opt/vina4dv /opt/deltavinarf20 /data
USER $MAMBA_USER
RUN git clone "$DV_REPO" /opt/deltavina \
 && git -C /opt/deltavina checkout "$DV_COMMIT" \
 && cd /opt/deltavina \
 && echo "944e70f5ded661296aa29f1470e372cc  deltavina/models/rffit.rda" | md5sum -c - \
 && echo "e979213b05a9042a2287ea27016dca7d  examples/input.csv" | md5sum -c - \
 && curl -fsSL -o /opt/deltavinarf20/atmtypenumbers "$ATM_URL" \
 && echo "85e40580c9e77d4584e860b6f01a6e51  /opt/deltavinarf20/atmtypenumbers" | md5sum -c - \
 && git clone "$VINA_REPO" /opt/vina4dv \
 && git -C /opt/vina4dv checkout "$VINA_COMMIT" \
 && cd /opt/vina4dv/src \
 && sed -i 's/path(str, boost::filesystem::native)/path(str)/; s/native_file_string()/string()/g' main/main.cpp \
 && B=/opt/conda/envs/vinabuild && mkdir -p /opt/vina4dv/build/gcc \
 && $B/bin/x86_64-conda-linux-gnu-g++ -O3 -DNDEBUG -std=c++11 -w -I$B/include -Ilib -o /opt/vina4dv/build/gcc/vina \
      main/main.cpp lib/cache.cpp lib/coords.cpp lib/current_weights.cpp lib/everything.cpp lib/grid.cpp lib/szv_grid.cpp \
      lib/manifold.cpp lib/model.cpp lib/monte_carlo.cpp lib/mutate.cpp lib/my_pid.cpp lib/naive_non_cache.cpp lib/non_cache.cpp \
      lib/parallel_mc.cpp lib/parse_pdbqt.cpp lib/pdb.cpp lib/quasi_newton.cpp lib/quaternion.cpp lib/random.cpp lib/ssd.cpp \
      lib/terms.cpp lib/weighted_terms.cpp \
      -L$B/lib -Wl,-rpath,$B/lib -lboost_system -lboost_thread -lboost_serialization -lboost_filesystem -lboost_program_options -lpthread \
 && /opt/vina4dv/build/gcc/vina --help > /dev/null
ENV MGLPY=/opt/conda/envs/mgltools/bin/python \
    MGLUTIL=/opt/conda/envs/mgltools/MGLToolsPckgs/AutoDockTools/Utilities24/ \
    VINADIR=/opt/vina4dv/build/gcc/

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_deltavinarf20.py test_1a30.py pdb_to_xyzr.py features_1a30.csv /opt/deltavinarf20/

WORKDIR /data
CMD ["python", "/opt/deltavinarf20/predict_deltavinarf20.py", "-h"]
