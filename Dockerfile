# Use this version of Python
ARG PYTHON_VERSION=3.11
# Use this version of uv
ARG UV_VERSION=0.7

# Install uv using the official image
# See https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv-distroless

# The devcontainer should use the developer target and run as root with podman
# or docker with user namespaces.
FROM python:${PYTHON_VERSION} AS developer

# Add any system dependencies for the developer/build environment here
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     graphviz

# Install from uv image
COPY --from=uv-distroless /uv /uvx /bin/

# The build stage installs the context into the venv
FROM developer AS build
# Copy only dependency files first
COPY pyproject.toml uv.lock /context/
WORKDIR /context

# Enable bytecode compilation and copy from the cache instead of linking 
# since it's a mounted volume
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /context
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# The runtime stage copies the built venv into a slim runtime container
FROM python:${PYTHON_VERSION}-slim AS runtime
# Add apt-get system dependecies for runtime here if needed

# We need to keep the venv at the same absolute path as in the build stage
COPY --from=build /context/.venv/ /context/.venv/
ENV PATH=/context/.venv/bin:$PATH

# Change this entrypoint if it is not the same as the repo
ENTRYPOINT ["dls-edm"]
CMD ["--version"]
