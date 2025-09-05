### In this script we do not wait for the response time from the server and 
### send the request regardless whether the request was processed or not to mimic a real world scenario 
### where we do not know if request will be sent only after the previous request has been responded to by the server

from locust import HttpUser, task, events
import json
import time
import statistics
import threading
import logging
import os


"""
Run with:
locust -f alternate_users_load_test_another.py --headless -u 2 -r 2 --run-time 65s
"""

token = os.getenv("dev_dk_token")
if not token:
    raise RuntimeError("Environment variable 'dev_dk_token' not set!")

# Host dev.dagknows.com defined in the class below so we don't have to pass it as a CLI argument while running the file
"""
Run with:
locust -f alternate_users_load_test.py --headless -u 2 -r 2 --run-time 65s
"""

# Suppress verbose locust logs
logging.getLogger("locust").setLevel(logging.WARNING)

# Global metrics
response_times = []
failures = 0
successes = 0
start_ts = None

# Synchronization primitive
lock = threading.Lock()
next_user_id = 1

class AlternatingUser(HttpUser):
    host = "https://dev.dagknows.com"
    user_id = None
    start_delay = 0

    # Dummy task to satisfy Locust
    @task
    def noop(self):
        pass

    def on_start(self):
        global start_ts, next_user_id

        with lock:
            self.user_id = next_user_id
            next_user_id += 1
            if start_ts is None:
                start_ts = time.time()

        self.start_delay = 0 if self.user_id == 1 else 1
        print(f"[+] User {self.user_id} initialized. Start delay: {self.start_delay}s")

        threading.Thread(target=self.alternate_request_loop).start()

    def alternate_request_loop(self):
        global successes, failures

        time.sleep(self.start_delay)  # offset 0s for user 1, 1s for user 2
        interval = 2  # fire every 2 seconds
        next_run = time.time()
        end_time = next_run + 60  # run for 1 minute

        while time.time() < end_time:
            url = "/processObservabilityEvent?proxy=dev&taskid=R5OnlfP9DDvUVlpAIJCt"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }

            with open("grafana_alert_sample.json") as f:
                payload = json.load(f)

            start_time = time.time()
            with self.client.post(url, json=payload, headers=headers, name=f"User{self.user_id}-POST", catch_response=True) as response:
                duration = (time.time() - start_time) * 1000  # ms
                response_times.append(duration)

                if response.status_code == 200:
                    response.success()
                    successes += 1
                    print(f"[✓] User {self.user_id} - Success: {duration:.2f} ms")
                else:
                    response.failure(f"Failed with status {response.status_code}")
                    failures += 1
                    print(f"[✗] User {self.user_id} - Failed: {response.status_code}, {duration:.2f} ms")

            # Schedule the next request exactly 2s after the last scheduled one
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
        print(f"Average response time: {statistics.mean(response_times):.2f} ms")
        print(f"Min response time: {min(response_times):.2f} ms")
        print(f"Max response time: {max(response_times):.2f} ms")