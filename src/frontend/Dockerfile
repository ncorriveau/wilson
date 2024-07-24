FROM node:18.7 as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ARG VITE_REACT_APP_API_URL
ENV VITE_REACT_APP_API_URL=$VITE_REACT_APP_API_URL
RUN npm run build
RUN ls -la /app/dist

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]