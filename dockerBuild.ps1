docker build `
--build-arg MONGODB_URL=mongodb://mongo:Park123!@db:27017/ `
--build-arg MONGODB_DB=dmarcdb `
--build-arg MONGODB_HOST=db `
--build-arg MONGODB_PORT=27017 `
--build-arg MONGODB_USERNAME=mongo `
--build-arg MONGODB_PASSWORD=Park123! `
--build-arg MONGODB_USE_SSL=false `
--build-arg MONGODB_REPLICASET= `
--build-arg MONGODB_DIRECT_CONNECTION=true `
--build-arg MONGODB_AUTH_MECHANISM=DEFAULT `
--build-arg SESSION_TYPE=filesystem `
--build-arg REDIS_URL=redis://queue:6379 `
--build-arg REDIS_QUEUE_NAME=DMARC_QUEUE `
-t dmarc .
