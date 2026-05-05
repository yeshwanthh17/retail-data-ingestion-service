# Written Approach

## High-level approach
I built this as a Django application using Django ORM models that mirror the assignment schema. The API exposes three upload endpoints for stores, users, and store-user mappings. Each upload is processed through a service layer so validation, normalization, lookup resolution, and persistence stay separate from the HTTP view functions.

## Validation strategy
Validation happens row by row before insertion. Each invalid row returns a structured error with row number, column name, reason, and invalid value. I validate required fields, max lengths, numeric parsing, boolean parsing, email format, phone format, allowed `user_type` values, duplicate unique keys, and foreign-key references for store-user mappings.

For lookup values such as `store_brand`, `store_type`, `city`, `state`, `country`, and `region`, I normalize input by trimming whitespace, collapsing repeated spaces, and using case-insensitive matching before create-or-reuse. Lookup rows are created only after the parent row passes validation so invalid rows do not pollute lookup tables.

## Failure policy
I chose partial ingestion: invalid rows are skipped, valid rows are ingested, and the response contains a detailed error report. This is more practical for operational bulk uploads because one bad row should not block the rest of a large file. It also keeps data-quality problems explicit instead of silent.

## 500K-row strategy
The large store file is handled with a streaming CSV reader and bulk inserts in batches of 1000 rows. This avoids loading the full file into memory during API processing and avoids row-by-row ORM saves. Lookup values are cached in memory to reduce repeated database hits. Users and mappings are smaller in this assignment, so they are validated with more cross-row checks in memory before bulk persistence.

## Tradeoffs considered
Rejecting the entire file would make transactional behavior simpler, but it would reduce practical usability for large uploads. Row-by-row insertion would make failure isolation easy, but it would be too slow for the 500K dataset. I chose batched Django ORM bulk inserts with pre-validation because it balances performance and precise row-level error reporting. For users, I added a second validation pass for supervisor references so an invalid supervisor row cannot silently degrade dependent users.
