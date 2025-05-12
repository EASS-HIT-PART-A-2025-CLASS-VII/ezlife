# Use Node 18 with Debian for better compatibility
FROM node:18.19.1-slim

WORKDIR /app

# Install build essentials for native modules
RUN apt-get update && \
    apt-get install -y python3 make g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package*.json ./

# Configure npm and install dependencies
ENV PYTHON=/usr/bin/python3
RUN npm install -g node-gyp && \
    npm cache clean --force && \
    NODE_ENV=development npm install --force && \
    npm rebuild

# Copy the rest of the application
COPY . .

ENV HOST=0.0.0.0
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
