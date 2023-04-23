import json

# python string dictionary
x = '{ "input":5, "orderID": 3, "required_tasks":["A", "B"], "current_task": "A", "completed_tasks":[]}'

# python dictionary object
dictData= json.loads(x)

#modify
dictData["input"] += 2
dictData["completed_tasks"].append(dictData["current_task"])

# convert back to string
y = str(dictData)

# the result is a JSON string:
print(y)