import asyncio
import pprint
from backend.app.database import connect_to_mongo, db

async def run():
    await connect_to_mongo()
    u = await db.db.users.find_one({})
    if u:
        print("User:", u.get("email"))
    else:
        print("No users found.")

if __name__ == "__main__":
    asyncio.run(run())
