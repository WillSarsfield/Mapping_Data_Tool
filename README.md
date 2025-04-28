# TPI_UK_Colour_Mapping
Visualization tool for ONS Regional productivity dataset

## Using Docker

### Prerequisite: install Docker Desktop

See https://docs.docker.com/get-docker/ for detailed instructions for installing Docker Desktop on Linux, Windows and macOS.

Once installed, make sure Docker Desktop is running and open a shell prompt (Linux/macOS) or PowerShell (Windows) and type:

```
docker run hello-world
```
To confirm everything is working. If you see an error message along the lines of 'Cannot connect to the Docker daemon' then restart Docker Desktop and try again.


### Build the Docker image

To build a Docker image for the app, make sure your inside the same folder as the Dockerfile and type: 

```
docker build -t tpi-uk-colour-mapping .
```

The image name 'tpi-uk-colour-mapping' is just an example - you can call it what you want.

### Run the app in a Docker container

The following command will start the app running in a Docker container accessible at [localhost:8888](http://localhost:8888)

```
docker run --rm  -p 8888:80 tpi-uk-colour-mapping
```

You can change `8888` to a different local port if preferred. 

### Local development using docker compose

You can use docker compose to build & run the app during local development. Make sure you're inside the same folder as the Dockerfile, and then you can start the app by typing the following: 

```
docker compose up -d --build
```

This will build and start a docker container, serving the app at [localhost:8888](http://localhost:8888). 

Local changes to source files are automatically reflected inside the container and can be tested without the need to restart/rebuild the containers. 

You can bring the app down by typing: 

```
docker compose down
```

You can start the app on a different local port by passing the STREAMLIT_PORT environment variable on the command line. E.g. to serve the app at [localhost:8080](http://localhost:8080):

```
STREAMLIT_PORT=8080 docker compose up -d --build
```

## Google Analytics

You can add an optional Google Analytics tracking tag by passing it as a build argument either when building the image or when using docker compose.

### Adding your google tag when building the image

If your google tag is *GT-XXXX* then pass it as a `--build-arg` named `GOOGLE_ANALYTICS_ID` when calling docker build:

```
docker build --build-arg GOOGLE_ANALYTICS_ID=GT-XXXX -t tpi-uk-colour-mapping .
```

### Adding your google tag using docker compose

You can add your google tag in two ways when using docker compose: passing it on the command line, or using a .env file

#### 1. Pass GOOGLE_ANALYTICS_ID on the command line when invoking docker compose 

```
GOOGLE_ANALYTICS_ID=GT-XXXX docker compose up -d --build
```

#### 2. Use a .env file

Docker compose will look for a file called `.env` and use it to set environment variables used when building images. Create a file called `.env` and add the following to it:

```
GOOGLE_ANALYTICS_ID=GT-XXXX
```

Then invoke docker compose as normal:

```
docker compose up -d --build
```
