from locust import HttpUser, task, between, events
import json
import time
import statistics


"""
# Run this script using:
locust -f locustfile.py --headless -u 1 -r 1 --run-time 60s --host https://dev.dagknows.com
"""
# Globals to store metrics
response_times = []
failures = 0
successes = 0
start_ts = None

class GrafanaAlertUser(HttpUser):
    # Send one request every second
    wait_time = between(1, 1)
    # wait_time = between(6, 6)

    def on_start(self):
        global start_ts
        start_ts = time.time()

    @task
    def send_grafana_alert(self):
        global successes, failures

        url = "/processObservabilityEvent?proxy=dev&taskid=R5OnlfP9DDvUVlpAIJCt"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer <TOKEN VALUE>"
        }

        with open("grafana_alert_sample.json") as f:
            payload = json.load(f)

        start_time = time.time()
        with self.client.post(url, json=payload, headers=headers, name="GrafanaAlertPOST", catch_response=True) as response:
            duration = (time.time() - start_time) * 1000  # in ms
            response_times.append(duration)

            if response.status_code == 200:
                response.success()
                successes += 1
                print(f"[✓] Success - Time: {duration:.2f} ms")
            else:
                response.failure(f"Failed with status {response.status_code}")
                failures += 1
                print(f"[✗] Failed - Status: {response.status_code}, Time: {duration:.2f} ms")


@events.quitting.add_listener
def display_summary(environment, **kwargs):
    total = successes + failures
    duration_sec = time.time() - start_ts if start_ts else 1
    rps = total / duration_sec

    print("\n--- Test Summary ---")
    print(f"Total requests: {total}")
    print(f"Successes: {successes}")
    print(f"Failures: {failures}")
    print(f"Test duration: {duration_sec:.2f} seconds")
    print(f"Requests/sec: {rps:.2f}")

    if response_times:
        print(f"Average response time: {statistics.mean(response_times):.2f} ms")
        print(f"Min response time: {min(response_times):.2f} ms")
        print(f"Max response time: {max(response_times):.2f} ms")