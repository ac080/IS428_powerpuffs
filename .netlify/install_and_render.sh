#!/usr/bin/env bash
set -euo pipefail

QUARTO_VERSION="1.4.550"

echo "Installing Quarto ${QUARTO_VERSION}..."

curl -fsSL -o quarto.tar.gz \
  https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.tar.gz

mkdir -p .quarto
tar -xzf quarto.tar.gz -C .quarto --strip-components=1

export PATH="$PWD/.quarto/bin:$PATH"

quarto --version
quarto render