# Payment Test Suite - Jenkins Setup Guide

## Project Structure

```
Hello-World/
├── src/
│   ├── __init__.py
│   └── payment_service.py        # Dummy payment service
├── tests/
│   ├── __init__.py
│   └── test_payment.py           # Payment test cases (21 tests)
├── Jenkinsfile                    # Jenkins pipeline configuration
├── requirements.txt               # Python dependencies
├── pytest.ini                     # Pytest configuration
├── .gitignore                     # Git ignore patterns
├── SETUP_GUIDE.md                # This file
└── README                         # Original readme

```

## Test Cases Included

The test suite includes **21 comprehensive test cases**:

### Positive Tests
1. ✅ Successful payment processing
2. ✅ Multiple payments handling
3. ✅ Transaction retrieval
4. ✅ Successful refund processing

### Negative Tests
5. ❌ Invalid amount (zero)
6. ❌ Invalid amount (negative)
7. ❌ Invalid card number (too short)
8. ❌ Invalid card number (empty)
9. ❌ Invalid CVV (too short)
10. ❌ Invalid CVV (empty)
11. ❌ Refund non-existent transaction
12. ❌ Duplicate refund

### Edge Cases
13. 🔍 Large amount payment
14. 🔍 Small amount payment
15. 🔍 Get all transactions (empty)
16. 🔍 Get non-existent transaction
17. 🔍 Card number masking

## Prerequisites

### Local Setup
1. **Python 3.9+** installed
2. **Git** installed
3. **pip** package manager

### Jenkins Setup
1. **Jenkins** server installed and running
2. **Python plugin** for Jenkins
3. **HTML Publisher plugin** for Jenkins
4. **JUnit plugin** for Jenkins (usually pre-installed)

## Step-by-Step Procedure

### Part 1: Local Testing (Optional but Recommended)

1. **Clone/Navigate to your repository:**
   ```bash
   cd d:\Hello-World
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run tests locally:**
   ```bash
   # Run all tests
   pytest tests/ -v

   # Run with coverage
   pytest tests/ --cov=src --cov-report=html

   # Run specific test
   pytest tests/test_payment.py::TestPaymentService::test_successful_payment -v
   ```

4. **View coverage report:**
   ```bash
   # Open htmlcov/index.html in your browser
   start htmlcov/index.html
   ```

### Part 2: Jenkins Setup

#### Option A: Jenkins Pipeline (Recommended)

1. **Install Required Jenkins Plugins:**
   - Go to Jenkins → Manage Jenkins → Manage Plugins
   - Install:
     - Pipeline
     - Git plugin
     - HTML Publisher plugin
     - JUnit plugin

2. **Create New Jenkins Job:**
   - Click "New Item"
   - Enter job name: `Payment-Test-Suite`
   - Select "Pipeline"
   - Click OK

3. **Configure Pipeline:**
   - Scroll to "Pipeline" section
   - Definition: Select "Pipeline script from SCM"
   - SCM: Select "Git"
   - Repository URL: Enter your Git repository URL
   - Branch: `*/main` (or your default branch)
   - Script Path: `Jenkinsfile`
   - Click "Save"

4. **Run the Pipeline:**
   - Click "Build Now"
   - Monitor the build in the console output

#### Option B: Freestyle Project

1. **Create New Jenkins Job:**
   - Click "New Item"
   - Enter job name: `Payment-Test-Suite-Freestyle`
   - Select "Freestyle project"
   - Click OK

2. **Source Code Management:**
   - Select "Git"
   - Repository URL: Enter your repository URL
   - Branch: `*/main`

3. **Build Steps:**
   - Add build step → Execute Windows batch command
   ```batch
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   pytest tests/ -v --junitxml=test-results.xml --html=test-report.html --self-contained-html
   pytest tests/ --cov=src --cov-report=html --cov-report=xml
   ```

4. **Post-build Actions:**
   - Add "Publish JUnit test result report"
     - Test report XMLs: `test-results.xml`
   - Add "Publish HTML reports"
     - HTML directory to archive: `htmlcov`
     - Index page: `index.html`
     - Report title: `Coverage Report`

5. **Save and Build:**
   - Click "Save"
   - Click "Build Now"

### Part 3: GitHub/Git Integration

1. **Push your code to Git:**
   ```bash
   git add .
   git commit -m "Add payment test suite and Jenkins pipeline"
   git push origin main
   ```

2. **Configure Webhook (Optional - for automatic builds):**
   - In GitHub: Settings → Webhooks → Add webhook
   - Payload URL: `http://your-jenkins-url/github-webhook/`
   - Content type: `application/json`
   - Select: "Just the push event"
   - Active: ✓

3. **In Jenkins Job Configuration:**
   - Build Triggers → Check "GitHub hook trigger for GITScm polling"

### Part 4: Viewing Results

After a successful build, you can view:

1. **Test Results:**
   - Click on build number → Test Results
   - Shows all 21 test cases with pass/fail status

2. **Coverage Report:**
   - Click on build number → Coverage Report
   - Shows code coverage percentage

3. **HTML Test Report:**
   - Click on build number → Test Report
   - Detailed HTML report with test execution details

4. **Console Output:**
   - Click on build number → Console Output
   - View complete build log

## Jenkins Pipeline Stages

The Jenkinsfile includes these stages:

1. **Checkout** - Pulls code from repository
2. **Setup Python Environment** - Verifies Python installation
3. **Install Dependencies** - Installs required packages
4. **Run Tests** - Executes all test cases
5. **Code Coverage** - Generates coverage report
6. **Publish Results** - Publishes test and coverage reports

## Troubleshooting

### Common Issues

1. **Python not found:**
   - Add Python to system PATH
   - In Jenkins: Manage Jenkins → Global Tool Configuration → Add Python

2. **Module not found:**
   - Ensure `requirements.txt` is installed
   - Check virtual environment activation

3. **Tests not discovered:**
   - Verify pytest.ini configuration
   - Check test file naming (test_*.py)

4. **HTML reports not showing:**
   - Install HTML Publisher plugin
   - Configure Content Security Policy:
     ```
     Manage Jenkins → Script Console → Run:
     System.setProperty("hudson.model.DirectoryBrowserSupport.CSP", "")
     ```

## Running Specific Test Categories

```bash
# Run only successful payment tests
pytest tests/test_payment.py -k "successful" -v

# Run only negative tests
pytest tests/test_payment.py -k "invalid" -v

# Run with markers (if configured)
pytest tests/ -m "unit" -v
```

## CI/CD Best Practices

1. **Run tests on every commit**
2. **Maintain >80% code coverage**
3. **Review failed tests immediately**
4. **Keep test execution time < 5 minutes**
5. **Archive test reports for compliance**

## Next Steps

1. Add more test cases for edge scenarios
2. Integrate with Slack/Email for notifications
3. Add performance testing
4. Implement test data management
5. Add security scanning stages

## Support

For issues or questions:
- Check Jenkins console output
- Review test logs in test-report.html
- Verify Python and dependency versions

---

**Last Updated:** May 2026
