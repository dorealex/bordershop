import asyncio
import random

async def profile_1():
  print("Profile 1")
  wait = random.choice([1,2])
  asyncio.sleep(wait)

async def profile_2():
  print("Profile 2")
  wait = random.choice([5,10])
  asyncio.sleep(wait)

async def profile_3():
  print("Profile 3")
  wait = 15
  asyncio.sleep(wait)

async def main():
    # Schedule three calls *concurrently*:
    L = await asyncio.gather(
      profile_1(),
      profile_2(),
      profile_3()
    )
    print(L)

asyncio.run(main())