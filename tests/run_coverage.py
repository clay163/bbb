"""基于 AST + trace 的精确覆盖率统计脚本"""
import ast
import sys
import trace
import unittest
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))


def get_function_body_lines(filename):
    """使用 AST 精确获取函数体内可执行语句的行号"""
    with open(filename, encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    lines = set()

    def walk_stmt(node):
        # 收集语句行号，排除函数/类定义本身
        if isinstance(node, ast.stmt) and hasattr(node, "lineno"):
            if not isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                lines.add(node.lineno)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.stmt):
                walk_stmt(child)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for stmt in node.body:
                walk_stmt(stmt)
    return lines


# 创建 tracer 并运行测试
tracer = trace.Trace(count=True, trace=False)
loader = unittest.TestLoader()
suite = loader.discover(str(root / "tests"))
runner = unittest.TextTestRunner(verbosity=0)
result = tracer.runfunc(lambda: runner.run(suite))

if not result.wasSuccessful():
    print("TESTS FAILED")
    sys.exit(1)

results = tracer.results()

app_dir = root / "app"
target_files = [
    app_dir / "fridge.py",
    app_dir / "storage.py",
    app_dir / "stats.py",
    app_dir / "recipe.py",
    app_dir / "vision.py",
]

print("=" * 65)
print(f"{'File':<20} {'Coverage':>10} {'Covered':>10} {'Total':>8}  {'Missing Lines'}")
print("=" * 65)

total_all = 0
covered_all = 0

for py_file in target_files:
    abs_path = str(py_file.resolve()).replace("\\", "/")
    executable_lines = get_function_body_lines(py_file)

    covered = set()
    for (fn, ln), count in results.counts.items():
        fn_norm = fn.replace("\\", "/")
        if fn_norm == abs_path and count > 0:
            covered.add(ln)

    covered_lines = executable_lines & covered
    missing_lines = sorted(executable_lines - covered)
    total = len(executable_lines)
    cov_count = len(covered_lines)

    total_all += total
    covered_all += cov_count

    pct = cov_count / total * 100 if total > 0 else 100.0
    missing_str = str(missing_lines) if missing_lines else "none"
    print(f"{py_file.name:<20} {pct:>9.1f}% {cov_count:>10} {total:>8}  {missing_str}")

print("=" * 65)
overall = covered_all / total_all * 100 if total_all > 0 else 100.0
print(f"{'OVERALL':<20} {overall:>9.1f}% {covered_all:>10} {total_all:>8}")
print("=" * 65)

if overall >= 80:
    print(f"\nPASS: Coverage {overall:.1f}% >= 80% threshold")
else:
    print(f"\nFAIL: Coverage {overall:.1f}% < 80% threshold")
    sys.exit(1)