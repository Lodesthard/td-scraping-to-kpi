import json, os, re, time
from collections import Counter

# One deliberately simple, deliberately editable KPI definition -- change
# TARGET_SKILL, or write a different KPI function entirely. Per this course's
# standing principle: a KPI is a construct you chose, not a neutral fact.
TARGET_SKILL = "AI"

# Second, structurally different KPI: share of *distinct* postings asking for at
# least one public cloud provider. Each provider is a closed list of aliases
# (provider names + unambiguous flagship services), matched as whole words --
# unlike the substring test above, "ai" in "Maintenance" cannot happen here.
# Deliberately left out: generic names ("Glue", "Lambda", "Athena") that only
# mean AWS in context, and "Intune"/"Endpoint Manager", which are Microsoft
# products but not Azure cloud skills.
CLOUD_PROVIDERS = {
    "AWS": ["aws", "amazon web services", "s3", "ec2", "sagemaker", "redshift", "cloudwatch"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud", "bigquery"],
}

def load_extracted(path="data/extracted.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["postings"]

def compute_kpi(postings, target_skill=TARGET_SKILL):
    n = len(postings)
    matching = [
        p for p in postings
        if any(target_skill.lower() in s.lower() for s in p.get("required_skills", []))
    ]
    all_skills = Counter()
    for p in postings:
        for s in p.get("required_skills", []):
            all_skills[s] += 1

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kpi_label": f"% of postings mentioning '{target_skill}'",
        "kpi_value": round(len(matching) / n, 3) if n else 0.0,
        "n_postings_analyzed": n,
        "n_matching": len(matching),
        "top_skills": [{"skill": s, "count": c} for s, c in all_skills.most_common(10)],
        "avg_skills_per_posting": round(sum(len(p.get("required_skills", [])) for p in postings) / n, 2) if n else 0.0,
    }

def _mentions(skill, alias):
    return re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", skill.lower()) is not None

def compute_cloud_kpi(postings, providers=CLOUD_PROVIDERS):
    # Same title = same ad republished under another company name (the
    # CarCutter/Diffusely case): keep the first one only.
    seen, distinct = set(), []
    for p in postings:
        key = p["title"].strip().lower()
        if key not in seen:
            seen.add(key)
            distinct.append(p)

    n = len(distinct)
    by_provider = Counter()
    n_matching = 0
    for p in distinct:
        found = {
            name for name, aliases in providers.items()
            for s in p.get("required_skills", []) for a in aliases if _mentions(s, a)
        }
        by_provider.update(found)
        n_matching += bool(found)

    return {
        "kpi_label": "% of distinct postings requiring at least one cloud provider (AWS, Azure, GCP)",
        "kpi_value": round(n_matching / n, 3) if n else 0.0,
        "n_postings_distinct": n,
        "n_duplicates_removed": len(postings) - n,
        "n_matching": n_matching,
        "by_provider": [{"provider": name, "count": by_provider[name]} for name in providers],
    }

def main():
    # Run from the project root whatever the launch directory, so the relative
    # data/ and docs/ paths below always resolve.
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    os.makedirs("docs/data", exist_ok=True)
    postings = load_extracted()
    kpi = compute_kpi(postings)
    kpi["cloud_kpi"] = compute_cloud_kpi(postings)
    print(json.dumps(kpi, indent=2))
    with open("docs/data/kpi.json", "w", encoding="utf-8") as f:
        json.dump(kpi, f, indent=2, ensure_ascii=False)
    print("\nWrote docs/data/kpi.json")

if __name__ == "__main__":
    main()
