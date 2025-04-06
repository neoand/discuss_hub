# Running tests

To run the tests, You can use Docker to set up an Odoo instance with the
necessary dependencies.

```bash
docker compose run --rm odoo odoo --dev=all --db-filter=^test_only\$ -d test_only --stop-after-init --test-enable --without-demo=all -i evoodoo --test-tags /evoodoo
```

# Run pre-commit locally without changing the addon README:
```bash
SKIP="oca-gen-addon-readme" pre-commit run --all-files --show-diff-on-failure --color=always
```

# Run shell to play with the code
```bash
docker compose run --rm odoo odoo shell -d odoo
```
