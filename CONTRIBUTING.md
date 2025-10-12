# Contributing to PassMark Scraper

Thank you for considering contributing to PassMark Scraper! 🎉

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Coding Standards](#coding-standards)
5. [Pull Request Process](#pull-request-process)
6. [Reporting Bugs](#reporting-bugs)
7. [Feature Requests](#feature-requests)

---

## Code of Conduct

This project follows a simple rule: **Be respectful and professional**.

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community

---

## How Can I Contribute?

### 🐛 Reporting Bugs

**Before submitting:**
- Check if the bug has already been reported in Issues
- Verify you're using the latest version
- Try to reproduce the issue

**When reporting:**
- Use a clear, descriptive title
- Describe exact steps to reproduce
- Include error messages and logs
- Specify your environment (OS, Python version, Docker version)

**Example:**
```markdown
**Bug:** Scraper fails for GPU list

**Steps to reproduce:**
1. Run `python scrape_all.py`
2. GPU scraping starts
3. Error after 2 minutes

**Error:**
```
TimeoutError: Page.wait_for_selector: Timeout 15000ms exceeded
```

**Environment:**
- OS: Windows 11
- Python: 3.11.5
- Docker: 24.0.6
```

---

### ✨ Feature Requests

We welcome feature requests! Please:
- Check if the feature has already been requested
- Describe the use case
- Explain why this would be useful
- Suggest implementation if possible

---

### 🔧 Code Contributions

#### Types of Contributions Needed

1. **Scraper Improvements**
   - Better HTML parsing
   - Support for more PassMark pages
   - Error handling

2. **API Enhancements**
   - New endpoints
   - Performance optimizations
   - Better error responses

3. **Documentation**
   - Tutorial improvements
   - Code comments
   - API examples

4. **Testing**
   - Unit tests
   - Integration tests
   - Load tests

5. **Infrastructure**
   - Docker improvements
   - CI/CD pipelines
   - Monitoring

---

## Development Setup

### Prerequisites

- Python 3.11+
- Docker (optional)
- Git

### Local Setup

```bash
# Clone repository
git clone https://github.com/yourusername/PassMarkScraper.git
cd PassMarkScraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run tests (when available)
pytest

# Start development server
uvicorn app.main:app --reload --port 9091
```

### Docker Setup

```bash
# Build and run
docker-compose up --build

# Run tests in container
docker exec passmark-scraper pytest
```

---

## Coding Standards

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** for function signatures
- Write **docstrings** for all public functions
- Maximum line length: **100 characters**
- Use **meaningful variable names**

**Example:**
```python
def scrape_component(url: str, timeout: int = 30) -> dict:
    """
    Scrape a single component from PassMark.
    
    Args:
        url: PassMark component URL
        timeout: Request timeout in seconds
        
    Returns:
        Component data dictionary
        
    Raises:
        ValueError: If URL is invalid
        TimeoutError: If request times out
    """
    # Implementation
    pass
```

### Project Structure

- **app/** - Application code
- **docs/** - Documentation
- **static/** - Frontend files
- **config/** - Configuration
- **tests/** - Test files (when added)

### Commit Messages

Use conventional commits:

```
feat: add GraphQL API support
fix: handle timeout in GPU scraper
docs: update API reference
refactor: simplify database queries
test: add unit tests for normalizer
chore: update dependencies
```

---

## Pull Request Process

### Before Submitting

1. **Test your changes**
   ```bash
   # Run all tests
   pytest
   
   # Check linting
   flake8 app/
   
   # Type checking
   mypy app/
   ```

2. **Update documentation**
   - README.md if API changed
   - CHANGELOG.md with your changes
   - Docstrings for new functions

3. **Follow coding standards**
   - PEP 8 compliant
   - Type hints included
   - Tests added (if applicable)

### Submitting

1. **Fork the repository**

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Small, focused commits
   - Clear commit messages
   - Test thoroughly

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**
   - Use a clear title
   - Describe what changed and why
   - Reference related issues
   - Include screenshots if UI changed

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Tested manually
- [ ] Added unit tests
- [ ] Tested in Docker

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No breaking changes (or documented)
```

---

## Development Tips

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_scraper.py

# With coverage
pytest --cov=app
```

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload

# Check logs
tail -f logs/app.log
```

### Database Inspection

```bash
# Connect to database
sqlite3 benchmarks.db

# Check component count
SELECT component_type, COUNT(*) FROM component_benchmarks GROUP BY component_type;

# Find specific component
SELECT * FROM component_benchmarks WHERE name LIKE '%RTX 3080%';
```

---

## 🎯 Good First Issues

Looking to contribute but don't know where to start?

- Add unit tests for normalizer functions
- Improve error messages in API responses
- Add more examples to documentation
- Create GitHub Actions workflow
- Add component price tracking
- Improve web UI styling

---

## 📧 Questions?

- **Issues:** For bug reports and feature requests
- **Discussions:** For questions and general discussion
- **Email:** (if you add contact email)

---

## 📝 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🙏

