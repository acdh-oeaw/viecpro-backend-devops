import redis


#TODO: move those into secrets file
client = redis.Redis(
    host='redis',
    port="6379", 
    password=None,
db=0)

