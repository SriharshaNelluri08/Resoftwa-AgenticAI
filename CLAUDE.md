# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Install: `npm install`
- Run the service: `cds watch` (VS Code task "cds watch" in `.vscode/tasks.json`). The `cds` CLI is not in `node_modules/.bin`; it comes from a global install. Without it, run `node node_modules/@sap/cds/bin/serve.js`. Both serve on port 4004.
- Tests: `npm test` runs `node --test`, but there are no test files yet, so it reports 0 tests. To run a single test file once one exists: `node --test test/<file>.js`.
- Manual API checks: `test/po.http` (VS Code REST Client, or copy the URLs into curl). It assumes the service is running on port 4004.

## Architecture

This is a SAP CAP (Node.js) project exposing purchase-order data as OData V4.

- **Data model** (`db/schema.cds`, namespace `resoftwa.po`): `Vendors` (ID, name, rating) and `PurchaseOrders` (poNumber, dueDate, orderedQty, deliveredQty, amount). `PurchaseOrders.vendor` is an association, so the stored foreign key column is `vendor_ID`.
- **Seed data** (`db/data/`): CSVs named `<namespace>-<Entity>.csv` are loaded automatically by CAP. They use semicolon delimiters. The database is in-memory SQLite, so every server start re-seeds from these files and any POSTed data is lost on restart.
- **Service** (`srv/po-service.cds`): `POService` is served at `/odata/v4/po` and projects the two entities. Only these two are exposed.
- **Business logic** (`srv/po-service.js`): this file holds all custom behavior.
  - `before CREATE`: rejects `amount <= 0` with HTTP 400. This check does not run on UPDATE.
  - `after READ`: computes the virtual field `isLate` (true when `dueDate` is before today and `deliveredQty < orderedQty`). `isLate` is not stored, so it cannot be used in `$filter`. Filter on `dueDate` and `deliveredQty` instead, as `test/po.http` does. "Today" is the server's clock, and the comparison is a string comparison on `YYYY-MM-DD` dates.
- **`app/`** is empty. There is no UI yet.

When changing a field in `db/schema.cds`, update the matching CSV headers in `db/data/` as well so the seed data stays in line with the model.
