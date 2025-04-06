# Running tests

To run the tests, You can use Docker to set up an Odoo instance with the necessary dependencies.

docker compose run --rm odoo \
  odoo \
    --dev=all \
    --db-filter=^test_only$ \
    -d test_only \
    --stop-after-init \
    --test-enable \
    --without-demo=all \
    -i evoodoo \
    --test-tags /evoodoo