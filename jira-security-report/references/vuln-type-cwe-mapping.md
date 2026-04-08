# 漏洞类型与 CWE 对照表 — ZOOM Security Two Level Mapping

> 生成 Jira 安全报告时，根据漏洞现象从下表选取**一级分类**与**二级分类**（表中「二级 CWE」列），填入报告的「漏洞类型」项。优先选用与漏洞最贴合的二级分类；若无直接对应可选用该一级下的 Generic 或最接近项。

---

## 1. Buffer Overflow/Operation Errors (CWE-119)

| 二级 CWE | 说明 |
|----------|------|
| CWE-119 | Lack of Binary Hardening / Memory Corruption - Generic |
| CWE-120 | Classic Buffer Overflow |
| CWE-121 | Stack Overflow |
| CWE-122 | Heap Overflow |
| CWE-123 | Write-what-where Condition |
| CWE-124 | Buffer Underflow |
| CWE-125 | Out-of-bounds Read |
| CWE-126 | Buffer Over-read |
| CWE-127 | Buffer Under-read |
| CWE-128 | Wrap-around Error |
| CWE-129 | Array Index Underflow |
| CWE-131 | Incorrect Calculation of Buffer Size |
| CWE-170 | Improper Null Termination |
| CWE-190 | Integer Overflow |
| CWE-191 | Integer Underflow |
| CWE-193 | Off-by-one Error |
| CWE-415 | Double Free |
| CWE-416 | Use After Free |
| CWE-476 | NULL Pointer Dereference |

---

## 2. Business Logic Error (CWE-840)

| 二级 CWE | 说明 |
|----------|------|
| CWE-451 | User Interface (UI) Misrepresentation of Critical Information |
| CWE-656 | Security Through Obscurity |
| CWE-657 | Violation of Secure Design Principles |
| CWE-840 | Business Logic Error |

---

## 3. Client Enforcement of Server Security (CWE-602)

| 二级 CWE | 说明 |
|----------|------|
| CWE-602 | Client Enforcement of Server Security |
| CWE-784 | Reliance on Cookies without Validation and Integrity Checking in a Security Decision |

---

## 4. Cross-Site Request Forgery (CWE-352)

| 二级 CWE | 说明 |
|----------|------|
| CWE-352 | Cross-Site Request Forgery (CSRF) |

---

## 5. Crypto Usage Errors (CWE-310)

| 二级 CWE | 说明 |
|----------|------|
| CWE-261 | Weak Cryptography for Passwords |
| CWE-295 | Improper Certificate Validation |
| CWE-296 | Improper Following of a Certificate's Chain of Trust |
| CWE-310 | Cryptographic Issues - Generic |
| CWE-322 | Key Exchange without Entity Authentication |
| CWE-323 | Reusing a Nonce & Key Pair in Encryption |
| CWE-324 | Use of a Key Past its Expiration Date |
| CWE-325 | Missing Required Cryptographic Step |
| CWE-326 | Inadequate Encryption Strength |
| CWE-327 | Use of a Broken or Risky Cryptographic Algorithm |
| CWE-328 | Reversible One-Way Hash |
| CWE-330 | Use of Insufficiently Random Values |
| CWE-338 | Use of Cryptographically Weak Pseudo-Random Number Generator (PRNG) |

---

## 6. Externally Controlled Resources (CWE-610)

| 二级 CWE | 说明 |
|----------|------|
| CWE-134 | Use of Externally-Controlled Format String |
| CWE-350 | Reliance on Reverse DNS Resolution for a Security-Critical Action |
| CWE-426 | Untrusted Search Path |
| CWE-601 | Open Redirect |
| CWE-610 | Externally Controlled Reference to a Resource in Another Sphere |
| CWE-611 | XML External Entities (XXE) |
| CWE-642 | External Control of Critical State Data |
| CWE-98 | Remote File Inclusion |

---

## 7. Improper Access Control (CWE-284)

