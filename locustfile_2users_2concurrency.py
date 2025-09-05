from locust import HttpUser, task, events
import json
import time
import statistics
import threading
import logging
import os


"""
# Run the script using
locust -f locustfile_2users_2concurrency.py --headless -u 2 -r 2 --run-time 65s
"""
# Set up logging
logging.getLogger("locust").setLevel(logging.WARNING)

# Get token from env var
token = os.getenv("dev_dk_token")
if not token:
    raise RuntimeError("Environment variable 'dev_dk_token' not set!")

# Metrics
response_times = []
failures = 0
successes = 0
start_ts = None

# For alternating users
lock = threading.Lock()
next_user_id = 1

class AlternatingUser(HttpUser):
    host = "https://dev.dagknows.com"
    user_id = None
    start_delay = 0

    @task
    def noop(self):
        pass  # Required to avoid Locust error

    def on_start(self):
        global start_ts, next_user_id

        with lock:
            self.user_id = next_user_id
            next_user_id += 1
            if start_ts is None:
                start_ts = time.time()

        self.start_delay = 0 if self.user_id == 1 else 1
        print(f"[+] User {self.user_id} initialized. Delay: {self.start_delay}s")

        threading.Thread(target=self.fixed_interval_loop).start()

    def fixed_interval_loop(self):
        global successes, failures

        time.sleep(self.start_delay)
        interval = 2
        next_run = time.time()
        end_time = next_run + 60

        while time.time() < end_time:
            url = "/processObservabilityEvent?proxy=dev&taskid=R5OnlfP9DDvUVlpAIJCt"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }

            with open("grafana_alert_sample.json") as f:
                payload = json.load(f)

            start = time.time()
            with self.client.post(url, json=payload, headers=headers, name=f"User{self.user_id}-POST", catch_response=True) as response:
                duration = (time.time() - start) * 1000
                response_times.append(duration)

                if response.status_code == 200:
                    response.success()
                    successes += 1
                    print(f"[✓] User {self.user_id} - {duration:.2f} ms")
                else:
                    response.failure(f"Status {response.status_code}")
                    failures += 1
                    print(f"[✗] User {self.user_id} - {duration:.2f} ms")

            next_run += interval
            sleep_time = next_run - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

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
        print(f"Avg response time: {statistics.mean(response_times):.2f} ms")
        print(f"Min: {min(response_times):.2f} ms | Max: {max(response_times):.2f} ms")