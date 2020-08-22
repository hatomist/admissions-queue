import motor.motor_asyncio

client = motor.motor_asyncio.AsyncIOMotorClient()
db = client.adm_queue
# {uid: int, stage: int, lang: str, certnum: str, template: {}, template_stage: int, tokens_num: int, 't_*': str}
users = db.users
