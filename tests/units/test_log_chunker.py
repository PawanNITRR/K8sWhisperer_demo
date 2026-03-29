from utils.log_chunker import extract_error_snippets, prepare_logs_for_llm, tail_lines


def test_tail_lines_truncates():
    lines = "\n".join([f"line-{i}" for i in range(150)])
    out = tail_lines(lines, max_lines=100)
    assert out.startswith("line-50") or "line-149" in out
    assert len(out.splitlines()) == 100


def test_extract_error_snippets():
    text = "ok line\nERROR: boom\nfine\nfatal: x\n"
    hits = extract_error_snippets(text)
    assert any("ERROR" in h for h in hits)


def test_prepare_logs_for_llm_caps_size():
    huge = "x" * 100_000
    out = prepare_logs_for_llm(huge, tail_line_count=10, max_chars=5000)
    assert len(out) <= 6000
