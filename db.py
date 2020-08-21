import motor.motor_asyncio

client = motor.motor_asyncio.AsyncIOMotorClient()
db = client.adm_queue
users = db.users
queues = db.queues
