#!/usr/bin/env bash
cd `dirname "$0"`

port=5432
if [ ! -z "$1" ]; then
  port=$1
fi

docker run \
 --name ersa-postgres \
 -e POSTGRES_PASSWORD=mysecretpassword \
 --rm \
 -it \
 -p $port:5432 \
 -v `pwd`/sql-init:/docker-entrypoint-initdb.d \
 postgres:10.2
