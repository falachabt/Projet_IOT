# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Installer dépendances
COPY package*.json ./
RUN npm install

# Copier code source et builder
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copier les fichiers buildés
COPY --from=build /app/dist /usr/share/nginx/html

# Configuration Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
