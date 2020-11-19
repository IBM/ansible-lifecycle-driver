#!/usr/bin/env bash
set -e 

title(){
  NAME=$1
  echo "=============================================="
  echo "$NAME"
  echo "=============================================="
}

# Clear out old whls
title "Clearing out old whls"
rm -rf ./build
rm -rf ./dist
rm -rf docker/whls
mkdir docker/whls
echo "Cleared"

# Ensure we have the right Python libs to run setup
title "Ensuring Setuptools is ready"
python3 -m pip install -U setuptools wheel

# Build whl
title "Building Whl"
python3 setup.py bdist_wheel

# Copy whl to docker source
title "Copy Whl to Docker Source"
cp -r dist/. docker/whls/
echo "Copied"

# Build docker image
title "Build Docker Image"
docker build -t ansible-lifecycle-driver:2.1.0.dev0.nfviautomation ./docker