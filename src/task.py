import asyncio
import logging
import time
import types

import const

tasks: dict[str, asyncio.Task] = {}
tasklist_maxlength = const.TASKLIST_MAXLENGTH


def _gc():
    if len(tasks) > tasklist_maxlength:
        completed_tasks = [
            (task_id, task) for task_id, task in tasks.items() if task.done()
        ]
        completed_tasks.sort(key=lambda x: x[1]._created_time)
        tasks_to_delete = tasklist_maxlength // 2
        for task_id, task in completed_tasks[:tasks_to_delete]:
            del tasks[task_id]


def create_task(coro: types.CoroutineType):
    _gc()
    task = asyncio.create_task(coro)
    task._created_time = time.time()
    hash_ = str(hash(task))
    task._hashid = hash_
    tasks[hash_] = task
    return hash_
