# easy-invoices

invoice generation program

```bash
python -m venv .venv
```

```bash
source .venv/Scripts/activate
```

```bash
pip install -r requirements.txt
```

```bash
pip install .
```

```bash
easy-invoices show-all <contact | company | options | preset>
easy-invoices show <contact | company | options | preset>
easy-invoices new <contact | company | options | preset>
easy-invoices edit <contact | company | options | preset>
easy-invoices delete <contact | company | options | preset>
```

- `new` `edit` and `show` can take an optional arg for "name"
- nunspecified fields will default to empty string.
- unspecified ids will be "default"
