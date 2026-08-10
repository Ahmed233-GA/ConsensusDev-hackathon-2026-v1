export interface SamplePR {
  prNumber: number;
  repoName: string;
  branch: string;
  author: string;
  title: string;
  diffText: string;
}

export const samplePRs: SamplePR[] = [
  {
    prNumber: 142,
    repoName: 'shopflow/api',
    branch: 'feat/checkout-validation',
    author: 'm.medhat',
    title: 'Add checkout form validation helpers',
    diffText: `diff --git a/src/checkout/validators.py b/src/checkout/validators.py
new file mode 100644
--- /dev/null
+++ b/src/checkout/validators.py
@@ -0,0 +1,28 @@
+import re
+from datetime import datetime
+
+def validate_email(email: str) -> bool:
+    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$"
+    return re.match(pattern, email) is not None
+
+def validate_card_number(card: str) -> bool:
+    digits = re.sub(r"\\D", "", card)
+    if len(digits) < 13 or len(digits) > 19:
+        return False
+    total = 0
+    for i, d in enumerate(reversed(digits)):
+        n = int(d)
+        if i % 2 == 1:
+            n *= 2
+            if n > 9:
+                n -= 9
+        total += n
+    return total % 10 == 0
+
+def validate_expiry(month: int, year: int) -> bool:
+    if not (1 <= month <= 12):
+        return False
+    return datetime.now().year <= year`,
  },
  {
    prNumber: 143,
    repoName: 'shopflow/api',
    branch: 'feat/user-search-api',
    author: 'a.atia',
    title: 'Add user search endpoint with query filters',
    diffText: `diff --git a/src/api/users.py b/src/api/users.py
--- a/src/api/users.py
+++ b/src/api/users.py
@@ -12,6 +12,18 @@
 from fastapi import APIRouter, Query
+import os

 router = APIRouter()

+DB_URL = "postgres://admin:SuperSecret123@db.internal:5432/prod"
+API_KEY = "sk-live-aaX9f2K3nQ7mZ0vB4cD8eF2gH6iJ0kL"
+
 @router.get("/search")
 def search_users(q: str = Query(...)):
-    return db.execute(f"SELECT * FROM users WHERE name LIKE '%{q}%'")
+    query = f"SELECT * FROM users WHERE name LIKE '%{q}%'"
+    return db.execute(query)`,
  },
  {
    prNumber: 144,
    repoName: 'shopflow/web',
    branch: 'perf/lazy-product-images',
    author: 'soliman',
    title: 'Lazy-load product images and memoize price filter',
    diffText: `diff --git a/src/components/ProductGrid.tsx b/src/components/ProductGrid.tsx
--- a/src/components/ProductGrid.tsx
+++ b/src/components/ProductGrid.tsx
@@ -5,8 +5,16 @@
 import { useMemo } from "react";
+import { lazy, Suspense } from "react";

-const ProductCard = require("../ProductCard").default;
+const ProductCard = lazy(() => import("../ProductCard"));

 export function ProductGrid({ products, maxPrice }) {
-  const filtered = products.filter(p => p.price <= maxPrice);
+  const filtered = useMemo(
+    () => products.filter(p => p.price <= maxPrice),
+    [products, maxPrice]
+  );
   return (
     <div className="grid">
-      {filtered.map(p => <ProductCard key={p.id} product={p} />)}
+      {filtered.map(p => (
+        <Suspense key={p.id} fallback={<Skeleton />}>
+          <ProductCard product={p} />
+        </Suspense>
+      ))}`,
  },
];
