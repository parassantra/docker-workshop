# Module 1 Homework: Docker & SQL - Solutions

This document describes the step-by-step solutions for the Docker & SQL homework from the Data Engineering Zoomcamp.

---

## Question 1: Understanding Docker Images

**Task:** Run docker with the `python:3.13` image and find the version of pip.

### Steps:

1. Run the Python 3.13 Docker container in interactive mode with bash entrypoint:

```bash
docker run -it --rm --entrypoint bash python:3.13
```

**Flags explained:**
- `-it`: Interactive mode with TTY (allows you to interact with the container)
- `--rm`: Automatically removes the container when it exits (cleanup)
- `--entrypoint bash`: Overrides the default entrypoint to start a bash shell instead of Python

2. Once inside the container, check the pip version:

```bash
pip --version
```

3. Output:

```
pip 25.3 from /usr/local/lib/python3.13/site-packages/pip (python 3.13)
```

**Answer: `25.3`**

---

## Question 2: Understanding Docker Networking and docker-compose

**Task:** Determine the hostname and port that pgAdmin should use to connect to the PostgreSQL database.

### Docker Compose Configuration Analysis:

```yaml
services:
  db:
    container_name: postgres
    image: postgres:17-alpine
    ports:
      - '5433:5432'  # Maps host:5433 -> container:5432
    ...

  pgadmin:
    container_name: pgadmin
    image: dpage/pgadmin4:latest
    ports:
      - "8080:80"
    ...
```

### Steps to Verify:

1. Start the services:

```bash
docker compose up -d
```

2. Access pgAdmin at `http://localhost:8080`

3. Login with:
   - Email: `pgadmin@pgadmin.com`
   - Password: `pgadmin`

4. Register a new server with connection details

### Why the Answer is `db:5432`:

- **Service name as hostname:** In Docker Compose, services can communicate using the **service name** as the hostname (not the container name). The service is named `db`, so the hostname is `db`.

- **Internal port:** When containers communicate within the same Docker network, they use the **internal container port** (`5432`), not the mapped host port (`5433`).

- **Port mapping context:**
  - `5433:5432` means: Host port 5433 → Container port 5432
  - From host machine: Use `localhost:5433`
  - From another container (pgAdmin): Use `db:5432`

**Answer: `db:5432`**

---

## Questions 3-6: Data Preparation and SQL Queries

### Prerequisites: Python Environment Setup

