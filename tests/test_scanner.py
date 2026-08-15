"""Unit and integration tests for the ConsensusDev Security Scanner."""

import unittest
import asyncio
from scanners.app import root, health, scan_diff
from scanners.schemas import ScanRequest
from scanners.checkov_runner import run_security_scan


class TestScannerService(unittest.TestCase):
    """Test suite for security scanner FastAPI endpoints and rule engine."""

    def test_root_endpoint(self):
        """Verify root endpoint status and port info."""
        data = asyncio.run(root())
        self.assertEqual(data["service"], "ConsensusDev Security Scanner")
        self.assertEqual(data["port"], 8002)
        self.assertEqual(data["status"], "running")

    def test_health_endpoint(self):
        """Verify health check endpoint returns healthy."""
        data = asyncio.run(health())
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["port"], 8002)

    def test_safe_diff_scan(self):
        """Verify safe diff passes with zero vulnerabilities."""
        safe_diff = """diff --git a/calculator.py b/calculator.py
index e69de29..b1b2c3d 100644
--- a/calculator.py
+++ b/calculator.py
@@ -1,3 +1,6 @@
+def add(a: int, b: int) -> int:
+    return a + b
+
+def multiply(a: int, b: int) -> int:
+    return a * b
"""
        req = ScanRequest(diff=safe_diff)
        data = asyncio.run(scan_diff(req))
        self.assertEqual(data.status, "PASS")
        self.assertEqual(data.vulnerabilities, 0)
        self.assertEqual(data.vulnerabilities_count, 0)
        self.assertEqual(len(data.critical_issues), 0)
        self.assertEqual(len(data.findings), 0)

    def test_vulnerable_diff_hardcoded_aws_key(self):
        """Verify scanner flags hardcoded AWS credentials."""
        vuln_diff = """diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,2 +1,3 @@
+AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'
+AWS_REGION = 'us-east-1'
"""
        req = ScanRequest(diff=vuln_diff)
        data = asyncio.run(scan_diff(req))
        self.assertEqual(data.status, "FAIL")
        self.assertGreaterEqual(data.vulnerabilities, 1)
        self.assertTrue(any("Hardcoded AWS Access Key" in issue for issue in data.critical_issues))
        self.assertEqual(data.findings[0].rule_id, "SEC-001")
        self.assertEqual(data.findings[0].severity, "CRITICAL")

    def test_vulnerable_diff_sql_injection(self):
        """Verify scanner flags SQL injection vulnerabilities."""
        vuln_diff = """diff --git a/db.py b/db.py
--- a/db.py
+++ b/db.py
@@ -10,3 +10,4 @@
 def get_user(user_id):
+    query = f"SELECT * FROM users WHERE id = '{user_id}'"
+    return db.execute(query)
"""
        req = ScanRequest(diff=vuln_diff)
        data = asyncio.run(scan_diff(req))
        self.assertEqual(data.status, "FAIL")
        self.assertTrue(any("SQL Injection" in issue for issue in data.critical_issues))

    def test_vulnerable_diff_iac_public_s3(self):
        """Verify scanner flags public S3 bucket IaC misconfigurations."""
        vuln_diff = """diff --git a/main.tf b/main.tf
--- a/main.tf
+++ b/main.tf
@@ -1,4 +1,5 @@
 resource "aws_s3_bucket" "b" {
   bucket = "my-public-bucket"
+  acl    = "public-read"
 }
"""
        req = ScanRequest(diff=vuln_diff)
        data = asyncio.run(scan_diff(req))
        self.assertEqual(data.status, "FAIL")
        self.assertTrue(any("Public S3 Bucket ACL" in issue for issue in data.critical_issues))

    def test_vulnerable_diff_trivy_dependency(self):
        """Verify Trivy vulnerability scanner flags known vulnerable dependencies."""
        vuln_diff = """diff --git a/requirements.txt b/requirements.txt
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,2 +1,3 @@
+requests==2.20.0
"""
        req = ScanRequest(diff=vuln_diff)
        data = asyncio.run(scan_diff(req))
        self.assertEqual(data.status, "FAIL")
        self.assertTrue(any("CVE-2023-32681" in issue or "requests" in issue for issue in data.critical_issues))

    def test_direct_runner_execution(self):

        """Verify direct Python runner invocation."""
        vuln_diff = """diff --git a/utils.py b/utils.py
--- a/utils.py
+++ b/utils.py
@@ -1,2 +1,3 @@
+os.system("rm -rf " + target_dir)
"""
        result = run_security_scan(vuln_diff)
        self.assertEqual(result.status, "FAIL")
        self.assertGreaterEqual(result.vulnerabilities, 1)
        self.assertEqual(result.findings[0].rule_id, "SEC-006")


if __name__ == "__main__":
    unittest.main()
