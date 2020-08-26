import motor.motor_asyncio

client = motor.motor_asyncio.AsyncIOMotorClient()
db = client.adm_queue
# {uid: int, stage: int, lang: str, certnum: str, tokens: [{}], template_stage: int, tokens_num: int, 't_*': str,
# 'o_*': str, get_queue: int, leave_queue: int, opt_reg: bool, opt_reg_completed: False}
users = db.users
