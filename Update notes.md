# Updates
## Comments 

- The orchestrator, in this context is quite dummy, because we want it so, but it could be more complex, for instance: organizing input/output information from service to service. In the case that your message starts getting complex, you might not want to introduce that business logic  per service, but integrated in the orchestrator. See examples below.
- Regarding microservices, avoid complex strings when possible, use properly defined json.

## Running scenario

Imaginge you have your hardware/software ready, how would you like your system to run? I can imagine an scenario in which:
1. The system is started, and automaticall, one service per task is started and remain idle.
2. A client sents an order, *somehow*. The order contains:
	1. Just one image
3. You know the client, so *it has associated a business setup*. For instance:
	1. Client X, sends image Y: we know client X's contract describes that services tasks A,B,C have to be executed per each request. These services could be:
		1. A: Adjust color & brightness
		2. B: Resize image for multiple devices( low/mid/high  resolutions)
		3. C: Apply client's watermark
		4. **forget about images here, and where you should store and so on, the imporant part is that each service should be independent from the rest, but they might need outputs from previous services** See examples below.
		


My point here is, your system should be active and listening for requests, in your context, the orders can be defined on the fly, or predefined in csv or something else, but **the process starting or sending the requests should be different from the process starting the system & services**.
From this scenario we also see that each service might need to access the output from the previous one.

Your system should have an starting and an end point:
- Starting point: The request with the image, or already with the tasks defined, that is not really relevant. The relevant here is associating an id.
- End point: All tasks have been executed, you have the id, so it can be removed from your list of active orders, or something like that.

## Heuristics

### Preliminaries
Your system is monitoring the tasks, so at any given time you know:
1. Number of active orders
2. Number of active tasks/services
3. You could infer the number of tasks still yet to be performed (you know the active orders, with their services)
	1. This is extremely important and one of the main reasons to have a queue system, because heavy operations have to be async
	
### Heuristics 1o1
1. If a service is idle for more than X seconds, it is switched off. When a new task is required to be performed, if the service is switched off, it has to be started.
	- How would you implement such logic with your current setup?
2. If you have many active orders that require task A to be completed, this task will become a bottleneck, so:
	- How would you detect such bottleneck, and what measures can be applied to reduce the overhead (perhaps starting another instance of such service, 2 instances can do the double amount of work than just a single one.)

# Examples
## Example 1
Define such a system that contains services to perform:  A: + 2, B: x 2, input: 5
### Step 1: START (indestion)
```
START: 
- input : {'input':5 'todo':['A', 'B']}
- output {'input':5 'todo':['A', 'B'], 'done':[]}
- next : send to orchestrator
```
### Step 2: Orchestrator (1)
```
orchestrator:
- input : {'input':5, 'tasks':['A', 'B'], 'done':[]}
- output : {'input':5, 'tasks':['A', 'B'], 'done':[]}
- next: send to service A
```
### Step 3: Service A
```
service A:
- input : {'input':5, 'tasks':['A', 'B'], 'done':[]}
- action : 5 + 2 = 7
- output : {'input':7, 'tasks':['A', 'B'], 'done':['A']}
- next :  send to orchestrator
```
### Step 3: Orchestrator (2)
```
orchestrator:
- input : {'input':7, 'tasks':['A', 'B'], 'done':['A']}
- output : {'input':7, 'tasks':['A', 'B'], 'done':['A']}
- next: send to service B
```
### Step 4: Service B
```
service B:
- input : {'input':7, 'tasks':['A', 'B'], 'done':['A']}
- action : 7 x 2 = 14
- output : {'input':14, 'tasks':['A', 'B'], 'done':['A','B']}
- next :  send to orchestrator
```
### Step 5: Orchestrator (3)
```
orchestrator:
- input : {'input':14, 'tasks':['A', 'B'], 'done':['A','B']}
- output : {'input':14, 'tasks':['A', 'B'], 'done':['A','B']}
- next: send to service END
```
### Step 6: END
```
END
- input : {'input':14, 'tasks':['A', 'B'], 'done':['A','B']}
- output : {'result':14}
- next: send to client/database/etc..
```

## Example 2
Same system, same services, same input: A: + 2, B: x 2, input: 5. but slightly different request, smarter orchestrator:
### Step 1: START (indestion)
```
START: 
- input : {'input':5 'todo':['B', 'A']}
- output {'input':5 'todo':['B', 'A'], 'from':['start']}
- next : send to orchestrator
```
### Step 2: Orchestrator (1)
```
orchestrator:
- input : 
	{"input":5 "todo":["B", "A"], "from":["start"]}
- output : 
	{"input":5,"tasks":["B","A"],"jobs":{"B":{"input":5}}}
- next: send to service A
```
### Step 3: Service B
```
service A:
- input : 
	{"input":5,"tasks":["B","A"],"jobs":{"B":{"input":5}}}
- action : 5 x 2 = 10
- output : 
	{"input":5,"tasks":["B","A"],"jobs":{"B":{"input":5,"result":10}},"from":"B"}
- next :  send to orchestrator
```
### Step 3: Orchestrator (2)
```
orchestrator:
- input : 
	{"input":5,"tasks":["B","A"],"jobs":{"B":{"input":5,"result":10}},"from":"B"}
- output : 
{"input":5,"tasks":["B","A"],"jobs":{"B":{"input":5,"result":10},"A":{"input":10}}}
- next: send to service B
```
### Step 4: Service A
```
service B:
- input : 
{"input":5,"tasks":["B","A"],"jobs":{"B":{"input":5,"result":10},"A":{"input":10}}}
- action : 10 + 2 = 12
- output : 
{"input":5,"tasks":["B","A"],"jobs":{"B":{"input":5,"result":10},"A":{"input":10,"result":12}},"from":"A"}
- next :  send to orchestrator
```
### Step 5: Orchestrator (3)
```
orchestrator:
- input :
- {"input":5,"tasks":["B","A"],"jobs":{"B":{"input":5,"result":10},"A":{"input":10,"result":12}},"from":"A"}
- output :
{"input":5,"tasks":["B","A"],"jobs":{"B":{"input":5,"result":10},"A":{"input":10,"result":12}}}
- next: send to service END
```
### Step 6: END
```
END
- input : 
{"input":5,"tasks":["B","A"],"jobs":{"B":{"input":5,"result":10},"A":{"input":10,"result":12}}}
- output : {'result':12}
- next: send to client/database/etc..
```
## Comments:
In this example, the order of the tasks is different, so the final result is also different, even though the services and the main input is the same.
The different here also is that we have an orchestrator that performs some tidying on the message, and that every task is traced, so we keep the original input at each step, and append results when necesary. By having the attribute `"from"` the orchestrator can discern where the task should go next.