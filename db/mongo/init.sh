#!/bin/bash
set -e

echo "Initializing MongoDB..."

# Wait for MongoDB to be ready
until mongosh --eval "db.adminCommand('ping')" &> /dev/null; do
    sleep 1
done

mongosh <<-EOF
    rs.initiate({
        _id: "rs0",
        members: [{ _id: 0, host: "localhost:27017" }]
    });
EOF

# Sleep to allow replicaset to initialize
sleep 5

# Run collection creation script
mongosh < /docker-entrypoint-initdb.d/collections.js

echo "MongoDB initialized successfully."

