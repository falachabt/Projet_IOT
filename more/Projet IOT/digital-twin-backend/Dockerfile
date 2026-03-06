FROM node:18-alpine

WORKDIR /app

# Copier package.json et installer dépendances
COPY package*.json ./
RUN npm install --omit=dev

# Copier le code source
COPY . .

# Copier .env.docker comme .env
COPY .env.docker .env

# Créer dossier logs
RUN mkdir -p logs

# Port exposé
EXPOSE 3000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Commande de démarrage
CMD ["node", "server.js"]
