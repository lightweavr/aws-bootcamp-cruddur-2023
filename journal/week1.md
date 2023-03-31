# Week 1 — App Containerization

All homework parts complete.

1 problem: When running the react frontend outside of Docker at the start, I didn't have the environment variable, I needed to run `REACT_APP_BACKEND_URL="https://4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}" npm start`.

One clue was the backend didn't get any requests. I wasn't expecting Node to [parse and perform interpolation on the local javascript](https://github.com/lightweavr/aws-bootcamp-cruddur-2023/blob/main/frontend-react-js/src/pages/HomeFeedPage.js#L23) before sending it to the user. (I thought React was purely client side).

The env var is used in Python for CORS (which is why `"*"` worked), but the frontend actually needs the proper URL to fetch the content.

## Docker

* Added .dockerignore files to ignore `node_modules` and `__pycache__` during the `COPY` command
* Updated base images to Python3.11-alpine and node:19-alpine, no issues observed (hopefully we don't update the base images later)
* Added Docker & Postgres helper extensions to .gitpod.yml, as well as setting port definition

## Docker Compose

* Named each container
* Moved DDB and pgsql data directory to live under /workspaces for persistence
* Added a start order to make sure the database containers start before the backend service
* Added healthchecks

Problem: the frontend container refused to start when running `docker compose up`, failed with a message about `react-server` not being found.

Wondered if it was an issue during copying the (really large) `node_modules` folder to prevent the big chunk of files from being copied, and depend on the node modules after npm install in the Docker container, but it still failed.

Changed the entrypoint in the Dockerfile to `/bin/sh`, `exec-ed` into the container after running `docker compose up` and ran `npm install` manually. `npm start` still failed.

Ran the frontend image manually with `docker run -it --entrypoint=/bin/sh  aws-bootcamp-cruddur-2023-frontend-react-js`, `npm start` once in the container worked fine.

Determined it was only failing when running `docker compose up`, suspected maybe the volume setup was problematic. Changed the volume path to include `/src` so only the source directory got mounted, running within docker compose worked fine.

Not sure why `npm install` didn't complain about the directory not being writable, unless the Docker overlay ended up silently suppressing the errors?

## Running `docker compose up` in EC2

References:

* Docker Compose plugin not included in install: <https://docs.docker.com/compose/install/linux/#install-the-plugin-manually>
* Needed to add `ec2-user` to the `docker` group: <https://phoenixnap.com/kb/docker-permission-denied>

```bash
sudo yum install docker git tmux -y
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.17.2/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
groups
docker run hello-world
sudo mkdir -p  /workspace/docker/dynamodb  /workspace/docker/psqldb
sudo chown -R ec2-user:docker /workspace
git clone https://github.com/lightweavr/aws-bootcamp-cruddur-2023.git
cd aws-bootcamp-cruddur-2023/
docker compose up
```

Showing that the backend was reachable:

```json
[ec2-user@ip-172-31-7-144 aws-bootcamp-cruddur-2023]$ curl -X GET http://localhost:4567/api/activities/home -H "Accept: application/json" -H "Content-Type: application/json"
[
  {
    "created_at": "2023-03-29T16:12:18.975109+00:00",
    "expires_at": "2023-04-05T16:12:18.975109+00:00",
    "handle": "Andrew Brown",
    "likes_count": 5,
    "message": "Cloud is fun!",
    "replies": [
      {
        "created_at": "2023-03-29T16:12:18.975109+00:00",
        "handle": "Worf",
        "likes_count": 0,
        "message": "This post has no honor!",
        "replies_count": 0,
        "reply_to_activity_uuid": "68f126b0-1ceb-4a33-88be-d90fa7109eee",
        "reposts_count": 0,
        "uuid": "26e12864-1c26-5c3a-9658-97a10f8fea67"
      }
    ],
    "replies_count": 1,
    "reposts_count": 0,
    "uuid": "68f126b0-1ceb-4a33-88be-d90fa7109eee"
  },
  {
    "created_at": "2023-03-24T16:12:18.975109+00:00",
    "expires_at": "2023-04-09T16:12:18.975109+00:00",
    "handle": "Worf",
    "likes": 0,
    "message": "I am out of prune juice",
    "replies": [],
    "uuid": "66e12864-8c26-4c3a-9658-95a10f8fea67"
  },
  {
    "created_at": "2023-03-31T15:12:18.975109+00:00",
    "expires_at": "2023-04-01T04:12:18.975109+00:00",
    "handle": "Garek",
    "likes": 0,
    "message": "My dear doctor, I am just simple tailor",
    "replies": [],
    "uuid": "248959df-3079-4947-b847-9e0892d1bab4"
  }
]
```

## Docker Healthchecks

First attempt of the healthchecks silently failed. Had to run `docker inspect backend` to see the healthcheck failure logs: `healthcheck: "OCI runtime exec failed: exec failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown"`

The problem is curl isn't in the container (I'm surprised Docker's running the healthcheck from inside the container, but it makes sense), solution is to [switch to wget](https://github.com/dotnet/AspNetCore.Docs/issues/24341#issuecomment-1004336380) which is in the alpine base image (that I changed to).

That got the healthchecks running:

```bash
$ docker compose ps
WARN[0000] The "GITPOD_WORKSPACE_ID" variable is not set. Defaulting to a blank string.
WARN[0000] The "GITPOD_WORKSPACE_CLUSTER_HOST" variable is not set. Defaulting to a blank string.
WARN[0000] The "GITPOD_WORKSPACE_ID" variable is not set. Defaulting to a blank string.
WARN[0000] The "GITPOD_WORKSPACE_CLUSTER_HOST" variable is not set. Defaulting to a blank string.
WARN[0000] The "GITPOD_WORKSPACE_ID" variable is not set. Defaulting to a blank string.
WARN[0000] The "GITPOD_WORKSPACE_CLUSTER_HOST" variable is not set. Defaulting to a blank string.
NAME                IMAGE                                         COMMAND                  SERVICE             CREATED              STATUS                        PORTS
backend             aws-bootcamp-cruddur-2023-backend-flask       "python3 -m flask ru…"   backend-flask       About a minute ago   Up About a minute (healthy)   0.0.0.0:4567->4567/tcp, :::4567->4567/tcp
db                  postgres:13-alpine                            "docker-entrypoint.s…"   db                  13 minutes ago       Up About a minute             0.0.0.0:5432->5432/tcp, :::5432->5432/tcp
dynamodb            amazon/dynamodb-local:latest                  "java -jar DynamoDBL…"   dynamodb            13 minutes ago       Up About a minute             0.0.0.0:8000->8000/tcp, :::8000->8000/tcp
frontend            aws-bootcamp-cruddur-2023-frontend-react-js   "docker-entrypoint.s…"   frontend-react-js   About a minute ago   Up About a minute (healthy)   0.0.0.0:3000->3000/tcp, :::3000->3000/tcp
```
