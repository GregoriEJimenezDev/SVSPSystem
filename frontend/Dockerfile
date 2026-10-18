FROM node:22-alpine AS build
WORKDIR /src
COPY package*.json ./
RUN npm ci
COPY . .
# "npm run build" ejecuta tsc, pero no existe tsconfig.json: se usa vite directo
RUN npx vite build

FROM caddy:2
COPY --from=build /src/dist /srv
COPY Caddyfile /etc/caddy/Caddyfile