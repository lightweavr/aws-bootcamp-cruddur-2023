FROM 017145807427.dkr.ecr.us-west-2.amazonaws.com/ecr-public/docker/library/node:19-alpine

ENV PORT=3000

COPY . /frontend-react-js
WORKDIR /frontend-react-js
RUN npm install
EXPOSE ${PORT}
ENV REACT_APP_BACKEND_URL="https://4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}"
CMD ["npm", "start"]
