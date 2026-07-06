FROM node:20-bookworm-slim

# Install wget and gnupg to download package signing keys if needed
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency lists
COPY package*.json tsconfig.json ./

# Install npm dependencies
RUN npm ci

# Install chromium browser binary and its system OS level libraries
RUN npx playwright install chromium --with-deps

# Copy the rest of the application source code
COPY src ./src

# Compile typescript sources
RUN npm run build

# Expose default HTTP/WS port
EXPOSE 8080

# Run compiled output
CMD ["npm", "start"]
