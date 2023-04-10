import sys
import kubernetes_job_cluster

taskID = sys.argv[1]
required_services = sys.argv[2]
required_services = eval(required_services)

# start the required services in the order specified
for i, service_name in enumerate(required_services):
    # start the job for the service
    service_job = kubernetes_job_cluster.create_job(service_name, [str(required_services), service_name, taskID])
    # wait for the job to complete
    kubernetes_job_cluster.wait_for_job_completion(service_name)

