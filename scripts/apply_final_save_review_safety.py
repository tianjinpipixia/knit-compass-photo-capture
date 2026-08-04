#!/usr/bin/env python3
"""Apply the final non-overlapping save and Human Review safety fixes."""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    fail(f"could not find {label}")


def replace_all(text: str, old: str, new: str, label: str, minimum: int = 1) -> str:
    count = text.count(old)
    if count >= minimum:
        return text.replace(old, new)
    if new in text:
        return text
    fail(f"could not find {label}")


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    start_at = text.find(start)
    if start_at < 0:
        if replacement in text:
            return text
        fail(f"could not find start of {label}")
    end_at = text.find(end, start_at)
    if end_at < 0:
        fail(f"could not find end of {label}")
    return text[:start_at] + replacement + text[end_at:]


def git_blob(path: str) -> str:
    result = subprocess.run(
        ["git", "hash-object", f"--path={path}", "--", path],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    digest = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", digest):
        fail(f"invalid blob hash for {path}: {digest}")
    return digest


def patch_photo_capture() -> None:
    text = read("app.js")
    text = replace_once(text, "const APP_VERSION = '1.2.1';", "const APP_VERSION = '1.2.2';", "Photo Capture version")
    text = replace_once(
        text,
        "    document.getElementById('saveAndSend').addEventListener('click', () => {\n      submitMode = 'send';\n      form.requestSubmit();\n    });\n    form.addEventListener('submit', saveCapture);",
        "    document.getElementById('saveDraft').addEventListener('click', () => {\n      submitMode = 'draft';\n    });\n    document.getElementById('saveAndSend').addEventListener('click', () => {\n      submitMode = 'send';\n      form.requestSubmit();\n    });\n    form.addEventListener('invalid', () => {\n      submitMode = 'draft';\n    }, true);\n    form.addEventListener('submit', saveCapture);",
        "submit mode reset",
    )
    text = replace_once(
        text,
        "    const values = [...String(text || '').matchAll(/(\\d+(?:\\.\\d+)?)\\s*%?/g)].map((match) => Number(match[1]));",
        "    const values = [...String(text || '').matchAll(/(\\d+(?:\\.\\d+)?)\\s*%/g)].map((match) => Number(match[1]));",
        "percentage-only composition parser",
    )
    text = replace_once(
        text,
        "      messageElement.textContent = '数値を入力すると合計を確認します。';",
        "      messageElement.textContent = /\\d/.test(String(text || '')) ? '合計確認する数値には%を付けてください。' : '数値を入力すると合計を確認します。';",
        "composition guidance",
    )
    text = replace_once(
        text,
        "    if (submitMode === 'send') enqueueHandoff(eventRow);\n    submitMode = 'draft';\n    editing = null;\n    await renderApp();\n    document.getElementById('inbox').scrollIntoView({ behavior: 'smooth' });",
        "    let handoffError = null;\n    if (submitMode === 'send') {\n      try {\n        enqueueHandoff(eventRow);\n      } catch (error) {\n        handoffError = error;\n      }\n    }\n    submitMode = 'draft';\n    editing = null;\n    await renderApp();\n    document.getElementById('inbox').scrollIntoView({ behavior: 'smooth' });\n    if (handoffError) {\n      alert(`DRAFTは保存しましたが、v0.4受信箱へ送信できませんでした。一覧から再送してください。\\n\\n${handoffError.message || handoffError}`);\n    }",
        "DRAFT-preserving handoff failure handling",
    )
    write("app.js", text)


def patch_human_review() -> None:
    path = "brand-intelligence/index.html"
    text = read(path)
    text = text.replace("v=0.4.4", "v=0.4.5")
    text = replace_once(
        text,
        ".btn.danger{background:#fff;color:var(--red);border-color:#d9b2aa}",
        ".btn.danger{background:#fff;color:var(--red);border-color:#d9b2aa}.btn:disabled{cursor:not-allowed;opacity:.55}",
        "disabled button style",
    )
    text = replace_once(
        text,
        "const WEAK_VALUES=new Set(['','unconfirmed','not_confirmed','candidate','inferred','unknown','Unknown','UNKNOWN']);",
        "const WEAK_VALUES=new Set(['','unconfirmed','not_confirmed','candidate','inferred','unknown','未確認','候補','推定']);",
        "weak status values",
    )
    text, escaped = re.subn(r"&quot(?=')", "&quot;", text, count=1)
    if escaped != 1 and "&quot;'" not in text:
        fail("could not fix HTML quote escaping")
    text = replace_once(
        text,
        "    const makeId=prefix=>`${prefix}-${uuid()}`;",
        "    const makeId=prefix=>`${prefix}-${uuid()}`;\n    const busyHandoffs=new Set();",
        "approval busy guard",
    )
    text = replace_once(
        text,
        "    function saveState(state){state.updated_at=now();state.server={workspaceId:'personal-owner',apiBase:location.origin,token:'',lastSyncAt:'',lastSyncStatus:'LOCAL_ONLY',syncMode:'LOCAL_ONLY',serverRevision:0,localRevision:0,...(state.server||{})};state.server.localRevision=Number(state.server.localRevision||0)+1;localStorage.setItem(V04_KEY,JSON.stringify(state))}",
        "    function saveState(state){state.updated_at=now();state.server={workspaceId:'personal-owner',apiBase:location.origin,token:'',lastSyncAt:'',lastSyncStatus:'LOCAL_ONLY',syncMode:'LOCAL_ONLY',serverRevision:0,localRevision:0,...(state.server||{})};state.server.localRevision=Number(state.server.localRevision||0)+1;localStorage.setItem(V04_KEY,JSON.stringify(state))}\n    function restoreStorage(key,raw){if(raw===null)localStorage.removeItem(key);else localStorage.setItem(key,raw)}\n    function saveApproval(state,queue){\n      const previousState=localStorage.getItem(V04_KEY),previousQueue=localStorage.getItem(HANDOFF_KEY);\n      const compacted=compactQueue(queue);\n      try{saveState(state);localStorage.setItem(HANDOFF_KEY,JSON.stringify(compacted))}\n      catch(error){\n        const rollbackErrors=[];\n        try{restoreStorage(V04_KEY,previousState)}catch(rollbackError){rollbackErrors.push(`マスター: ${rollbackError.message||rollbackError}`)}\n        try{restoreStorage(HANDOFF_KEY,previousQueue)}catch(rollbackError){rollbackErrors.push(`受信箱: ${rollbackError.message||rollbackError}`)}\n        throw new Error(`承認結果を保存できなかったため変更を元に戻しました: ${error.message||error}${rollbackErrors.length?`／復元失敗 ${rollbackErrors.join('、')}`:''}`);\n      }\n      return{saved:compacted.length,prunedReviewed:Math.max(0,queue.length-compacted.length)};\n    }",
        "atomic approval storage",
    )
    text = replace_once(
        text,
        "    function firstMeaningful(...values){return values.find(hasMeaningfulValue)}\n    function preferIncoming(incoming,existing,fallback=''){return firstMeaningful(incoming,existing,fallback)}\n    function preferStatus(incoming,existing,fallback='unconfirmed'){\n      const incomingText=String(incoming??'');const existingText=String(existing??'');\n      if(!hasMeaningfulValue(incoming))return preferIncoming(existing,fallback);\n      if(WEAK_VALUES.has(incomingText)&&hasMeaningfulValue(existing)&&!WEAK_VALUES.has(existingText))return existing;\n      return incoming;\n    }",
        "    function firstMeaningful(...values){return values.find(hasMeaningfulValue)}\n    function preferIncoming(incoming,existing,fallback=''){return firstMeaningful(incoming,existing,fallback)}\n    function normalizeStatus(value){return String(value??'').trim().toLowerCase()}\n    function isWeakStatus(value){return WEAK_VALUES.has(normalizeStatus(value))}\n    function preferStatus(incoming,existing,fallback='unconfirmed'){\n      if(!hasMeaningfulValue(incoming))return preferIncoming(existing,fallback);\n      if(isWeakStatus(incoming)&&hasMeaningfulValue(existing)&&!isWeakStatus(existing))return existing;\n      return incoming;\n    }",
        "normalized weak status protection",
    )
    text = replace_once(
        text,
        "const incomingStructure=WEAK_VALUES.has(String(payload.basicYarnForm||''))?payload.yarnStructure:firstMeaningful(payload.yarnStructure,payload.basicYarnForm);",
        "const incomingStructure=isWeakStatus(payload.basicYarnForm)?payload.yarnStructure:firstMeaningful(payload.yarnStructure,payload.basicYarnForm);",
        "normalized yarn form status",
    )
    text = replace_once(text, "      saveState(state);return ids;", "      return{ids,state};", "deferred master save")
    text = replace_once(
        text,
        "<button class=\"btn\" data-approve=\"${esc(item.handoff_id)}\">承認してマスター反映</button><button class=\"btn danger\" data-reject=\"${esc(item.handoff_id)}\">却下</button>",
        "<button class=\"btn\" data-approve=\"${esc(item.handoff_id)}\" ${busyHandoffs.has(item.handoff_id)?'disabled aria-disabled=\"true\"':''}>${busyHandoffs.has(item.handoff_id)?'処理中…':'承認してマスター反映'}</button><button class=\"btn danger\" data-reject=\"${esc(item.handoff_id)}\" ${busyHandoffs.has(item.handoff_id)?'disabled aria-disabled=\"true\"':''}>却下</button>",
        "approval button state",
    )
    new_approve = '''    function approve(handoffId){
      if(busyHandoffs.has(handoffId))return;
      const queue=loadQueue(),item=queue.find(row=>row.handoff_id===handoffId);if(!item||item.review_status!=='PENDING')return;
      const type=document.querySelector(`[data-type="${CSS.escape(handoffId)}"]`).value;
      const finalIdValue=document.querySelector(`[data-final-id="${CSS.escape(handoffId)}"]`).value.trim();
      const ok=confirm(`この候補をHuman Review承認し、商品・糸・会社マスターへ確定反映します。\\n\\n対象: ${TYPE_OPTIONS.find(row=>row[0]===type)?.[1]||type}\\n正式ID: ${finalIdValue||'自動採番'}\\n\\n続行しますか？`);if(!ok)return;
      busyHandoffs.add(handoffId);render();
      try{
        const promoted=promote(item,type,finalIdValue),ids=promoted.ids;
        item.review_status='APPROVED';item.reviewed_at=now();item.reviewed_by=$('reviewer').value.trim()||'Owner Human Review';item.master_ids=ids;
        const result=saveApproval(promoted.state,queue);
        try{localStorage.setItem(REVIEWER_KEY,$('reviewer').value.trim())}catch{}
        $('v04Frame').contentWindow.location.reload();
        setMessage(`承認しました。${Object.entries(ids).filter(([,value])=>typeof value==='string').map(([key,value])=>`${key}: ${value}`).join(' / ')||'マスター更新済み'}${result.prunedReviewed?`／古い承認済み・却下済み履歴${result.prunedReviewed}件を整理しました。`:''}`);
      }catch(error){setMessage(`承認処理に失敗しました: ${error.message||error}`,true)}
      finally{busyHandoffs.delete(handoffId);render()}
    }
'''
    text = replace_between(text, "    function approve(handoffId){", "    function reject(handoffId){", new_approve, "approve implementation")
    write(path, text)


def patch_versions_workflow_and_tests() -> None:
    index = read("index.html")
    index = index.replace("manifest.webmanifest?v=1.2.1", "manifest.webmanifest?v=1.2.2")
    index = index.replace("版: v1.2.1", "版: v1.2.2")
    index = index.replace("app.js?v=1.2.1", "app.js?v=1.2.2")
    write("index.html", index)

    sw = read("brand-intelligence/sw.js").replace("kc-brand-intelligence-v0-4-4", "kc-brand-intelligence-v0-4-5")
    write("brand-intelligence/sw.js", sw)

    workflow = read(".github/workflows/validate-system-registry.yml")
    workflow = replace_all(
        workflow,
        '      - "app.js"\n      - "app.css"',
        '      - "app.js"\n      - "app-state-guard.js"\n      - "app.css"',
        "app-state-guard registry workflow paths",
        minimum=2,
    )
    write(".github/workflows/validate-system-registry.yml", workflow)

    validator = read("scripts/validate_handoff_safety.py")
    marker = '    require(inline_script, "if(hasMeaningfulValue(value))existing[key]=value", "non-empty-only upsert")\n'
    additions = '''    require(app_text, "matchAll(/(\\d+(?:\\.\\d+)?)\\s*%/g)", "percentage-only composition total")
    require(app_text, "let handoffError = null", "DRAFT-preserving handoff failure handling")
    require(app_text, "DRAFTは保存しましたが、v0.4受信箱へ送信できませんでした", "handoff retry guidance")
    require(inline_script, "normalizeStatus", "normalized weak status protection")
    require(inline_script, "'未確認','候補','推定'", "Japanese weak statuses")
    require(inline_script, "saveApproval", "atomic approval storage")
    require(inline_script, "restoreStorage", "approval rollback")
    require(inline_script, "busyHandoffs", "duplicate approval guard")
    require(inline_script, "return{ids,state}", "deferred master save")
    forbid(inline_script, r"saveState\(state\);return ids", "one-sided approval save")
'''
    if additions not in validator:
        validator = replace_once(validator, marker, marker + additions, "final safety regression checks")
    write("scripts/validate_handoff_safety.py", validator)


def update_registry_and_docs() -> None:
    app_sha = git_blob("app.js")
    guard_sha = git_blob("app-state-guard.js")

    index = read("index.html")
    index = re.sub(r"Revision: [0-9a-f]{12}", f"Revision: {app_sha[:12]}", index, count=1)
    write("index.html", index)

    index_sha = git_blob("index.html")
    v04_index_sha = git_blob("brand-intelligence/index.html")
    v04_sw_sha = git_blob("brand-intelligence/sw.js")

    registry_path = ROOT / "config/system-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["schema_version"] = "1.2.2"
    registry["updated_at"] = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
    for system in registry["systems"]:
        if system["system_id"] == "KC-PHOTO-CAPTURE":
            system["display_version"] = "v1.2.2"
            system["code_revision"] = f"git-blob:{app_sha}"
            auxiliaries = system.setdefault("auxiliary_sources", [])
            guard = next((row for row in auxiliaries if row.get("code_source") == "app-state-guard.js@main"), None)
            if guard is None:
                guard = {"code_source": "app-state-guard.js@main", "code_revision": f"git-blob:{guard_sha}"}
                auxiliaries.insert(1, guard)
            else:
                guard["code_revision"] = f"git-blob:{guard_sha}"
            for source in auxiliaries:
                if source.get("code_source") == "index.html@main":
                    source["code_revision"] = f"git-blob:{index_sha}"
            system["storage_detail"] = (
                "IndexedDB kc_independent_photo_capture_v1_0; sessionStorage kc_session_v1; "
                "sessionStorage kc_photo_capture_editor_draft_v1 stores recoverable in-progress form values without photo blobs; "
                "localStorage kc_photo_capture_last_backup_v1 stores only the last backup timestamp; "
                "localStorage kc_v04_handoff_queue_v1 stores Human Review candidates without photo blobs; "
                "queue compaction retains all PENDING candidates; DRAFT remains saved when handoff storage fails"
            )
        elif system["system_id"] == "KC-V04-WEB":
            system["display_version"] = "v0.4.5"
            for source in system.get("auxiliary_sources", []):
                if source.get("code_source") == "brand-intelligence/index.html@main":
                    source["code_revision"] = f"git-blob:{v04_index_sha}"
                elif source.get("code_source") == "brand-intelligence/sw.js@main":
                    source["code_revision"] = f"git-blob:{v04_sw_sha}"
            system["storage_detail"] = (
                "localStorage kc_independent_practical_v0_4; Human Review inbox kc_v04_handoff_queue_v1; "
                "reviewer name kc_v04_reviewer_name_v1; partial approvals preserve existing values; "
                "temporary organization IDs stay stable; master and inbox approval results roll back together on storage failure"
            )
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = read("README.md").replace("Photo Capture v1.2.1", "Photo Capture v1.2.2").replace("Knit Compass v0.4.4", "Knit Compass v0.4.5")
    if "DRAFTを保持したまま再送" not in readme:
        readme = readme.replace(
            "- 保存容量不足時は未承認候補を黙って削除せず、保存失敗として表示します。",
            "- 保存容量不足時は未承認候補を黙って削除せず、保存失敗として表示します。\n- 受信箱保存に失敗してもDRAFTを保持したまま再送でき、TENCEL A100等の品名数字を混率へ誤加算しません。\n- Human Review承認はマスターと受信箱を一組で保存し、片側失敗時は両方を元に戻します。",
        )
    write("README.md", readme)

    handoff = read("docs/PHOTO_CAPTURE_HANDOFF.md").replace("版: 1.0.1", "版: 1.0.2")
    if "## 承認保存の一体性" not in handoff:
        handoff += "\n## 承認保存の一体性\n\nHuman Review承認では、マスター更新と受信箱のAPPROVED更新を一組として保存します。どちらかのlocalStorage書込みが失敗した場合は保存前の両方の値へ復元し、PENDINGのまま再確認できる状態を維持します。\n\nPhoto Capture側は受信箱保存に失敗しても先に保存したDRAFTを保持し、一覧から再送できます。混率合計は`%`付き数値だけを対象とし、`TENCEL A100`や`G100`の数字は加算しません。\n"
    write("docs/PHOTO_CAPTURE_HANDOFF.md", handoff)

    system_doc = read("docs/SYSTEM_REGISTRY.md")
    system_doc = system_doc.replace("版: 1.2.1", "版: 1.2.2").replace("`v1.2.1`", "`v1.2.2`").replace("`v0.4.4`", "`v0.4.5`")
    if "app-state-guard.js" not in system_doc:
        system_doc += "\n## Photo Capture UI状態ガード\n\n`app-state-guard.js`はPhoto Captureの正式な補助ソースです。保存中の二重操作防止、イベント版単位の送信済み判定、入力途中フォームのsessionStorage復元を担当し、接続台帳とRevision検証の対象に含めます。\n"
    if "片側保存" not in system_doc:
        system_doc += "\n## Human Review保存境界\n\nHuman Review承認はマスターと受信箱を一体で保存し、片側保存に失敗した場合は両方を保存前へ復元します。Production / Core / Company DBへの自動接続は追加しません。\n"
    write("docs/SYSTEM_REGISTRY.md", system_doc)


def main() -> None:
    patch_photo_capture()
    patch_human_review()
    patch_versions_workflow_and_tests()
    update_registry_and_docs()
    print("OK: applied final save and Human Review safety fixes")


if __name__ == "__main__":
    main()
