from pathlib import Path


SOURCE = Path("capture/exhibition-burst-mode.js")


def source():
    return SOURCE.read_text(encoding="utf-8")


def test_detail_visibility_only_mutates_hidden_when_state_changes():
    text = source()
    assert "const shouldHide = !showDetails;" in text
    assert "if (node.hidden !== shouldHide) node.hidden = shouldHide;" in text
    assert "node.hidden = !showDetails;" not in text
    assert 'attributeFilter: ["hidden", "disabled"]' in text


def test_details_toggle_still_syncs_visibility():
    text = source()
    details = text.index('case "details":')
    save = text.index('case "save":', details)
    block = text[details:save]
    assert 'document.body.classList.toggle("kc-simple-show-details")' in block
    assert 'syncSimpleDetailVisibility(byId("kcCaptureForm"))' in block
    assert "updateControls();" in block


def test_photo_first_simple_screen_keeps_only_leading_fields_and_quick_photo():
    text = source()
    assert 'const keepBasic = new Set(["supplier", "yarn_name"])' in text
    assert 'id="kcSimpleQuickPhoto"' in text
    assert 'data-photo-source="camera"' in text
    assert 'data-photo-source="library"' in text
    assert '詳細（必要な時だけ）' in text


def test_save_routes_remain_connected_to_existing_save_lifecycle():
    text = source()
    for action in ("save", "save-next-material", "save-change-supplier"):
        assert f'case "{action}":' in text
    assert "startSave(button.dataset.simpleAction);" in text
    assert "source.click();" in text
    assert 'document.addEventListener("kc:capture-save-finished"' in text
