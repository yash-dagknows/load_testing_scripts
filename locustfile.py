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
            "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkYWdrbm93cy5jb20iLCJzdWIiOiJ5YXNoQGRhZ2tub3dzLmNvbSIsIm5iZiI6MTczNjQ1Mjc5MCwiZXhwIjoxNzY3OTg4OTcwLCJqdGkiOiJsQ0czZ3h3U0ZzbUl1ZDZkIiwiYXVkIjoiZGFna25vd3MiLCJyb2xlIjoiYWRtaW4iLCJ1c2VyX2NsYWltcyI6eyJ1aWQiOiIzOSIsInVuYW1lIjoieWFzaEBkYWdrbm93cy5jb20iLCJvcmciOiJkYWdrbm93cyIsImZpcnN0X25hbWUiOiJZYXNoIiwibGFzdF9uYW1lIjoiWWFkYXYiLCJyb2xlIjoiQWRtaW4iLCJhZXNfa2V5IjoiRGZrMlFucEsvVDlZREZqZ3MwSWIyZytGaXVnS2dSUUsiLCJvZnN0IjpbNDA5LDE4NSwxNjksMzE4LDY4LDE2MCw5OCwzOTgsMzEwLDI0MiwyNDYsMTMxLDIwNiwzODAsMTg4LDI3NiwzNTYsMzUzLDM2OCw5MiwyODIsMzMwLDMxMSwzMzksMzM0LDcxLDI2NCwyOTMsMjc2LDg4LDI1Miw2NV19fQ.Um-DMFIMeT1x-xAat_K8FZcPA0Sl4EhOpXGPvCQee0C_ljztKEmTcpjWVMuDttIRcBiPSUGZSj8olfclT9nxHfFL5hMgJ97a6patSvLaaFfuz7DkJcXmP5eaQGQyx_h1sxWsEgZf7rnenuCRn78ksHjTxOQnAJn7e3OmhIwV2qR6vZgVc2hI9YKonmuFrllu3SqJk93XNhY4C0oH6yTznqjRna4pJVCJIP0iKllqIDyGQAoa4v_u00_xhMMfk6newl9IGo6jQ9xVja77Hmzl09BPuxm2xGvO7pkXj4nYDIjRZV6Lw5-ZV1x0c8n8TJqhCuaEttTeFUUiuUvlartn-A"
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