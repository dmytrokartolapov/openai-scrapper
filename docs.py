import json
import os

import yaml

from src.main import app


def main() -> None:
    docs = app.openapi()
    DOCS_PATH = "docs"
    os.makedirs(DOCS_PATH, exist_ok=True)
    json_path = os.path.join(DOCS_PATH, "docs.json")
    yaml_path = os.path.join(DOCS_PATH, "docs.yaml")

    # Write JSON
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(docs, file, indent=2)

    # Write YAML
    with open(yaml_path, "w", encoding="utf-8") as file:
        yaml.dump(docs, file, sort_keys=False, allow_unicode=True)


if __name__ == "__main__":
    main()
