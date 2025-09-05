from locust import HttpUser, task, between, events
import json
import time
import statistics
import os


"""
# Run it using:
locust -f locustfile_single+burst_variation.py --headless -u 2 -r 2 --run-time 65s
"""
# Shared globals
response_times = []
failures = 0
successes = 0
start_ts = None

# Token via env var
token = os.getenv("dev_dk_token")
if not token:
    raise RuntimeError("Environment variable 'dev_dk_token' not set!")

# Alert logic
def post_alert(client, name):
    global successes, failures

    url = "/processObservabilityEvent?proxy=dev&taskid=R5OnlfP9DDvUVlpAIJCt"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    with open("grafana_alert_sample.json") as f:
        payload = json.load(f)

    start_time = time.time()
    with client.post(url, json=payload, headers=headers, name=name, catch_response=True) as response:
        duration = (time.time() - start_time) * 1000
        response_times.append(duration)

        if response.status_code == 200:
            response.success()
            successes += 1
            print(f"[✓] {name} - Time: {duration:.2f} ms")
        else:
            response.failure(f"Failed with status {response.status_code}")
            failures += 1
            print(f"[✗] {name} - Status: {response.status_code}, Time: {duration:.2f} ms")

# Steady user: 1 request every 2s
class SteadyUser(HttpUser):
    host = "https://dev.dagknows.com"
    wait_time = between(2, 2)

    def on_start(self):
        global start_ts
        start_ts = time.time()

    @task
    def send_steady(self):
        post_alert(self.client, "SteadyRequest")

# Burst user: sends 4 requests every 5s (burst style)
class BurstUser(HttpUser):
    host = "https://dev.dagknows.com"
    wait_time = between(5, 5)

    @task
    def send_burst(self):
        for i in range(4):  # burst of 4 requests
            post_alert(self.client, f"BurstRequest-{i+1}")

# Print summary at the end
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