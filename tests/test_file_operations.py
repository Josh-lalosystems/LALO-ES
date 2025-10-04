import asyncio
import os
from core.tools.file_operations import file_operations_tool, ALLOWED_ROOT

async def _run(op, path, content=None):
    return await file_operations_tool.execute_with_validation(op=op, path=path, content=content)

def test_list_root(tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_TOOL_ROOT", str(tmp_path))
    # recreate tool with new root
    from importlib import reload
    import core.tools.file_operations as fop
    reload(fop)
    tool = fop.file_operations_tool

    # create files
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "sub").mkdir()
    res = asyncio.run(tool.execute_with_validation(op="list", path="."))
    assert res.success
    assert res.output["type"] == "dir"
    names = {item["name"] for item in res.output["items"]}
    assert {"a.txt", "sub"}.issubset(names)

def test_write_and_read_text(tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_TOOL_ROOT", str(tmp_path))
    from importlib import reload
    import core.tools.file_operations as fop
    reload(fop)
    tool = fop.file_operations_tool

    res_w = asyncio.run(tool.execute_with_validation(op="write", path="docs/note.txt", content="hello world"))
    assert res_w.success
    res_r = asyncio.run(tool.execute_with_validation(op="read", path="docs/note.txt"))
    assert res_r.success
    assert res_r.output["content"] == "hello world"

def test_delete(tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_TOOL_ROOT", str(tmp_path))
    from importlib import reload
    import core.tools.file_operations as fop
    reload(fop)
    tool = fop.file_operations_tool

    p = tmp_path / "to_delete.txt"
    p.write_text("x")
    res_d = asyncio.run(tool.execute_with_validation(op="delete", path="to_delete.txt"))
    assert res_d.success
    assert not p.exists()
