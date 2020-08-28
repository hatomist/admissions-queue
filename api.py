import logging
import aiohttp
from typing import Dict, Union
import prometheus


class AdmissionAPI:
    def __init__(self, host: str, token: str):
        self.host = host
        self.token = token
        self.headers = {'Authorization': f'Bearer {self.token}'}
        self.logger = logging.getLogger('AdmissionAPI')

    async def register_user(self, uid: Union[int, str], username: Union[str, None], first_name: str,
                            last_name: Union[str, None]):
        prometheus.api_requests_cnt.inc({})
        json = {}
        if username is not None:
            json['username'] = username
        json['first_name'] = first_name
        if last_name is not None:
            json['last_name'] = last_name
        json['id'] = str(uid)
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(self.host + '/users', json=json) as resp:
                assert resp.status == 200 or resp.status == 409
                self.logger.debug(f'Registered user {uid}')

    async def set_user_details(self, uid: Union[int, str], details: Dict[str, str]):
        prometheus.api_requests_cnt.inc({})
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.put(self.host + f'/users/{uid}/registration', json=details) as resp:
                assert resp.status == 200 or resp.status == 400
                self.logger.debug(f'Set details for user {uid} with response code {resp.status}: {details}')
                return await resp.json() if resp.status == 400 else None

    async def set_user_certificate(self, uid: Union[int, str], cert: Union[int, str], fio: str):
        prometheus.api_requests_cnt.inc({})
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.put(self.host + f'/users/{uid}/certificate', json={'certificate': cert,
                                                                                  'full_name': fio}) as resp:
                assert resp.status == 200 or resp.status == 400, (await resp.json())['message'] + ' ' + (await resp.json())['details']
                if resp.status == 200:
                    self.logger.debug(f'Set certificate for user {uid}: {cert}, {fio}')
                else:
                    self.logger.debug(f'Failed to set certificate for user {uid}: {cert}, {fio}, '
                                      f'{(await resp.json())["message"]}')
            return resp.status, (await resp.json())['message'] if resp.status == 400 else None

    async def get_users(self, search: Union[str, None], offset: int, size: int):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.host + f'/users?{"search=" + search + "&" if search is not None else ""}'
                                               f'skip={offset}&take={size}') as resp:
                assert resp.status == 200, (await resp.json())['message'] + ' ' + (await resp.json())['details']
                self.logger.debug(f'Got users by search \"{search}\" with offset {offset} and size {size}: '
                                  f'{await resp.json()}')
                return resp.json()

    async def get_user_info(self, uid: Union[str, int]):
        prometheus.api_requests_cnt.inc({})
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.host + f'/users/{uid}') as resp:
                assert resp.status == 200, (await resp.json())['message'] + ' ' + (await resp.json())['details']
                self.logger.debug(f'Got user {uid} info: {await resp.json()}')
                return await resp.json()

    async def count_users(self):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.host + f'/users/count') as resp:
                assert resp.status == 200, (await resp.json())['message'] + ' ' + (await resp.json())['details']
                self.logger.debug(f'Counted users: {await resp.json()}')
                return await resp.json()

    async def get_registration_template(self):
        prometheus.api_requests_cnt.inc({})
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.host + f'/templates/registration') as resp:
                assert resp.status == 200, (await resp.json())['message'] + ' ' + (await resp.json())['details']
                self.logger.debug(f'Registration template: {await resp.json()}')
                return await resp.json()

    async def add_user_to_queue(self, queue_id: Union[str, int], uid: Union[str, int]):
        prometheus.api_requests_cnt.inc({})
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(self.host + f'/queues/{queue_id}/users', json={"id": str(uid)}) as resp:
                assert resp.status == 200 or resp.status == 404 or resp.status == 400,\
                    (await resp.json())['message'] + ' ' + str(resp.status)
                self.logger.debug(f'Added user {uid} to queue {queue_id}: {await resp.json()}')
                return await resp.json(), resp.status

    async def remove_user_from_queue(self, queue_id: Union[str, int], uid: Union[str, int]):
        prometheus.api_requests_cnt.inc({})
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.delete(self.host + f'/queues/{queue_id}/users/{uid}') as resp:
                assert resp.status == 200, (await resp.json())['message'] + ' ' + (await resp.json())['details']
                self.logger.debug(f'Removed user {uid} from queue {queue_id}')

    async def get_user_position(self, queue_id: Union[str, int], uid: Union[str, int]):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.host + f'/queues/{queue_id}/users/{uid}') as resp:
                assert resp.status == 200, (await resp.json())['message'] + ' ' + (await resp.json())['details']
                self.logger.debug(f'Got user\'s {uid} position in queue {queue_id}: {await resp.json()}')
                return resp.json()

    async def get_all_users_positions(self, queue_id: Union[str, int]):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.host + f'/queues/{queue_id}/users') as resp:
                assert resp.status == 200, (await resp.json())['message'] + ' ' + (await resp.json())['details']
                self.logger.debug(f'Got users\'  positions in queue {queue_id}: {await resp.json()}')
                return await resp.json()

    async def list_queues(self):
        prometheus.api_requests_cnt.inc({})
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.host + f'/queues') as resp:
                assert resp.status == 200, (await resp.json())['message'] + ' ' + (await resp.json())['details']
                self.logger.debug(f'Got queues: {await resp.json()}')
                return await resp.json()

    async def get_queue_details(self, queue_id: Union[str, int]):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.host + f'/queues/{queue_id}') as resp:
                assert resp.status == 200, (await resp.json())['message'] + ' ' + (await resp.json())['details']
                self.logger.debug(f'Got queue {queue_id} info: {await resp.json()}')
                return await resp.json()

    async def create_queue(self, queue_name: str):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(self.host + f'/queues', json={"name": queue_name}) as resp:
                assert resp.status == 200, (await resp.json())['message'] + ' ' + (await resp.json())['details']
                self.logger.debug(f'Created queue {queue_name}: {await resp.json()}')
                return await resp.json()

    async def update_queue(self, queue_id: int):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.put(self.host + f'/queues/{queue_id}') as resp:
                assert resp.status == 200, (await resp.json())['message'] + ' ' + (await resp.json())['details']
                self.logger.debug(f'Updated queue {queue_id}: {await resp.json()}')
                return await resp.json()
