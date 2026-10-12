FROM node:24-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . ./
RUN npm run build

FROM node:24-slim

WORKDIR /app

RUN groupadd -g 10002 appgroup && \
    useradd -u 10002 -g appgroup -s /bin/sh -m appuser && \
    npm install -g serve && \
    mkdir -p /app/dist && \
    chown -R appuser:appgroup /app

COPY --from=builder --chown=appuser:appgroup /app/dist /app/dist

USER appuser

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
