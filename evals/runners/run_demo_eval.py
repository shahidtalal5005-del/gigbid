import json
import os
import sys
from pathlib import Path
import pandas as pd

# Ensure project root is in python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from agent.nodes.scout import scout_node
from agent.nodes.analyst import analyst_node
from agent.nodes.risk_assessor import risk_assessor_node
from agent.nodes.fit_matcher import fit_matcher_node
from agent.nodes.pricing import pricing_node
from agent.nodes.writer import writer_node
from agent.nodes.critic import critic_node
from agent.nodes.compliance import compliance_node
from agent.nodes.client_liaison import client_liaison_node

def load_real_jobs(csv_path, num_samples=5):
    """Loads and preprocesses real jobs from the Kaggle CSV."""
    if not os.path.exists(csv_path):
        print(f"⚠️ Dataset not found at {csv_path}. Falling back to synthetic data.")
        return []

    print(f"📊 Loading real dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Preprocessing: Drop rows missing critical information
    df = df.dropna(subset=['title', 'description'])
    
    # Sample a small subset so the evaluation doesn't take hours
    sample_df = df.head(num_samples)
    
    test_jobs = []
    for idx, row in sample_df.iterrows():
        # Handle variations in Kaggle column names gracefully
        skills_raw = str(row.get('skills', ''))
        skills_list = [s.strip() for s in skills_raw.split(',')] if skills_raw != 'nan' else []
        
        test_jobs.append({
            "id": f"real_job_{idx}",
            "title": str(row['title']),
            "description": str(row['description']),
            "skills": skills_list,
            "budget": {
                "min": float(row.get('hourly_low', 10)), 
                "max": float(row.get('hourly_high', row.get('budget', 100)))
            }
        })
    return test_jobs

def run_evaluation():
    print("🚀 Starting GigBid Multi-Agent Evaluation Run...")

    # Try to load real data first
    data_path = project_root / "data" / "upwork_jobs.csv"
    test_jobs = load_real_jobs(data_path, num_samples=5)

    # Fallback to synthetic if CSV isn't placed correctly yet
    if not test_jobs:
        print("Using synthetic generated data for evaluation baseline.")
        test_jobs = [
            {
                "id": "synthetic_eval_01",
                "title": "Python & scikit-learn Machine Learning Classifier",
                "description": "Need an expert to build customer churn classification models using Python and scikit-learn.",
                "skills": ["Python", "scikit-learn"],
                "budget": {"min": 500, "max": 1000}
            }
        ]

    results = []

    for job in test_jobs:
        print(f"\n--- Evaluating Job: {job['id']} ---")
        state = {"job": job}

        # Run full pipeline graph sequence
        state = scout_node(state)
        state = analyst_node(state)
        state = risk_assessor_node(state)
        state = fit_matcher_node(state)
        state = pricing_node(state)
        state = writer_node(state)
        state = critic_node(state)
        state = compliance_node(state)
        state = client_liaison_node(state)

        result_summary = {
            "job_id": job["id"],
            "title": job["title"],
            "decision": state.get("decision"),
            "risk_score": state.get("risk_report", {}).get("score"),
            "fit_score": state.get("fit_report", {}).get("score"),
            "approval_status": state.get("approval_status"),
            "errors": state.get("errors", [])
        }
        results.append(result_summary)

    # Ensure results directory exists
    results_dir = project_root / "evals" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_path = results_dir / "evaluation_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Evaluation completed successfully! Saved report to {output_path}")

if __name__ == "__main__":
    run_evaluation()