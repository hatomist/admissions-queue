import motor.motor_asyncio
import os

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ['MONGO_URI'])
db = client.adm_queue
# {uid: int, stage: int, lang: str, certnum: str, tokens: [{}], template_stage: int, tokens_num: int, 't_*': str,
# 'o_*': str, get_queue: int, leave_queue: int, opt_reg: bool, opt_reg_completed: False}
users = db.users
