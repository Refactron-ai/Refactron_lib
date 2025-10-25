# Refactron Architecture

## Overview

Refactron is designed as a modular, extensible Python library for code analysis and refactoring. The architecture follows clean separation of concerns with well-defined interfaces.

## Project Structure

```
refactron/
├── core/                   # Core functionality
│   ├── refactron.py       # Main entry point
│   ├── config.py          # Configuration management
│   ├── models.py          # Data models
│   ├── analysis_result.py # Analysis results
│   └── refactor_result.py # Refactoring results
├── analyzers/             # Code analyzers
│   ├── base_analyzer.py   # Abstract base class
│   ├── complexity_analyzer.py
│   └── code_smell_analyzer.py
├── refactorers/           # Code refactorers
│   ├── base_refactorer.py # Abstract base class
│   └── extract_method_refactorer.py
└── cli.py                 # Command-line interface
```

## Core Components

### 1. Refactron (Main Class)

The `Refactron` class is the main entry point that orchestrates analysis and refactoring:

```python
class Refactron:
    def __init__(self, config: Optional[RefactronConfig] = None)
    def analyze(self, target: Union[str, Path]) -> AnalysisResult
    def refactor(self, target: Union[str, Path], ...) -> RefactorResult
```

**Responsibilities:**
- Initialize analyzers and refactorers
- Coordinate file discovery
- Run analysis and refactoring operations
- Return structured results

### 2. Configuration System

`RefactronConfig` provides flexible configuration:

```python
@dataclass
class RefactronConfig:
    enabled_analyzers: List[str]
    enabled_refactorers: List[str]
    max_function_complexity: int
    # ... other settings
```

**Features:**
- Default configuration
- YAML file support
- Per-project customization

### 3. Data Models

Core data structures defined in `models.py`:

- **`CodeIssue`**: Represents detected problems
- **`FileMetrics`**: Metrics for a single file
- **`RefactoringOperation`**: Proposed code changes
- **`IssueLevel`**: Severity enumeration
- **`IssueCategory`**: Issue type enumeration

## Analyzers

Analyzers detect code issues and patterns.

### Base Analyzer

All analyzers inherit from `BaseAnalyzer`:

```python
class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
```

### Built-in Analyzers

1. **ComplexityAnalyzer**
   - Cyclomatic complexity
   - Function length
   - Maintainability index
   
2. **CodeSmellAnalyzer**
   - Too many parameters
   - Deep nesting
   - Magic numbers
   - Missing docstrings
   - Duplicate code patterns

### Creating a Custom Analyzer

```python
from refactron.analyzers.base_analyzer import BaseAnalyzer
from refactron.core.models import CodeIssue, IssueLevel, IssueCategory

class MyAnalyzer(BaseAnalyzer):
    @property
    def name(self) -> str:
        return "my_analyzer"
    
    def analyze(self, file_path: Path, source_code: str) -> List[CodeIssue]:
        issues = []
        
        # Your analysis logic here
        tree = ast.parse(source_code)
        # ... analyze the AST
        
        # Create issues
        issue = CodeIssue(
            category=IssueCategory.CODE_SMELL,
            level=IssueLevel.WARNING,
            message="Problem detected",
            file_path=file_path,
            line_number=10,
            suggestion="Fix it this way",
            rule_id="MY001",
        )
        issues.append(issue)
        
        return issues
```

**Register in config:**
```yaml
enabled_analyzers:
  - my_analyzer
```

## Refactorers

Refactorers propose and apply code transformations.

### Base Refactorer

All refactorers inherit from `BaseRefactorer`:

```python
class BaseRefactorer(ABC):
    @abstractmethod
    def refactor(self, file_path: Path, source_code: str) -> List[RefactoringOperation]:
        pass
    
    @property
    @abstractmethod
    def operation_type(self) -> str:
        pass
```

### Built-in Refactorers

1. **ExtractMethodRefactorer**
   - Identifies opportunities to extract methods
   - Suggests breaking down complex functions

### Creating a Custom Refactorer