| 二级 CWE | 说明 |
|----------|------|
| CWE-1021 | Improper Restriction of Rendered UI Layers or Frames |
| CWE-250 | Execution with Unnecessary Privileges |
| CWE-266 | Incorrect Privilege Assignment |
| CWE-269 | Improper Privilege Management |
| CWE-272 | Least Privilege Violation |
| CWE-280 | Improper Handling of Insufficient Permissions or Privileges |
| CWE-284 | Improper Access Control - Generic |
| CWE-285 | Improper Authorization |
| CWE-300 | Man-in-the-Middle |
| CWE-377 | Insecure Temporary File |
| CWE-384 | Session Fixation |
| CWE-471 | Modification of Assumed-Immutable Data (MAID) |
| CWE-489 | Leftover Debug Code (Backdoor) |
| CWE-613 | Insufficient Session Expiration |
| CWE-639 | Insecure Direct Object Reference (IDOR) |
| CWE-732 | Incorrect Permission Assignment for Critical Resource |
| CWE-862 | Missing Authorization |
| CWE-863 | Incorrect Authorization |
| CWE-926 | Improper Export of Android Application Components |
| CWE-941 | Incorrectly Specified Destination in a Communication Channel |

---

## 8. Improper Authentication (CWE-287)

| 二级 CWE | 说明 |
|----------|------|
| CWE-256 | Plaintext Storage of a Password |
| CWE-257 | Storing Passwords in a Recoverable Format |
| CWE-259 | Use of Hard-coded Password |
| CWE-260 | Password in Configuration File |
| CWE-287 | Improper Authentication - Generic |
| CWE-288 | Authentication Bypass Using an Alternate Path or Channel |
| CWE-304 | Missing Critical Step in Authentication |
| CWE-306 | Missing Authentication for Critical Function |
| CWE-307 | Brute Force |
| CWE-321 | Use of Hard-coded Cryptographic Key |
| CWE-345 | Insufficient Verification of Data Authenticity |
| CWE-347 | Improper Verification of Cryptographic Signature |
| CWE-360 | Trust of System Event Data |
| CWE-425 | Forced Browsing |
| CWE-522 | Insufficiently Protected Credentials |
| CWE-523 | Unprotected Transport of Credentials |
| CWE-620 | Unverified Password Change |
| CWE-640 | Weak Password Recovery Mechanism for Forgotten Password |
| CWE-798 | Use of Hard-coded Credentials |

---

## 9. Improper Exceptional Condition Handling (CWE-703)

| 二级 CWE | 说明 |
|----------|------|
| CWE-391 | Unchecked Error Condition |
| CWE-674 | Uncontrolled Recursion |
| CWE-703 | Improper Check or Handling of Exceptional Conditions |

---

## 10. Improper Input Validation (CWE-20)

| 二级 CWE | 说明 |
|----------|------|
| CWE-113 | HTTP Response Splitting |
| CWE-1286 | Improper Validation of Syntactic Correctness of Input |
| CWE-184 | Incomplete Blacklist |
| CWE-20 | Improper Input Validation |
| CWE-409 | Improper Handling of Highly Compressed Data (Data Amplification) |
| CWE-444 | HTTP Request Smuggling |
| CWE-502 | Deserialization of Untrusted Data |
| CWE-73 | External Control of File Name or Path |
| CWE-807 | Reliance on Untrusted Inputs in a Security Decision |
| CWE-1284 | Improper Validation of Specified Quantity in Input |

---

## 11. Injection (CWE-74)

| 二级 CWE | 说明 |
|----------|------|
| CWE-138 | Improper Neutralization of Special Elements |
| CWE-150 | Improper Neutralization of Escape, Meta, or Control Sequences |
| CWE-177 | Improper Handling of URL Encoding (Hex Encoding) |
| CWE-644 | Improper Neutralization of HTTP Headers for Scripting Syntax |
| CWE-646 | Reliance on File Name or Extension of Externally-Supplied File |
| CWE-75 | Failure to Sanitize Special Elements (Special Element Injection) |
| CWE-77 | Command Injection - Generic |
| CWE-78 | OS Command Injection |
| CWE-79 | Cross-site Scripting (XSS) - DOM / Generic / Reflected / Stored |
| CWE-80 | Improper Neutralization of Script-Related HTML Tags (Basic XSS) |
| CWE-89 | SQL Injection |
| CWE-90 | LDAP Injection |
| CWE-91 | XML Injection |
| CWE-93 | CRLF Injection |
| CWE-94 | Code Injection |
| CWE-99 | Resource Injection |

