# DB installations

## MongoDB Community Server

https://www.mongodb.com/docs/v8.0/tutorial/install-mongodb-on-ubuntu/

Latest release 8.3
Need to import public key etc first.
Install latest release: sudo apt-get install -y mongodb-org

(Version in your ITG202: v8.0.26; major long term release 8.0)
Check: mongod --version

## Neo4j Community Edition (CE)

https://neo4j.com/docs/operations-manual/current/installation/linux/debian/

Current stable release 1:2026.07.1
Need to add the repository first.
Install latest release: sudo apt-get install neo4j=1:2026.07.1

(Version in your ITG202: 1:2026.06.0)
Check: apt list --installed | grep neo4j

## ChromaDB: 

Current stable release: 1.5.9
pip install chromadb=1.5.9

(Version in your ITG202: 1.5.9)
Check: pip show chromadb

## systemctl
sudo systemctl status mongod
sudo systemctl restart mongod
sudo systemctl enable mongod