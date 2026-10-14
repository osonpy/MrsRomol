# Builds the Mini App and serves it with Caddy, which also proxies the API
# and gets HTTPS certificates automatically. Build context: repository root.
FROM node:20-alpine AS build
WORKDIR /src
COPY miniapp/package.json miniapp/package-lock.json ./
RUN npm ci
COPY miniapp/ ./
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM caddy:2-alpine
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /src/dist /srv/miniapp
