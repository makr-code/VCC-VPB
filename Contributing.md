# Contributing / Beitragsrichtlinien

**Version:** 0.5.0

Vielen Dank für Ihr Interesse, zu VPB beizutragen!

Thank you for your interest in contributing to VPB!

---

## 🤝 How to Contribute / Wie beitragen

### Ways to Contribute / Beitragsmöglichkeiten

**Code Contributions:**
- 🐛 Fix bugs
- ✨ Add features
- 🎨 Improve UI
- ⚡ Optimize performance
- 🔒 Enhance security

**Non-Code Contributions:**
- 📝 Improve documentation
- 🌍 Add translations
- 🧪 Write tests
- 🎓 Create tutorials
- 💬 Answer questions

---

## 🐛 Reporting Bugs / Fehler melden

### Before Reporting / Vor der Meldung

1. **Search existing issues** - May already be reported
2. **Try latest version** - Might be fixed already
3. **Reproduce the bug** - Ensure it's consistent

### Creating a Bug Report / Fehlerbericht erstellen

**Use this template:**

```markdown
**Bug Description:**
Clear description of the bug

**Steps to Reproduce:**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- VPB Version: 0.5.0
- OS: Windows 11 / macOS 13 / Ubuntu 22.04
- Python Version: 3.10
- Browser (if API): Chrome 120

**Screenshots:**
If applicable

**Additional Context:**
Any other relevant information
```

**Submit:** https://github.com/makr-code/VCC-VPB/issues/new?labels=bug

---

## ✨ Requesting Features / Features anfragen

### Feature Request Template

```markdown
**Feature Title:**
Brief feature name

**Problem:**
What problem does this solve?

**Proposed Solution:**
How should it work?

**Alternatives:**
Other solutions considered

**Use Case:**
Who benefits and how?

**Priority:**
Low / Medium / High (your opinion)
```

**Check First:**
- **[[Roadmap]]** - May already be planned
- Existing issues - May already be requested

**Submit:** https://github.com/makr-code/VCC-VPB/issues/new?labels=enhancement

---

## 🔧 Development Setup / Entwicklungsumgebung

### 1. Fork & Clone

```bash
# Fork on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/VCC-VPB.git
cd VCC-VPB

# Add upstream remote
git remote add upstream https://github.com/makr-code/VCC-VPB.git
```

### 2. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest flake8 black mypy
```

### 3. Create Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-new-feature
```

See **[[Development-Guide]]** for complete setup.

---

## 💻 Making Changes / Änderungen vornehmen

### Code Standards / Code-Standards

**Python Style:**
- Follow **PEP 8**
- Use **type hints**
- Write **docstrings**
- Max line length: **120 characters**

**Example:**
```python
def process_element(element: VPBElement) -> Dict[str, Any]:
    """
    Process a VPB element and return result.
    
    Args:
        element: The VPB element to process
        
    Returns:
        Dictionary with processing result
        
    Raises:
        ValueError: If element is invalid
    """
    if not element.is_valid():
        raise ValueError(f"Invalid element: {element.id}")
    
    return {
        "id": element.id,
        "type": element.type,
        "processed": True
    }
```

### Documentation

**Update Documentation When:**
- Adding new features
- Changing behavior
- Modifying API
- Fixing bugs (if affects usage)

**Documentation Files:**
- User-facing: Wiki pages (Home.md, User-Guide.md, etc.)
- Developer-facing: Development-Guide.md, Architecture.md
- API: API-Reference.md
- Changes: Changelog.md

### Testing

**Required:**
- All new code **must have tests**
- All tests **must pass**
- Coverage should be **≥ 80%**

**Run Tests:**
```bash
# All tests
pytest

# With coverage
pytest --cov=vpb --cov-report=html

# Specific test
pytest tests/test_element.py::test_element_creation -v
```

**Test Example:**
```python
def test_my_new_feature():
    """Test my new feature"""
    # Arrange
    element = VPBElement(id="test1", type="COUNTER")
    
    # Act
    result = my_new_function(element)
    
    # Assert
    assert result["success"] is True
    assert "data" in result
```

