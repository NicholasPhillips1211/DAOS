FROM node:20-alpine

WORKDIR /app

COPY package.json ./
COPY tsconfig.json ./
COPY vite.config.ts ./
COPY index.html ./
COPY postcss.config.cjs ./
COPY tailwind.config.cjs ./
COPY src ./src

RUN npm install
RUN npm run build

EXPOSE 4173
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "4173"]
