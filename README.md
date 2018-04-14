This API performs two functions:
 1. harvest data from the CRM and usage servers, and store it in the database
 1. provide endpoints for clients to request report data for services

## Requirements
 - Python 3.6
 - Docker (developed against 17.12)
 - a database that works with SQLAlchemy (developed against Postgres)

## Quickstart for Docker
First things, we need to build the docker image:
```bash
docker build \
  -t tomsaleeba/supersummariser \
  .
```

Now, we can run the app. You have two choices 1) use `docker-compose` to start the app and a database together, or 2) run the app in a container and use your own database.

### docker-compose
The easy way is to use `docker-compose` to start the app and database, like this:
```bash
cd ./docker/
# edit docker-compose.yml to add your ERSA_AUTH_TOKEN (and don't commit)
docker-compose up
```

Now, if this is the first run, we'll need to init the database. We do that by exec-ing into the docker container with our app, and running a command:
```bash
# open another terminal because the docker-compose stack is still running in the other one
docker exec \
  -it \
  -e FLASK_APP=main.py \
  `docker ps --filter ancestor=tomsaleeba/supersummariser -q` \
  /bin/bash -c 'flask db upgrade'
```

### Docker single container
Or, if you want to run just the app because you already have a database, you can do that too. This example shows supplying the database URI as well as a number of other configuration options so the harvesting will point back to a machine on LAN rather than hit the *real* servers:
```bash
docker run \
  -it \
  --rm \
  -p 5000:80 \
  -e REPORTING_SERVER='http://192.168.0.3:5001' \
  -e CRM_SERVER='http://192.168.0.3:5001/bman' \
  -e USAGE_SERVER='http://192.168.0.3:5001' \
  -e ERSA_AUTH_TOKEN='222dcbdc-06cb-413b-9e91-21f7e5523b80' \
  -e SQLALCHEMY_DATABASE_URI='postgresql://user:secretpassword@192.168.0.3/custom_db'
  tomsaleeba/supersummariser
```

# Config
This app is written as a [12 factor](https://12factor.net/) app. Namely, it writes logs to the console and uses environment variables for config. When running with Docker, you can pass environment variables using the `-e` argument to `docker run`. For a list of options, see `supersummariser/settings.py` in the `Config` class.

At a minimum, you'll have to pass the `ERSA_AUTH_TOKEN` option as there is no default for that.

# Endpoints
At the time of writing, there are 5 services supported:
 1. hpcsummary (HPC compute usage)
 1. hpcstorage (HPC storage usage)
 1. nectar (OpenStack compute usage)
 1. tango (In-house cloud compute usage)
 1. allocationsummary (general storage usage)

Chart data is the main focus of this API at this time, so you'll find a `/<service>/chart` endpoint for all of those services. There are various examples of the other 3 endpoints, spread over the services, to prove suitability for future use: `/<service>/simple/<year>/<month>`, `/<service>/rollup/<year>/<month>` and `/<service>/detailed/<year>/<month>`.

The `GET /chart` endpoint supports the following query string params:
 - `month_window=int`(default=12) defines the number of months to go back (from the current month) to gather chart data. Set this to how many months you want on your chart.
 - `org=str` (default='') allows you to filter the results to only contain a single organisation. The value must be an exact match (case sensitive). You can pull values from a call without the filter so you get everything back.

The `GET /process` endpoint is the trigger for performing a harvest from the CRM and usage systems. It supports the following query string parameters:
 - `months_back=int` (default=2) number of months to harvest data for. 1 means the current month, regardless of what day in the month it is. 2 means the current month and the previous, and so on. It handles months with different lengths correctly. This function is idempotent so you can re-run it whenever you want. The idempotent behaviour is achieved in two ways:
   1. for contract/account data, we delete an existing record before writing a new one
   1. for usage data, we delete the entire month for the service before writing all the fresh data

# Limitations
 1. usage data that can't be joined to the contract/account data **will not** be returned in responses from this API. If you want this information included, you'll need to make a code change for `LEFT JOIN` type behaviour.
 1. no security is applied to the reporting data endpoints. It is assumed that the web server can provide this.

# Unit tests
You can run unit tests with:
```bash
nose2
```

## Quickstart to run on host
This is a great way to develop the app as code changes will be hot reloaded.
```bash
git clone <this repo>
cd supersummariser
export SQLALCHEMY_DATABASE_URI=sqlite:///ss.db # or run postgres with ./docker/pg_db/run-postgres.sh
export FLASK_DEBUG=1
export FLASK_APP=autoapp.py
# create and activate virtualenv, if you want, then
export ERSA_AUTH_TOKEN=aabbb11a-16ea-3dc0-9d2d-5368f80707e6 # get this value from sessionStorage['secret'] in the reporting portal
pip install -r requirements.txt
flask db upgrade
flask run
# in a third terminal
curl http://localhost:5000/process # call harvester to populate data
curl http://localhost:5000/hpcsummary/chart # get HPC summary chart data for all orgs
curl http://localhost:5000/hpcsummary/chart?org=Austides # get HPC summary chart data for one org
```
