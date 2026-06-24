# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability within this project, please send an email to the maintainers. All security vulnerabilities will be promptly addressed.

## XSS Prevention

This repository follows best practices to prevent Cross-Site Scripting (XSS) attacks:

- Never render raw HTML or JavaScript from user input
- Always sanitize and escape user-provided content before displaying
- Use Content Security Policy (CSP) headers when serving web content
- Validate and sanitize all input data on the server side

## Input Validation

All user inputs should be:
- Validated against expected formats
- Sanitized to remove or escape potentially dangerous characters
- Stored using parameterized queries to prevent injection attacks

## Responsible Disclosure

We kindly ask that you:
- Report vulnerabilities privately before making them public
- Allow reasonable time for a fix to be implemented
- Avoid exploiting the vulnerability beyond what is necessary to demonstrate it
