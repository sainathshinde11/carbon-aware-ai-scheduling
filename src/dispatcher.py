"""
Dispatcher (Section 3.1 / Figure 1 of the paper).

In a production deployment, the Dispatcher would hold a scheduled job until
its selected start time t_s* arrives, then hand it off to the underlying
compute infrastructure (Kubernetes, SLURM, a cloud GPU cluster, etc.) for
actual execution in the selected region r*.

For this simulation/evaluation codebase, the Dispatcher does not actually
wait or execute anything — it logs the dispatch decision, which is what the
experiment runner uses to build the results table. Swap `dispatch()` for a
real API call (e.g. submitting a Kubernetes Job, or a cloud batch job) to
move this from simulation to production.
"""


class Dispatcher:
    def __init__(self):
        self.log = []

    def dispatch(self, schedule_result: dict):
        """
        Record a scheduling decision. In production this is where you would
        call out to the actual job orchestration system, e.g.:

            kubernetes_client.create_namespaced_job(
                body=job_spec, namespace=schedule_result["region"]
            )

        or hold the job (e.g. via a delayed queue / cron trigger) until
        schedule_result["start_time"] arrives.
        """
        entry = {
            "job_id": schedule_result["job_id"],
            "dispatched_to_region": schedule_result["region"],
            "scheduled_start": schedule_result["start_time"],
            "status": schedule_result["status"],
        }
        self.log.append(entry)
        return entry

    def get_log(self):
        return self.log
