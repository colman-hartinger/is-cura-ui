#!/usr/bin/env bash

# UNCOMMENT FOR A SPECIFIC BRANCH OF PYWIM/PY3MF
#git clone https://github.com/tetonsim/pywim.git
#git clone https://github.com/tetonsim/py3mf.git
#mv pywim/pywim SmartSlicePlugin/3rd-party/cpython-common
#mv py3mf/threemf SmartSlicePlugin/3rd-party/cpython-common

# shellcheck disable=SC2046
git clone -b $1 --single-branch https://github.com/Ultimaker/Cura.git
mv SmartSlicePlugin Cura/plugins

python3 -m pip install PyQt5==5.10 teton-3mf teton-pywim

# shellcheck disable=SC2164
cd Cura
PYTHONPATH=${PYTHONPATH}:$(pwd)

Xvfb :1.0 -screen 0 1280x800x16 &
export DISPLAY=:1.0
export QT_QPA_PLATFORM=offscreen
python3 plugins/SmartSlicePlugin/tests/run.py