---

## 12. Misconfiguration (CWE-16)

| 二级 CWE | 说明 |
|----------|------|
| CWE-16 | Misconfiguration |

---

## 13. Use of Incorrectly-Resolved Name or Reference (CWE-706) — Path Traversal

| 二级 CWE | 说明 |
|----------|------|
| CWE-22 | Path Traversal |
| CWE-23 | Relative Path Traversal |
| CWE-35 | Path Traversal: '.../...//' |

---

## 14. Race Condition (CWE-362)

| 二级 CWE | 说明 |
|----------|------|
| CWE-362 | Concurrent Execution using Shared Resource with Improper Synchronization (Race Condition) |
| CWE-367 | Time-of-check Time-of-use (TOCTOU) Race Condition |

---

## 15. Sensitive Information Exposure (CWE-200)

| 二级 CWE | 说明 |
|----------|------|
| CWE-200 | Information Disclosure |
| CWE-201 | Information Exposure Through Sent Data |
| CWE-203 | Information Exposure Through Discrepancy |
| CWE-208 | Information Exposure Through Timing Discrepancy |
| CWE-209 | Information Exposure Through an Error Message |
| CWE-215 | Information Exposure Through Debug Information |
| CWE-359 | Privacy Violation |
| CWE-538 | File and Directory Information Exposure |
| CWE-548 | Information Exposure Through Directory Listing |
| CWE-598 | Sensitive Data in Query Strings |

---

## 16. Server-Side Request Forgery (CWE-918)

| 二级 CWE | 说明 |
|----------|------|
| CWE-918 | Server-Side Request Forgery (SSRF) |

---

## 17. Uncontrolled Resource Consumption (CWE-400)

| 二级 CWE | 说明 |
|----------|------|
| CWE-400 | Denial of Service |
| CWE-770 | Allocation of Resources Without Limits or Throttling |
| CWE-776 | XML Entity Expansion |
| CWE-799 | Improper Control of Interaction Frequency |

---

## 18. Unencrypted Sensitive Data (CWE-311)

| 二级 CWE | 说明 |
|----------|------|
| CWE-311 | Missing Encryption of Sensitive Data |
| CWE-312 | Cleartext Storage of Sensitive Information |
| CWE-319 | Cleartext Transmission of Sensitive Information |
| CWE-922 | Insecure Storage of Sensitive Information |

---

## 19. Use of Dangerous Function (CWE-242)

| 二级 CWE | 说明 |
|----------|------|
| CWE-242 | Use of Inherently Dangerous Function |

---

## 20. Vulnerable and Outdated Components (CWE-1035)

| 二级 CWE | 说明 |
|----------|------|
| CWE-1035 | Using Components with Known Vulnerabilities |

---

## 21. Incorrect Resource Transfer Between Spheres (CWE-669)

| 二级 CWE | 说明 |
|----------|------|
| CWE-434 | Unrestricted Upload of File with Dangerous Type |
| CWE-494 | Download of Code Without Integrity Check |
| CWE-829 | Inclusion of Functionality from Untrusted Control Sphere |

---

## 22. Misc. CWE

| 二级 CWE | 说明 |
|----------|------|
| CWE-252 | Unchecked Return Value |
| CWE-357 | Insufficient UI Warning of Dangerous Operations |
| CWE-449 | The UI Performs the Wrong Action |
| CWE-506 | Embedded Malicious Code |
| CWE-509 | Replicating Malicious Code (Virus or Worm) |
| CWE-697 | Incorrect Comparison |
| CWE-749 | Exposed Dangerous Method or Function |
| CWE-843 | Type Confusion |

---

## 23. UI Misrepresentation (CWE-451)

| 二级 CWE | 说明 |
|----------|------|
| CWE-1021 | Improper Restriction of Rendered UI Layers or Frames (Clickjacking) |

---

**使用说明**：报告中「漏洞类型」填写格式建议为：`一级分类 / 二级分类 (CWE-XXX)`（CWE 与表中所选二级行一致），例如 `Injection / SQL Injection (CWE-89)`、`Improper Authentication / Missing Authentication for Critical Function (CWE-306)`。
