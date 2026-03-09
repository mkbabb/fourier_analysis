FROM node:22-slim AS base
WORKDIR /app

FROM base AS deps
COPY web/package.json web/package-lock.json ./
RUN npm install -g npm@latest && hash -r && npm ci

FROM deps AS development
COPY web/ .
CMD ["npm", "run", "dev", "--", "--host", "--port", "3000"]

FROM deps AS builder
ARG VITE_API_URL=/api
ARG VITE_BASE_URL=/fourier/
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_BASE_URL=${VITE_BASE_URL}
COPY web/ .
# Assets needed by the paper figures (symlink won't resolve in Docker)
COPY assets/ public/assets/
# Paper .tex and .bib needed by vite-plugin-latex-paper at build time
COPY paper/fourier_paper.tex paper/fourier_paper.bib /paper/
RUN npm run build

FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    location ~* \\.(?:js|css|woff2|png|jpg|svg)$ {\n\
        expires 1y;\n\
        add_header Cache-Control "public, immutable";\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf
