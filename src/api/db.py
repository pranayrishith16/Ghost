from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi

uri = "mongodb+srv://admin:admin@cluster0.zglnave.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace <db_password> with your password
client = MongoClient(
    uri,
    server_api=ServerApi('1'),
    tls=True,
    tlsCAFile=certifi.where()
)
db = client["user_auth"]            # Replace with your database name


#collections
users_collection = db["users"]
free_user_usage_collection = db['free_user_usage']
refresh_tokens_collection = db['refresh_tokens']

# create TTL index for expiring free user usage docs automatically
free_user_usage_collection.create_index("expires_at",expireAfterSeconds=0)

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