See **[[Development-Guide#Testing]]** for details.

---

## 📝 Commit Guidelines / Commit-Richtlinien

### Commit Message Format

Use **[Conventional Commits](https://www.conventionalcommits.org/)**:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types / Typen

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat: Add LOOP element` |
| `fix` | Bug fix | `fix: Correct validation error` |
| `docs` | Documentation | `docs: Update API reference` |
| `style` | Code style | `style: Format with black` |
| `refactor` | Refactoring | `refactor: Simplify element creation` |
| `test` | Tests | `test: Add counter element tests` |
| `chore` | Maintenance | `chore: Update dependencies` |
| `perf` | Performance | `perf: Optimize graph queries` |
| `ci` | CI/CD | `ci: Add GitHub Actions` |

### Examples / Beispiele

**Good Commits:**
```
feat: Add semantic search to process list

Implements ChromaDB integration for semantic process search.
Users can now search processes using natural language queries.

Closes #42
```

```
fix: Resolve SAGA rollback issue

Fixed issue where failed ChromaDB writes didn't trigger
proper rollback compensation in PostgreSQL and Neo4j.

Fixes #58
```

**Bad Commits:**
```
❌ Fixed stuff
❌ WIP
❌ Update file
❌ asdfasdf
```

---

## 🔍 Code Review Process / Code-Review-Prozess

### Before Submitting PR / Vor dem PR

**Checklist:**
- [ ] Code follows PEP 8
- [ ] All tests pass
- [ ] New tests added (coverage ≥ 80%)
- [ ] Documentation updated
- [ ] Changelog.md updated
- [ ] No merge conflicts
- [ ] Commits are clean and descriptive
- [ ] No debug code/print statements

### Creating Pull Request / Pull Request erstellen

**PR Template:**

```markdown
## Description
Clear description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Changelog updated

## Related Issues
Closes #42
Related to #55

## Screenshots (if applicable)
```

### Review Process / Review-Ablauf

1. **Automated Checks** - CI/CD runs tests
2. **Code Review** - Maintainer reviews code
3. **Feedback** - Address review comments
4. **Approval** - Once approved, will be merged
5. **Merge** - Maintainer merges PR

### Review Timeline / Review-Zeitplan

- Initial review: **Within 3-5 days**
- Follow-up: **1-2 days**
- Merge: **After approval**

---

## 🎨 Design Guidelines / Design-Richtlinien

### UI/UX Contributions

**Guidelines:**
- Consistent with existing UI
- Accessible (keyboard navigation, screen readers)
- Responsive design
- Clear visual feedback
- Intuitive interactions

**Before Implementing:**
- Discuss in issue
- Share mockups/wireframes
- Get feedback from maintainers

---

## 🌍 Translation / Übersetzung

VPB supports bilingual documentation (German/English).

**How to Contribute:**
1. Identify untranslated content
2. Create issue or PR with translations
3. Follow existing bilingual format

**Format:**
```markdown
## Section Title / Abschnittstitel

**EN:** English text here.

**DE:** Deutsche Übersetzung hier.
```

---

## 📚 Documentation Contributions

### Wiki Pages

**Structure:**
- Follow existing format
- Bilingual (DE/EN)
- Clear navigation
- Code examples
- Links to related pages

**Guidelines:**
- User-friendly language
- Step-by-step instructions
- Screenshots when helpful
- Keep updated

### Code Documentation

**Docstrings:**
```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    Brief description.
    
    Detailed description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When and why raised
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        {'success': True}
    """
```

---

## 🔒 Security / Sicherheit

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

**Instead:**
1. Email: (contact maintainer privately)
2. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

**Response:**
- Acknowledgment within **24 hours**
- Fix timeline communicated
- Credit given (if desired)

---

## ⚖️ License / Lizenz

By contributing, you agree that your contributions will be licensed under the same license as the project.

**Protected Modules:**
- Some modules protected by VERITAS Tech GmbH
- Check module headers
- Contact if questions

---

## 🎯 Good First Issues

Looking to start contributing?

**Search for:**
- Label: `good first issue`
- Label: `help wanted`
- Label: `documentation`

**Beginner-Friendly Areas:**
- Documentation improvements
- Test additions
- UI enhancements
- Translation

---

## 💬 Communication / Kommunikation

### Where to Ask Questions

**GitHub Issues:**
- Bug reports
- Feature requests
- General questions

**GitHub Discussions:** (coming soon)
- General discussions
- Ideas
- Q&A

**Pull Requests:**
- Code-specific questions
- Implementation details

### Be Respectful / Respektvoll sein

- Be kind and courteous
- Respect different opinions
- Constructive feedback
- Inclusive language
- Patient with newcomers

---

## 🏆 Recognition / Anerkennung

Contributors are recognized in:
- Changelog.md
- Release notes
- Contributors list (coming soon)

**Thank you for contributing! 🎉**

---

## Related Documentation

- **[[Development-Guide]]** - Setup and workflow
- **[[Architecture]]** - System architecture
- **[[Testing]]** - Testing guidelines (coming soon)
- **[[Changelog]]** - Version history

---

## External Resources

- **Conventional Commits:** https://www.conventionalcommits.org/
- **PEP 8:** https://pep8.org/
- **Git Flow:** https://nvie.com/posts/a-successful-git-branching-model/

---

**Questions?** Open an issue or contact maintainers.

[[Home]] | [[Development-Guide]] | [[FAQ]]
