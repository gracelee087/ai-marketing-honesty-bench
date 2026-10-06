"""Read Kaggle quota metadata using existing authentication; never prints credentials."""
import json

from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()
with api.build_kaggle_client() as client:
    q = client.benchmarks.benchmark_tasks_api_client.get_benchmark_task_quota()
    print(json.dumps({"daily_used_usd": q.daily_quota_used,
                      "daily_allowed_usd": q.total_daily_quota_allowed,
                      "remaining_usd": q.total_daily_quota_allowed - q.daily_quota_used}))
