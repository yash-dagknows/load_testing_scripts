# Load Testing with Locust

This repo contains Locust scripts to perform load testing against **[DagKnows Dev](https://dev.dagknows.com)** APIs.  

## Prerequisites

- [Install Locust](https://docs.locust.io/en/stable/installation.html):

  ```bash
  pip install locust
  ```

- Ensure you are in the project directory where the `locustfile.py` scripts are located.

---

## Running Locust Tests

### 1. Single User – 60 Requests/Minute
One user sending **1 request every second** (using `wait_time=(1,1)`):  

```bash
locust -f locustfile.py \
  --headless \
  -u 1 \
  -r 1 \
  --run-time 1m \
  --host https://dev.dagknows.com
```

---

### 2. Ten Users – 100 Requests/Minute
Ten users, each sending **1 request every 6 seconds**:  

```bash
locust -f locustfile.py \
  --headless \
  --users 10 \
  --spawn-rate 10 \
  --run-time 1m \
  --host https://dev.dagknows.com
```

---

### 3. Burst Testing
Ten users starting together, creating a short burst of load:  

```bash
locust -f locustfile_single+burst.py \
  --headless \
  --users 10 \
  --spawn-rate 10 \
  --run-time 1m \
  --host https://dev.dagknows.com
```

---

## Notes

- Tune `--users`, `--spawn-rate`, and `--run-time` to simulate different workloads.   
