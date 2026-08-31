# DB installations on Amazon Linux (RH-based OS)

## MongoDB Community Server
MongoDB's default port is 27017

https://www.mongodb.com/docs/v8.0/tutorial/install-mongodb-on-amazon/#std-label-install-mdb-community-amazon-linux

sudo yum install -y mongodb-org
mongod --version
db version v8.0.29

## The EC2 instance comes with DBs running in separate Docker containers
sudo docker ps --filter publish=27017
sudo docker inspect mongodb
sudo docker inspect mongodb --format '{{json .Config.Env}}'
(Result: MONGO_VERSION=7.0.40)

## Connect to MongoDB in Docker container
sudo docker exec -it mongodb mongosh
mongosh "mongodb://localhost:27017"

## If you want to use the native MongoDB installation
sudo docker stop mongodb
sudo systemctl start mongod
sudo systemctl status mongod

## Neo4j Community Edition (CE)
Neo4j's default port is 7687 (Docker version has additional port 7474)

https://neo4j.com/docs/operations-manual/current/installation/linux/debian/

Current stable release 1:2026.07.1
Need to add the repository first.
Install latest release: sudo apt-get install neo4j=1:2026.07.1

(Version in your ITG202: 1:2026.06.0)
Check: apt list --installed | grep neo4j

sudo docker inspect 935feb8e2cee
sudo docker inspect 935feb8e2cee \
  --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}'
sudo docker inspect 935feb8e2cee \
  --format '{{range .Config.Env}}{{println .}}{{end}}' | grep NEO4J
(Result: NEO4J_AUTH=neo4j/IFAfA8bVXzKsPzWFhaan)

sudo docker exec neo4j neo4j --version
(Result: 5.26.29)

## ChromaDB
ChromaDB's default port is 8000 
Current stable release: 1.5.9
pip install chromadb=1.5.9
Check: pip show chromadb

python -c "import chromadb; print(chromadb.__version__)"
(Result: 1.5.9)

## MongoDB RBAC (local installation)
## Previously stored in config.py
mongo_user_credentials = """[
    {"username": "hfyee", "password": "9108122d"},
    {"username": "tsteo", "password": "3897044t"},
    {"username": "mkao", "password": "6667044q"}
]"""
password_list = json.loads(mongo_user_credentials)
password_lookup = {user["username"]: user["password"] for user in password_list}
MONGO_USER = "hfyee"
MONGO_PASSWORD = password_lookup.get(MONGO_USER)
