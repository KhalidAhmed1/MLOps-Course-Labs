"""Locust load testing script for Bank Churn Prediction API."""

from locust import HttpUser, task, between
import random


class ChurnAPIUser(HttpUser):
    """Simulated user for load testing the churn prediction API."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Called when a simulated user starts."""
        # Test the home endpoint first
        self.client.get("/")

    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health")

    @task(3)
    def predict_churn(self):
        """Make a churn prediction request."""
        payload = {
            "CreditScore": random.randint(300, 900),
            "Geography": random.choice(["France", "Spain", "Germany"]),
            "Gender": random.choice(["Male", "Female"]),
            "Age": random.randint(18, 100),
            "Tenure": random.randint(0, 10),
            "Balance": round(random.uniform(0, 250000), 2),
            "NumOfProducts": random.randint(1, 4),
            "HasCrCard": random.randint(0, 1),
            "IsActiveMember": random.randint(0, 1),
            "EstimatedSalary": round(random.uniform(10000, 200000), 2),
        }
        self.client.post("/predict", json=payload)
