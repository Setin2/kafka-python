import json

# python string dictionary
x = '{ "input":5, "orderID": 3, "required_tasks":["A", "B"], "task_name": "A", "completed_tasks":[]}'

# python dictionary object
dictData= json.loads(x)

#modify
dictData["input"] /= 2
dictData["completed_tasks"].append(dictData["task_name"])

# convert back to string
y = str(dictData)

# the result is a JSON string:
print(y)

orchestrator_input = """{
            "input": {input},
            "orderID": {orderID},
            "required_tasks": {required_tasks},
            "completed_tasks": {completed_tasks}
        }""".format(
            input = 5,
            orderID = orderID,
            required_tasks = order["required_tasks"],
            completed_tasks = order["completed_tasks"]

        )