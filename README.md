# scholarps-exporter

[![Badge](https://img.shields.io/badge/docker-legnoh/scholarps--exporter-blue?logo=docker&link=https://hub.docker.com/r/legnoh/scholarps-exporter)](https://hub.docker.com/r/legnoh/scholarps-exporter) [![publish](https://github.com/legnoh/scholarps-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/legnoh/scholarps-exporter/actions/workflows/ci.yml)

Prometheus(OpenMetrics) exporter for [スカラネット・パーソナル](https://scholar-ps.sas.jasso.go.jp/mypage/).

## Usage

### Start(Docker)

The simplest way to use it is with Docker.

```
docker run -p 8000:8000 \
     -e SCHOLARPS_ID="yourloginidhere" \
     -e SCHOLARPS_PASSWORD="yourpasswordhere" \
     -e SCHOLARPS_NUMBER="123-45-678901" \
    legnoh/scholarps-exporter
```

### Start(source)

Alternatively, it can be started from the source.

```sh
# clone
git clone https://github.com/legnoh/scholarps-exporter.git && cd scholarps-exporter
uv sync --frozen

# prepare .env file for your apps
cat << EOS > .env
SCHOLARPS_ID="yourloginidhere" \
SCHOLARPS_PASSWORD="yourpasswordhere" \
SCHOLARPS_NUMBER="123-45-678901" \
EOS

# run exporter
uv run main.py
```

## Metrics

please check [metrics.yml](./config/metrics.yml)

## Disclaim

- This script is NOT authorized by Scholarnet Personal and JASSO.
  - We are not responsible for any damages caused by using this script.
- This script is not intended to overload these sites or services.
  - When using this script, please keep your request frequency within a sensible range.
