FROM node:23-alpine

RUN apk add chromium

WORKDIR /usr/src/app
COPY app/package.json package.json
RUN npm i 
COPY app .

CMD ["npm","start"]