This project uses [uv](https://docs.astral.sh/uv/) as the Python package manager. The `homework` folder is located inside the `pipeline` directory.

#### Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

#### Setup the Python Environment

```bash
# Navigate to the pipeline directory (parent of homework)
cd pipeline

# Install dependencies
uv sync

# Verify installation (should show Python 3.13.x)
uv run python --version
```

> **Note:** This project requires Python 3.13+. The `.python-version` file in the pipeline directory ensures `uv` uses the correct version.

The dependencies defined in `pyproject.toml` include:
- `click` - CLI argument parsing
- `pandas` - Data manipulation
- `sqlalchemy` - Database ORM
- `psycopg` - PostgreSQL adapter
- `pyarrow` - Parquet file support
- `tqdm` - Progress bars

---

### Data Preparation Steps:

#### Step 1: Download the Data Files

```bash
# Navigate to homework folder
cd pipeline/homework

# Download green taxi trips data for November 2025
wget https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2025-11.parquet

# Download taxi zone lookup data
wget https://github.com/DataTalksClub/nyc-tlc-data/releases/download/misc/taxi_zone_lookup.csv
```

#### Step 2: Start PostgreSQL and pgAdmin

```bash
docker compose up -d
```

#### Step 3: Load Data into PostgreSQL

Using the `insert_table.py` script to load both datasets:

```bash
# Load green taxi trips data (run from homework folder)
uv run python insert_table.py \
  --file-url green_tripdata_2025-11.parquet \
  --target-table green_taxi_trips \
  --pg-user postgres \
  --pg-password postgres \
  --pg-host localhost \
  --pg-port 5433 \
  --pg-db ny_taxi

# Load taxi zones lookup data
uv run python insert_table.py \
  --file-url taxi_zone_lookup.csv \
  --target-table zone1 \
  --pg-user postgres \
  --pg-password postgres \
  --pg-host localhost \
  --pg-port 5433 \
  --pg-db ny_taxi
```

#### Step 4: Verify Data Load

Connect to pgAdmin (`http://localhost:8080`) and verify tables exist:
- `green_taxi_trips`
- `zone1`

---

### Question 3: Counting Short Trips

**Task:** Count trips in November 2025 with trip_distance <= 1 mile.

#### SQL Query:

```sql
SELECT COUNT(*)
FROM green_taxi_trips
WHERE lpep_pickup_datetime >= '2025-11-01'
  AND lpep_pickup_datetime < '2025-12-01'
  AND trip_distance <= 1.0;
```

**Answer: `8,007`**

---

### Question 4: Longest Trip for Each Day

**Task:** Find the pickup day with the longest trip distance (excluding trips >= 100 miles).

#### SQL Query:

```sql
SELECT
    DATE(lpep_pickup_datetime) AS pickup_day,
    MAX(trip_distance) AS max_distance
FROM green_taxi_trips
WHERE trip_distance < 100
GROUP BY DATE(lpep_pickup_datetime)
ORDER BY max_distance DESC
LIMIT 1;
```

**Answer: `2025-11-14`**

---

### Question 5: Biggest Pickup Zone

**Task:** Find the pickup zone with the largest total_amount sum on November 18th, 2025.

#### SQL Query:

```sql
SELECT
    z."Zone",
    SUM(gtt.total_amount) AS total_amount_sum
FROM green_taxi_trips gtt
JOIN zone1 z
  ON gtt."PULocationID" = z."LocationID"
WHERE DATE(gtt.lpep_pickup_datetime) = '2025-11-18'
GROUP BY z."Zone"
ORDER BY total_amount_sum DESC
LIMIT 1;
```

**Answer: `East Harlem North`**

---

### Question 6: Largest Tip

**Task:** For pickups in "East Harlem North" during November 2025, find the drop-off zone with the largest tip.

#### SQL Query:

```sql
SELECT
    z_do."Zone" AS dropoff_zone
FROM green_taxi_trips gtt
JOIN zone1 z_pu
  ON gtt."PULocationID" = z_pu."LocationID"
JOIN zone1 z_do
  ON gtt."DOLocationID" = z_do."LocationID"
WHERE gtt.lpep_pickup_datetime >= '2025-11-01'
  AND gtt.lpep_pickup_datetime < '2025-12-01'
  AND z_pu."Zone" = 'East Harlem North'
ORDER BY gtt.tip_amount DESC
LIMIT 1;
```

**Answer: `Yorkville West`**

---

## Question 7: Terraform Workflow

**Task:** Identify the correct Terraform workflow sequence for:
1. Downloading provider plugins and setting up backend
2. Generating proposed changes and auto-executing the plan
3. Removing all resources managed by Terraform

### Steps to Run Terraform:

#### Prerequisites:
- Terraform installed
- GCloud token set in environment (already configured)

#### Step 1: Clone/Copy Terraform Files

Get the Terraform configuration files from:
https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/01-docker-terraform/terraform/terraform/terraform_with_variables

#### Step 2: Initialize Terraform

```bash
terraform init
```

This command:
- Downloads required provider plugins (e.g., Google Cloud provider)
- Sets up the backend for state storage
- Initializes the working directory

#### Step 3: Apply Changes with Auto-Approve

```bash
terraform apply -auto-approve
```

This command:
- Generates an execution plan
- Automatically approves and applies the changes (creates GCP Bucket and BigQuery Dataset)
- The `-auto-approve` flag skips the interactive approval prompt

#### Step 4: Destroy Resources

```bash
terraform destroy
```

This command:
- Removes all resources managed by Terraform
- Will prompt for confirmation (or use `-auto-approve` to skip)

### Workflow Summary:

| Step | Command | Purpose |
|------|---------|---------|
| 1 | `terraform init` | Download providers, setup backend |
| 2 | `terraform apply -auto-approve` | Generate plan and auto-execute |
| 3 | `terraform destroy` | Remove all managed resources |

**Answer: `terraform init, terraform apply -auto-approve, terraform destroy`**

---

## Files in This Directory

| File | Description |
|------|-------------|
| `docker-compose.yml` | Docker Compose configuration for PostgreSQL and pgAdmin |
| `green_tripdata_2025-11.parquet` | Green taxi trip data for November 2025 |
| `taxi_zone_lookup.csv` | NYC taxi zone lookup table |
| `insert_table.py` | Python script to load data into PostgreSQL |
| `insert_table.ipynb` | Jupyter notebook version of the data loading script |
| `sql.txt` | SQL queries for questions 3-6 |
| `homework.txt` | Original homework questions |

---

## Quick Reference: All Answers

| Question | Answer |
|----------|--------|
| Q1 | `25.3` |
| Q2 | `db:5432` |
| Q3 | `8,007` |
| Q4 | `2025-11-14` |
| Q5 | `East Harlem North` |
| Q6 | `Yorkville West` |
| Q7 | `terraform init, terraform apply -auto-approve, terraform destroy` |
