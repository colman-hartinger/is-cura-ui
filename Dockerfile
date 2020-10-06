FROM ultimaker/cura-build-environment:python3.7-debian-latest

# Environment vars for easy configuration
ENV CURA_APP_DIR=/srv/cura

# Ensure our sources dir exists
RUN mkdir $CURA_APP_DIR

# Setup Uranium
ENV URANIUM_BRANCH=4.6
WORKDIR $CURA_APP_DIR
RUN git clone -b $URANIUM_BRANCH --depth 1 https://github.com/Ultimaker/Uranium

# Setup materials
ENV MATERIALS_BRANCH=master
WORKDIR $CURA_APP_DIR
RUN git clone -b $MATERIALS_BRANCH --depth 1 https://github.com/Ultimaker/fdm_materials materials

# Setup Cura
WORKDIR $CURA_APP_DIR/Cura
ADD . .
RUN mv $CURA_APP_DIR/materials resources/materials

# Make sure Cura can find CuraEngine
# RUN ln -s /usr/local/bin/CuraEngine $CURA_APP_DIR/Cura docker build --tag cura_dev:1.0 .

# Run Cura
WORKDIR $CURA_APP_DIR/Cura
ENV PYTHONPATH=${PYTHONPATH}:$CURA_APP_DIR/Uranium
RUN apt-get install -y mesa-utils xvfb

# Uncomment to run tests when docker image runs
# RUN chmod +x ./run_unit_tests.sh
# CMD "./run_unit_tests.sh"
