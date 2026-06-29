# REVIEW_CHECKLIST.md

# Sprint Review Checklist

This checklist must be completed before every commit.

---

# 1. Architecture Review

* [ ] Architecture unchanged
* [ ] Package responsibilities respected
* [ ] No cyclic dependency
* [ ] Dependency rules followed
* [ ] SOLID principles followed

---

# 2. Code Quality

* [ ] Type hints added
* [ ] Public docstrings written
* [ ] No duplicated code
* [ ] No dead code
* [ ] No TODO left in implementation
* [ ] No wildcard imports

---

# 3. Security Review

* [ ] External inputs validated
* [ ] JSON validated
* [ ] PDF validated
* [ ] File paths sanitized
* [ ] No eval()
* [ ] No exec()
* [ ] No shell=True
* [ ] Exceptions handled safely

---

# 4. Error Handling

* [ ] Domain exceptions used
* [ ] Errors logged
* [ ] User-friendly messages
* [ ] Graceful failure

---

# 5. Testing Review

* [ ] Happy path tested
* [ ] Invalid input tested
* [ ] Edge cases tested
* [ ] Failure scenarios tested
* [ ] Regression impact considered

---

# 6. Static Analysis

* [ ] Ruff passes
* [ ] Black passes
* [ ] MyPy passes
* [ ] Pytest passes

---

# 7. Performance Review

* [ ] No unnecessary loops
* [ ] No duplicate parsing
* [ ] Efficient memory usage
* [ ] Stateless implementation

---

# 8. Documentation Review

* [ ] Docstrings updated
* [ ] README updated (if required)
* [ ] Comments explain why, not what

---

# 9. Git Review

* [ ] Single logical commit
* [ ] Conventional commit message
* [ ] No temporary files committed

---

# 10. Final Approval Checklist

Before marking a sprint complete:

* [ ] Feature complete
* [ ] Tests complete
* [ ] Static analysis clean
* [ ] Security review complete
* [ ] Architecture preserved
* [ ] Ready for merge

---

# Definition of Done

A sprint is complete only when every checklist item above has been verified.

If any item remains unchecked, the sprint must not be considered complete.
