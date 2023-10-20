# ---
# cmd: ["python", "misc/queue_simple.py"]
# runtimes: ["runc", "gvisor"]
# ---
#
# # Using a queue to send/receive data
#
# This is an example of how to use queues to send/receive data.
# We don't do it here, but you could imagine doing this _between_ two functions.


import asyncio

import modal
import modal.queue

stub = modal.Stub("example-queue-simple", q=modal.Queue.new())


@stub.function()
async def run_async(q: modal.Queue) -> None:
    print(q)
    print(q.put)
    await q.put.aio(42)
    r = await q.get.aio()
    assert r == 42
    await q.put_many.aio([42, 43, 44, 45, 46])
    await q.put_many.aio([47, 48, 49, 50, 51])
    r = await q.get_many.aio(3)
    assert r == [42, 43, 44]
    r = await q.get_many.aio(99)
    assert r == [45, 46, 47, 48, 49, 50, 51]


@stub.function()
async def many_consumers(q: modal.Queue) -> None:
    print("Creating getters")
    tasks = [asyncio.create_task(q.get.aio()) for i in range(20)]
    print("Putting values")
    await q.put_many.aio(list(range(10)))
    await asyncio.sleep(1)
    # About 10 tasks should now be done
    n_done_tasks = sum(1 for t in tasks if t.done())
    assert n_done_tasks == 10
    # Finish remaining ones
    await q.put_many.aio(list(range(10)))
    await asyncio.sleep(1)
    assert all(t.done() for t in tasks)


async def main():
    with stub.run():
        await run_async.remote.aio(stub.q)
        await many_consumers.remote.aio(stub.q)


if __name__ == "__main__":
    asyncio.run(main())
