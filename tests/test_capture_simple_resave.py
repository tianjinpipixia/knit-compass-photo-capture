from pathlib import Path


SOURCE = Path("capture/exhibition-burst-mode.js")


def test_existing_draft_bypasses_new_capture_requirements():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'const isExistingDraft = Boolean(clean(form.elements.record_id?.value));' in source
    assert 'if (!isExistingDraft && (!clean(form.elements.supplier?.value) || !photoCount())) {' in source


def test_new_capture_still_requires_supplier_and_photo():
    source = SOURCE.read_text(encoding="utf-8")
    guard = source.index('if (!isExistingDraft && (!clean(form.elements.supplier?.value) || !photoCount())) {')
    click = source.index('source.click();', guard)
    guarded_block = source[guard:click]
    assert 'メーカー / Supplierを選択または入力してください。' in guarded_block
    assert '写真を1枚以上追加してください。' in guarded_block
