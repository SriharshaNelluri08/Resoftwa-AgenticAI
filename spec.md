# Feature Spec: Goods Receipt Action

## 1. Summary

Add a bound OData V4 action on `PurchaseOrders` that records goods received against a purchase order. The action increments `deliveredQty` and rejects any receipt that would make `deliveredQty` exceed `orderedQty`.

Today, `deliveredQty` can only be changed by directly updating the PO row, and no rule guards that change. This feature gives receiving a single, validated entry point.

## 2. Goals

- Provide one supported way to record a goods receipt.
- Prevent `deliveredQty` from exceeding `orderedQty`.
- Prevent receipts of zero or negative quantities.
- Return the updated PO, including the computed `isLate` value, so callers do not need a second read.

## 3. Non-goals

- Partial-receipt tracking per delivery note (no receipt history entity).
- Goods receipt reversal or correction.
- Inventory or stock updates.
- UI (`app/` is still empty).
- Changing the `amount` validation (see section 9).

## 4. API

### 4.1 Action definition

| Item | Value |
|---|---|
| Name | `receiveGoods` |
| Binding | Bound to `PurchaseOrders` (instance-level) |
| Path | `POST /odata/v4/po/PurchaseOrders('{poNumber}')/POService.receiveGoods` |
| Parameter | `quantity : Integer` (required) |
| Returns | `PurchaseOrders` (the updated entity) |

### 4.2 Example request

```http
POST http://localhost:4004/odata/v4/po/PurchaseOrders('4500014')/POService.receiveGoods
Content-Type: application/json

{ "quantity": 20 }
```

### 4.3 Example response (200 OK)

```json
{
  "poNumber": "4500014",
  "vendor_ID": "V003",
  "dueDate": "2026-10-05",
  "orderedQty": 50,
  "deliveredQty": 20,
  "amount": "275000.00",
  "isLate": true
}
```

## 5. Business rules

| # | Rule | Result if violated |
|---|---|---|
| R1 | `quantity` must be an integer greater than 0 | 400, `Quantity must be greater than 0` |
| R2 | `deliveredQty + quantity` must be less than or equal to `orderedQty` | 400, `Received quantity exceeds ordered quantity` |
| R3 | The PO must exist | 404 (standard CAP behavior) |

R2 is evaluated against the stored `deliveredQty` at the time of the call. The check and the update must run in the same transaction so two concurrent receipts cannot both pass R2.

## 6. Implementation plan

### 6.1 `srv/po-service.cds`

Declare the action on the projection:

```cds
entity PurchaseOrders as projection on po.PurchaseOrders actions {
  action receiveGoods(quantity: Integer) returns PurchaseOrders;
};
```

### 6.2 `srv/po-service.js`

Add a handler next to the existing rules:

```js
this.on('receiveGoods', PurchaseOrders, async (req) => {
  const { quantity } = req.data;
  if (!(Number.isInteger(quantity) && quantity > 0)) {
    return req.reject(400, 'Quantity must be greater than 0');
  }

  const { poNumber } = req.params[0];
  const tx = cds.tx(req);
  const po = await tx.read(PurchaseOrders, poNumber);
  if (!po) return req.reject(404, 'Purchase order not found');

  if (po.deliveredQty + quantity > po.orderedQty) {
    return req.reject(400, 'Received quantity exceeds ordered quantity');
  }

  await tx.update(PurchaseOrders, poNumber).with({
    deliveredQty: po.deliveredQty + quantity
  });

  return tx.read(PurchaseOrders, poNumber);
});
```

Notes for the implementer:

- Returning `tx.read(...)` runs the existing `after READ` handler, so `isLate` is computed in the response. Verify this during testing.
- Confirm that the `req.params[0]` shape matches the bound-action key in your CAP version.
- If `deliveredQty` is null in the data, treat it as 0.

### 6.3 Other files

- `test/po.http`: add a sample request for the action (see 4.2).
- `db/`: no schema change is needed. No CSV changes are needed.

## 7. Test cases

| # | Scenario | Setup | Expected |
|---|---|---|---|
| T1 | Valid partial receipt | PO 4500014 (ordered 50, delivered 0), quantity 20 | 200, deliveredQty = 20 |
| T2 | Receipt that fills the order | PO 4500012 (ordered 100, delivered 60), quantity 40 | 200, deliveredQty = 100, isLate = false |
| T3 | Over-receipt | PO 4500012, quantity 41 | 400, deliveredQty unchanged |
| T4 | Zero quantity | any PO, quantity 0 | 400 |
| T5 | Negative quantity | any PO, quantity -5 | 400 |
| T6 | Non-integer quantity | quantity 1.5 | 400 |
| T7 | Unknown PO | poNumber 9999999 | 404 |
| T8 | Sequential receipts | two receipts that together exceed orderedQty | second one returns 400 |

Test files do not exist yet (`test/` has no tests). Add them under `test/` and run with `node --test test/<file>.js`.

## 8. Data notes

- Seed data is in-memory SQLite. Receipts are lost when the server restarts, and every restart re-seeds from `db/data/`.
- Seed PO 4500012 (ordered 100, delivered 60) and PO 4500014 (ordered 50, delivered 0) are good candidates for manual testing.

## 9. Open questions and related work

- **UPDATE validation gap.** The `amount <= 0` check runs only on CREATE. This is outside this feature, but it is the same kind of gap. Decide whether to extend it to UPDATE in a separate change.
- **Direct edits to `deliveredQty`.** Should direct PATCH on `deliveredQty` be blocked (for example, with `@readonly`) so that this action is the only way to change it? This is a policy decision and is not included in this spec.
- **Locking.** The plan uses a read-check-update sequence inside one transaction. Under SQLite this is adequate for the current scale. Confirm the approach if the service moves to a multi-instance database.
- **Return on error.** Confirm the exact error response format CAP produces for `req.reject` so the tests match it.
