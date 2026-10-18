
# LexiGuard scaffold image (scaffold only; no end-to-end flow yet).
# Production target: app + Ollama in one container; the privacy proof runs with
# `--network none` and a headless scripted flow (Phase 6), never as an
# interactive isolated UI (a --network none container publishes no ports).

FROM node:20-slim AS web
WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY tsconfig.json vite.config.ts ./
COPY frontend ./frontend
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OLLAMA_NO_CLOUD=1 \
    DO_NOT_TRACK=1 \
    HF_HUB_OFFLINE=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY backend ./backend
RUN pip install --no-cache-dir -e .
COPY --from=web /app/frontend/dist ./frontend/dist
# Phase 6: install Ollama and Tesseract, mount the model volume read-only,
# and add the headless scripted privacy flow as the isolated entrypoint.
EXPOSE 8765
CMD ["python", "-m", "app"]
