import asyncio
import random
import os
from datetime import date

from nio import AsyncClient, RoomMessageImage, RoomGetStateResponse, RoomEncryptedImage

MATRIX_HOMESERVER_URL = os.getenv('MATRIX_HOMESERVER_URL')
MATRIX_USERNAME = os.getenv('MATRIX_USERNAME')
MATRIX_PASSWORD = os.getenv('MATRIX_PASSWORD')
MATRIX_ACCESS_TOKEN = os.getenv('MATRIX_ACCESS_TOKEN')
TIMESTAMP = os.getenv('TIMESTAMP')
PREFIX = os.getenv('PREFIX')
DATE_FORMAT = os.getenv('DATE_FORMAT')

class MatrixBot:
    def __init__(self):
        self.client = AsyncClient(MATRIX_HOMESERVER_URL, MATRIX_USERNAME)
        self.client.access_token = MATRIX_ACCESS_TOKEN

    async def fetch_room_media(self, room_id):
        media_list = []
        token = "END"  # a not None start token, actual value doesn't matter

        while True:
            # fetch room messages
            response = await self.client.room_messages(room_id, token)
            token = response.end

            # add media messages to the list
            media_list.extend([
                msg for msg in response.chunk
                if isinstance(msg, RoomMessageImage)
                and "url" in msg.source["content"]  # only media messages have 'url'
                and int(TIMESTAMP) >= int(msg.source["origin_server_ts"])
                ])

            if token is None:  # all messages have been fetched
                break

        return media_list

    async def send_media_message(self, random_media):
        post_date = date.fromtimestamp(random_media.source["origin_server_ts"]/1000)
        post_date = post_date.strftime(DATE_FORMAT)
        content = {
            "msgtype": "m.text",
            "body": PREFIX+' '+post_date
        }
        await self.client.room_send(random_media.source["room_id"], "m.room.message", content)

        await self.client.room_send(
                room_id=random_media.source["room_id"],
                message_type="m.room.message",
                content=random_media.source["content"]
                )

    async def run(self):
        # login
        await self.client.login(MATRIX_PASSWORD)

        response = await self.client.joined_rooms()
        for room in response.rooms:
            # fetch room media then randomly select and send one
            media_list = await self.fetch_room_media(room)
            print(room, "Fetched room media")
            if not media_list:
                print(room, "The room is E2EE or doesn't have any media in it")
                continue # the room is E2EE or doesnt have any media in it
            random_media = random.choice(media_list)
            await self.send_media_message(random_media)
            print(room, "Sent randomly chosen media to the room")

        await self.client.logout()
        await self.client.close()

if __name__ == "__main__":
    bot = MatrixBot()
    asyncio.run(bot.run())
