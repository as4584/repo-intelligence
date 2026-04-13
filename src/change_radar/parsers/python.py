"""Lightweight Python structural extraction using the standard library AST."""

from __future__ import annotations

import ast
from pathlib import PurePosixPath

from change_radar.types import EdgeRecord, FileRecord, SymbolRecord

SOURCE_ROOT_PREFIXES = {"src", "lib", "app"}


def extract_symbols_and_edges(
    file_record: FileRecord, source_text: str, available_paths: set[str]
) -> tuple[list[SymbolRecord], list[EdgeRecord]]:
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return [], []

    module_index = _build_module_index(available_paths)
    current_module = _canonical_module_name(file_record.relative_path)
    symbols = _extract_symbols(file_record, tree)
    edges = _extract_import_edges(file_record, tree, module_index, current_module)
    return symbols, edges


def _extract_symbols(file_record: FileRecord, tree: ast.AST) -> list[SymbolRecord]:
    symbols: list[SymbolRecord] = []
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                SymbolRecord(
                    repo_root=file_record.repo_root,
                    symbol_name=node.name,
                    symbol_kind="function",
                    relative_path=file_record.relative_path,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                )
            )
            continue

        if isinstance(node, ast.ClassDef):
            symbols.append(
                SymbolRecord(
                    repo_root=file_record.repo_root,
                    symbol_name=node.name,
                    symbol_kind="class",
                    relative_path=file_record.relative_path,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                )
            )

    symbols.sort(key=lambda item: (item.start_line, item.symbol_name))
    return symbols


def _extract_import_edges(
    file_record: FileRecord,
    tree: ast.AST,
    module_index: dict[str, str],
    current_module: str,
) -> list[EdgeRecord]:
    seen: set[tuple[str, str, str, str]] = set()
    edges: list[EdgeRecord] = []

    for node in ast.walk(tree):
        candidates: set[str] = set()
        if isinstance(node, ast.Import):
            for alias in node.names:
                candidates.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base_module = _resolve_from_base(current_module, node.module, node.level)
            if base_module:
                candidates.add(base_module)
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    candidates.add(f"{base_module}.{alias.name}")

        for candidate in sorted(candidates):
            resolved_path = module_index.get(candidate)
            if resolved_path is None or resolved_path == file_record.relative_path:
                continue
            key = (file_record.repo_root, file_record.relative_path, resolved_path, "imports")
            if key in seen:
                continue
            seen.add(key)
            edges.append(
                EdgeRecord(
                    repo_root=file_record.repo_root,
                    source_path=file_record.relative_path,
                    target_path=resolved_path,
                    edge_type="imports",
                )
            )

    edges.sort(key=lambda item: (item.source_path, item.target_path))
    return edges


def _build_module_index(available_paths: set[str]) -> dict[str, str]:
    module_index: dict[str, str] = {}
    for relative_path in sorted(available_paths):
        path = PurePosixPath(relative_path)
        if path.suffix != ".py":
            continue

        raw_parts = path.parts[:-1] if path.name == "__init__.py" else path.with_suffix("").parts
        if raw_parts:
            raw_module = ".".join(raw_parts)
            module_index.setdefault(raw_module, relative_path)

        if raw_parts and raw_parts[0] in SOURCE_ROOT_PREFIXES and len(raw_parts) >= 2:
            stripped_module = ".".join(raw_parts[1:])
            module_index.setdefault(stripped_module, relative_path)

    return module_index


def _canonical_module_name(relative_path: str) -> str:
    path = PurePosixPath(relative_path)
    parts = path.parts[:-1] if path.name == "__init__.py" else path.with_suffix("").parts
    if parts and parts[0] in SOURCE_ROOT_PREFIXES and len(parts) >= 2:
        return ".".join(parts[1:])
    return ".".join(parts)


def _resolve_from_base(current_module: str, module: str | None, level: int) -> str | None:
    if level == 0:
        return module

    current_parts = current_module.split(".") if current_module else []
    if not current_parts:
        return module

    package_parts = current_parts[:-1]
    if level > len(package_parts):
        return module

    base_parts = package_parts[: len(package_parts) - level + 1]
    if module:
        base_parts.extend(module.split("."))
    return ".".join(part for part in base_parts if part)