```python
from refactron.refactorers.base_refactorer import BaseRefactorer
from refactron.core.models import RefactoringOperation

class MyRefactorer(BaseRefactorer):
    @property
    def operation_type(self) -> str:
        return "my_refactoring"
    
    def refactor(self, file_path: Path, source_code: str) -> List[RefactoringOperation]:
        operations = []
        
        # Your refactoring logic here
        tree = ast.parse(source_code)
        # ... find refactoring opportunities
        
        operation = RefactoringOperation(
            operation_type=self.operation_type,
            file_path=file_path,
            line_number=42,
            description="Apply my refactoring",
            old_code="old code",
            new_code="new code",
            risk_score=0.3,  # 0.0 = safe, 1.0 = risky
            reasoning="This improves readability",
        )
        operations.append(operation)
        
        return operations
```

## Analysis Pipeline

1. **File Discovery**
   - Scan directories for Python files
   - Apply include/exclude patterns
   
2. **File Analysis**
   - Read source code
   - Parse into AST
   - Run each enabled analyzer
   - Collect issues
   
3. **Metric Calculation**
   - Lines of code
   - Comment lines
   - Complexity metrics
   
4. **Result Aggregation**
   - Combine all issues
   - Generate summary statistics
   - Create report

## Refactoring Pipeline

1. **Analysis Phase**
   - Run analyzers to understand code
   
2. **Opportunity Detection**
   - Each refactorer identifies opportunities
   - Calculate risk scores
   
3. **Operation Generation**
   - Create RefactoringOperation objects
   - Include before/after code
   
4. **Preview/Application**
   - Show diff (preview mode)
   - Apply changes (apply mode)
   - Create backups

## Extension Points

### 1. Custom Rules

Add rules via configuration:

```yaml
custom_rules:
  max_class_methods: 20
  enforce_type_hints: true
```

Access in analyzers:
```python
custom_value = self.config.custom_rules.get("max_class_methods", 20)
```

### 2. Plugin System (Future)

Planned plugin architecture:

```python
from refactron.plugins import RefactronPlugin

class MyPlugin(RefactronPlugin):
    def register(self):
        return {
            "analyzers": [MyAnalyzer],
            "refactorers": [MyRefactorer],
        }
```

### 3. Custom Reporters

Currently supports: text, JSON, HTML
Future: PDF, Markdown, etc.

## CLI Architecture

The CLI (`cli.py`) provides command-line interface:

```bash
refactron analyze <target>
refactron refactor <target>
refactron report <target>
refactron init
```

Built with `click` for:
- Argument parsing
- Help text
- Option handling

Uses `rich` for:
- Beautiful terminal output
- Tables
- Progress indicators
- Syntax highlighting

## Design Principles

1. **Modularity**: Each component has single responsibility
2. **Extensibility**: Easy to add new analyzers/refactorers
3. **Configuration**: Customizable via config files
4. **Safety**: Preview before apply, risk scoring
5. **Clarity**: Clear error messages and suggestions
6. **Performance**: Efficient AST parsing, caching where appropriate

## Technology Stack

- **libcst**: Concrete syntax tree (preserves formatting)
- **ast**: Abstract syntax tree (analysis)
- **radon**: Complexity metrics
- **astroid**: Advanced AST analysis
- **click**: CLI framework
- **rich**: Terminal UI
- **pyyaml**: Configuration files
- **pytest**: Testing

## Testing Strategy

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test end-to-end workflows
3. **Example-Based Tests**: Use real code examples
4. **Coverage**: Aim for >80% code coverage

## Future Enhancements

1. **Multi-language Support**: JavaScript, TypeScript, etc.
2. **AI Integration**: LLM-powered suggestions
3. **IDE Plugins**: VS Code, PyCharm
4. **CI/CD Integration**: GitHub Actions, GitLab CI
5. **Learning System**: Adapt to project patterns
6. **Batch Processing**: Parallel analysis
7. **Auto-fix**: Automatically apply safe refactorings
8. **Custom Rule Engine**: DSL for defining rules

## Performance Considerations

- Use generators for large file sets
- Cache parsed ASTs when possible
- Parallelize analysis across files
- Lazy load analyzers
- Incremental analysis (only changed files)

## Security Considerations

- Never execute analyzed code
- Sandbox refactoring operations
- Validate file paths
- Limit file sizes
- Rate limit external API calls (future)

---

For more details, see:
- [API Documentation](docs/api.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Examples](examples/)

