import pandas as pd

from src.preprocessing import load_and_clean_dataset, make_unseen_domain_split


def test_cleaning_removes_invalid_and_duplicate_urls(tmp_path):
    path = tmp_path / "sample.csv"
    pd.DataFrame(
        {
            "url": ["https://safe.example/a", "https://safe.example/a", "not a url", "http://bad.example/login"],
            "label": ["legitimate", "legitimate", "phishing", "phishing"],
        }
    ).to_csv(path, index=False)
    frame, report = load_and_clean_dataset(path)
    assert len(frame) == 2
    assert report.removed_duplicate_urls == 1
    assert report.removed_invalid_url == 1


def test_unseen_domain_split_has_no_shared_domains():
    rows = []
    for index in range(10):
        for label, path in [(0, "safe"), (1, "login")]:
            rows.append({"url": f"http://domain{index}.example/{path}", "target": label, "url_key": f"{index}-{label}", "domain": f"domain{index}.example"})
    frame = pd.DataFrame(rows)
    train, test = make_unseen_domain_split(frame, n_splits=2)
    assert not (set(train["domain"]) & set(test["domain"]))
