FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --production
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build 2>/dev/null || true
EXPOSE 8004
CMD ["node", "--experimental-specifier-resolution=node", "dist/index.js"]
