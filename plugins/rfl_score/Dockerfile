# RFL-Score v1 (Arrua, Aderhold, Werhli & Machado, IEEE CIBCB 2024) - inference-only image for CombiLabHUB (CPU)
# Full pipeline: Open Babel 2.4.1, PaDEL (Java), DSSP, MGLTools, vina4dv and R randomForest.
# Build (from this folder):   docker build -t combilab/rfl_score:1.1 .
# See INSTALL.md, section B, for how to run it.

FROM mambaorg/micromamba:1.5.10

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates dssp \
 && rm -rf /var/lib/apt/lists/*
USER $MAMBA_USER

# --- Three environments: rfl (Python 3.7 + R), mgltools (Python 2.7) and vinabuild (g++ 12 + Boost 1.82, to compile vina4dv)
COPY --chown=$MAMBA_USER:$MAMBA_USER environment_pipeline.yml environment_mgltools.yml /tmp/
RUN micromamba create -y -f /tmp/environment_pipeline.yml \
 && micromamba create -y -f /tmp/environment_mgltools.yml \
 && micromamba create -y -n vinabuild -c conda-forge gxx_linux-64=12.4 libboost-devel=1.82 \
 && micromamba clean --all --yes
ENV ENV_NAME=rfl
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# --- RFL-Score code + trained model, and vina4dv; pinned commits + MD5 checks.
# vina4dv is compiled from source: its prebuilt static binary (build/linux/release/vina, Intel compiler, 2016)
# crashes (segmentation fault) on kernels without vsyscall, such as the WSL 2 kernel used by Docker Desktop.
# Built with g++ its output for 1a30 is identical to the prebuilt binary's (checked).
ARG RFL_REPO=https://github.com/combilab-furg/rfl-score_v1.git
ARG RFL_COMMIT=2020d9039436b7c48891753a3d7aa5a97a239246
ARG VINA_REPO=https://github.com/chengwang88/vina4dv.git
ARG VINA_COMMIT=d8e4cd1b350200bf0e622721fd41102a4dbb5f5a
USER root
RUN mkdir -p /opt/rfl-score_v1 /opt/vina4dv /opt/rfl_score /data \
 && chown -R $MAMBA_USER:$MAMBA_USER /opt/rfl-score_v1 /opt/vina4dv /opt/rfl_score /data
USER $MAMBA_USER
RUN git clone "$RFL_REPO" /opt/rfl-score_v1 \
 && git -C /opt/rfl-score_v1 checkout "$RFL_COMMIT" \
 && cd /opt/rfl-score_v1 \
 && echo "d1ad344ed3f167e2e053e97dd1f9890e  scoring/RScript/model/scoring_function_160.rda" | md5sum -c - \
 && echo "cc59df3203179361fbcb7d063dfb06dd  examples/1a30/1a30_160_input.csv" | md5sum -c - \
 && git clone "$VINA_REPO" /opt/vina4dv \
 && git -C /opt/vina4dv checkout "$VINA_COMMIT" \
 && echo "6d78ba24f4b507a6edb29888f41e0d61  /opt/vina4dv/build/linux/release/vina" | md5sum -c - \
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

COPY --chown=$MAMBA_USER:$MAMBA_USER predict_rfl_score.py test_1a30.py /opt/rfl_score/

WORKDIR /data
CMD ["python", "/opt/rfl_score/predict_rfl_score.py", "-h"]
