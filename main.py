from fastapi import FastAPI
from pydantic import BaseModel
import os
from pymongo import MongoClient
from hashlib import sha256

app = FastAPI()

MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE")

MONGODB_CONFIG_COLLECTION = "nhtMinerConfigs"
MONGODB_HASH_COLLECTION = "nhtHash"
DEFAULT_DIFFICULTY_LEVEL = 5
DEFAULT_SEED_STRING = "---btslabs.ai---genesis---string---"

MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME")
MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD")
MONGODB_HOSTNAME = os.environ.get("MONGODB_HOSTNAME")

mongo_uri = "mongodb://%s:27017/" % MONGODB_HOSTNAME
conn = MongoClient(host=mongo_uri)
db = conn.get_database(MONGODB_DATABASE)


class DifficultyLevel(BaseModel):
    level: int


class ClientHash(BaseModel):
    hash_string: str
    random_string: str
    seed_string: str
    difficulty_level: int
    identity: str


@app.get("/")
def root():
    return {"message": "Hello World!"}


@app.get("/init/")
def root():
    config = {"seedString": DEFAULT_SEED_STRING,
              "level": DEFAULT_DIFFICULTY_LEVEL}
    r = db.get_collection(MONGODB_CONFIG_COLLECTION).insert_one(config)
    print("Inserted: %s" % r)
    return {"inserted": str(r.inserted_id)}


@app.get("/getSeedString/")
def seed_string():
    config = db.get_collection(MONGODB_CONFIG_COLLECTION).find_one()
    print("Read: %s" % config)
    return {"seedString": config["seedString"]}


@app.get("/getDifficultyLevel/")
def difficulty_level():
    config = db.get_collection(MONGODB_CONFIG_COLLECTION).find_one()
    print("Read: %s" % config)
    return {"level": config["level"]}


@app.post("/setDifficultyLevel/")
def set_difficulty_level(level: DifficultyLevel):
    config = db.get_collection(MONGODB_CONFIG_COLLECTION).find_one()
    config["level"] = level.level
    db.get_collection(MONGODB_CONFIG_COLLECTION).update_one({"_id": config["_id"]}, {'$set': config})
    print("Updated: %s" % config)
    return {"message": "OK"}


@app.post("/sendHash/")
def send_hash(h: ClientHash):
    print("User: %s send hash: %s" % (h.identity, h.hash_string))
    content = "%s###%s" % (h.seed_string, h.random_string)
    calculated_hash = sha256(content.encode('utf-8')).hexdigest()
    if h.hash_string != calculated_hash:
        print("!!! ERROR: user [%s] hash is not validated calculated_hash[%s] != hash_string[%s]" % (h.identity,
                                                                                                     calculated_hash,
                                                                                                     h.hash_string))
    else:
        difficulty_string = "0" * h.difficulty_level
        if not calculated_hash.startswith(difficulty_string):
            print("!!! ERROR: user [%s] hash [%s] is not validated by difficulty [%s] level" % (h.identity,
                                                                                                h.hash_string,
                                                                                                h.difficulty_level))
        else:
            print("!!! SUCCESS: user [%s] hash [%s] is VALIDATED." % (h.identity,
                                                                      h.hash_string))
            hash_dict = h.dict()
            r = db.get_collection(MONGODB_HASH_COLLECTION).insert_one(hash_dict)
            print("Inserted: %s" % r)
            print("!!! SUCCESS: user [%s] earn 50 BTS-COIN" % h.identity)
            return {"inserted": str(r.inserted_id)}
    return


@app.get("/scoreTable/")
def score_table():
    i = {}
    r = db.get_collection(MONGODB_HASH_COLLECTION).find({})
    for d in r:
        iden = d["identity"]
        if iden not in i:
            i[iden] = 0
        else:
            i[iden] = i[iden] + 1

    return {"scores": i}
