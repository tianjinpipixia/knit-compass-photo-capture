#!/usr/bin/env python3
"""Apply the second safety pass to PR #16 without rewriting unrelated files."""
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


def replace_regex(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count == 1:
        return updated
    if replacement in text:
        return text
    fail(f"could not replace {label}")


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
    path = "app.js"
    text = read(path)
    text = replace_once(text, "const APP_VERSION = '1.2.1';", "const APP_VERSION = '1.2.2';", "Photo Capture version")
    text = replace_once(text, "  let submitMode = 'draft';\n", "  let submitMode = 'draft';\n  let saveInProgress = false;\n", "save guard state")
    text = replace_once(
        text,
        "  function latestHandoffForCapture(captureId) {\n    return handoffQueue().find((item) => item.capture_id === captureId) || null;\n  }",
        "  function handoffForEvent(eventRow) {\n    const dedupeKey = `${eventRow.recordId}:${eventRow.version}`;\n    return handoffQueue().find((item) => item.dedupe_key === dedupeKey) || null;\n  }",
        "event-specific handoff lookup",
    )
    text = replace_once(
        text,
        "      const handoff = latestHandoffForCapture(row.captureId || event.recordId);\n      const status = handoff?.review_status || '未送信';",
        "      const handoff = handoffForEvent(event);\n      const status = handoff?.review_status || '未送信';\n      const alreadySent = Boolean(handoff);",
        "event-specific status",
    )
    text = replace_once(
        text,
        "<div class=\"actions\"><button class=\"secondary\" data-edit=\"${escapeHtml(event.recordId)}\">編集・再保存</button><button data-send=\"${escapeHtml(event.recordId)}\">v0.4受信箱へ送る</button></div>",
        "<div class=\"actions\"><button class=\"secondary\" data-edit=\"${escapeHtml(event.recordId)}\">編集・再保存</button><button data-send=\"${escapeHtml(event.recordId)}\" ${alreadySent ? 'disabled aria-disabled=\"true\"' : ''}>${alreadySent ? 'この版は送信済み' : 'v0.4受信箱へ送る'}</button></div>",
        "disable already-sent button",
    )
    text = replace_once(
        text,
        "    document.getElementById('saveAndSend').addEventListener('click', () => {\n      submitMode = 'send';\n      form.requestSubmit();\n    });\n    form.addEventListener('submit', saveCapture);",
        "    document.getElementById('saveDraft').addEventListener('click', () => {\n      submitMode = 'draft';\n    });\n    document.getElementById('saveAndSend').addEventListener('click', () => {\n      submitMode = 'send';\n      form.requestSubmit();\n    });\n    form.addEventListener('invalid', () => {\n      submitMode = 'draft';\n    }, true);\n    form.addEventListener('submit', saveCapture);",
        "submit-mode reset",
    )
    text = replace_once(
        text,
        "    const values = [...String(text || '').matchAll(/(\\d+(?:\\.\\d+)?)\\s*%?/g)].map((match) => Number(match[1]));",
        "    const values = [...String(text || '').matchAll(/(\\d+(?:\\.\\d+)?)\\s*%/g)].map((match) => Number(match[1]));",
        "composition parser",
    )
    text = replace_once(
        text,
        "      messageElement.textContent = '数値を入力すると合計を確認します。';",
        "      messageElement.textContent = /\\d/.test(String(text || '')) ? '合計確認する数値には%を付けてください。' : '数値を入力すると合計を確認します。';",
        "composition guidance",
    )

    new_save_capture = r'''  async function saveCapture(event) {
    event.preventDefault();
    if (saveInProgress) return;

    const form = event.currentTarget;
    const message = document.getElementById('editMessage');
    const saveButtons = [...form.querySelectorAll('#saveDraft,#saveAndSend')];
    saveInProgress = true;
    saveButtons.forEach((button) => {
      button.disabled = true;
      button.setAttribute('aria-disabled', 'true');
    });

    try {
      const targetType = form.targetType.value;
      const targetId = form.targetId.value.trim() || editing?.snapshot?.targetId || temporaryCommonId(targetType);
      const recordId = editing?.recordId || internalId('KCI-CAPTURE');
      const existingPhotoRefs = [...(editing?.snapshot?.photoRefs || [])];
      const newPhotoRefs = [];
      const photoRows = [];

      for (const [type, label] of PHOTO_TYPES) {
        const file = pendingPhotos[type];
        if (!file) continue;
        const photoId = `TMP-PH-${uuid()}`;
        const capturedAt = nowIso();
        newPhotoRefs.push({ photoId, type, label, fileName: file.name, capturedAt });
        photoRows.push({ photoId, recordId, targetId, type, label, fileName: file.name, blob: file, capturedAt });
      }
      const replacedTypes = new Set(newPhotoRefs.map((reference) => reference.type));
      const photoRefs = [...existingPhotoRefs.filter((reference) => !replacedTypes.has(reference.type)), ...newPhotoRefs];

      const composition = parseComposition(form.compositionRaw.value);
      const functionCodes = checkedValues(form, 'functionCodes');
      const sustainableCodes = checkedValues(form, 'sustainableCodes');
      const captureId = editing?.snapshot?.captureId || recordId;
      const snapshot = {
        dataContractVersion: DATA_CONTRACT_VERSION,
        captureId,
        priority: form.priority.value,
        targetType,
        targetId,
        commonIds: normalizeCommonIds(targetType, targetId, form),
        sourceOrganizationName: form.sourceOrganizationName.value.trim(),
        sourceOrganizationId: form.sourceOrganizationId.value.trim(),
        manufacturerName: form.manufacturerName.value.trim(),
        manufacturerId: form.manufacturerId.value.trim(),
        sellerName: form.sellerName.value.trim(),
        sellerId: form.sellerId.value.trim(),
        brandName: form.brandName.value.trim(),
        productName: form.productName.value.trim(),
        productCode: form.productCode.value.trim(),
        productUrl: form.productUrl.value.trim(),
        yarnName: form.yarnName.value.trim(),
        yarnCode: form.yarnCode.value.trim(),
        countSystem: form.countSystem.value,
        countValue: form.countValue.value.trim(),
        countDisplay: form.countDisplay.value.trim(),
        gauge: form.gauge.value.trim(),
        basicYarnForm: form.basicYarnForm.value,
        yarnStructure: form.yarnStructure.value.trim(),
        spinningMethod: form.spinningMethod.value,
        processingMethod: form.processingMethod.value.trim(),
        compositionRaw: form.compositionRaw.value.trim(),
        compositionTotal: composition.values.length ? composition.total : null,
        compositionStatus: form.compositionStatus.value,
        functionalProperties: propertyItems(functionCodes, FUNCTION_OPTIONS, form.functionClaimStatus.value, form.functionDetail.value.trim(), { test: form.functionTest.value.trim() }),
        functionClaimStatus: form.functionClaimStatus.value,
        functionDetail: form.functionDetail.value.trim(),
        functionTest: form.functionTest.value.trim(),
        sustainableAttributes: propertyItems(sustainableCodes, SUSTAINABLE_OPTIONS, form.sustainableStatus.value, form.sustainableBasis.value.trim(), { certification: form.certification.value.trim() }),
        sustainableStatus: form.sustainableStatus.value,
        sustainableBasis: form.sustainableBasis.value.trim(),
        certification: form.certification.value.trim(),
        seasons: checkedValues(form, 'season'),
        documentType: form.documentType.value,
        sourceType: form.sourceType.value,
        sourceUrl: form.sourceUrl.value.trim(),
        verificationStatus: form.verificationStatus.value,
        evidenceId: form.evidenceId.value.trim(),
        notes: form.notes.value.trim(),
        photoRefs
      };

      const meaningful = photoRefs.length || snapshot.yarnName || snapshot.productName
        || snapshot.sourceOrganizationName || snapshot.compositionRaw || snapshot.notes;
      if (!meaningful) {
        if (message) message.textContent = '写真または対象情報を入力してください。';
        return;
      }

      const timestamp = nowIso();
      const eventRow = {
        eventId: internalId('KCI-EVENT'),
        recordId,
        version: editing ? Number(editing.version) + 1 : 1,
        eventType: editing ? 'UPDATE' : 'CREATE',
        dataState: 'DRAFT',
        createdAt: editing?.createdAt || timestamp,
        updatedAt: timestamp,
        actorId: session.accountId,
        snapshot
      };

      const transaction = db.transaction(['events', 'photos'], 'readwrite');
      transaction.objectStore('events').add(eventRow);
      photoRows.forEach((row) => transaction.objectStore('photos').add(row));
      await transactionPromise(transaction);

      let handoffError = null;
      if (submitMode === 'send') {
        try {
          enqueueHandoff(eventRow);
        } catch (error) {
          handoffError = error;
        }
      }

      editing = null;
      await renderApp();
      document.getElementById('inbox').scrollIntoView({ behavior: 'smooth' });
      if (handoffError) {
        alert(`DRAFTは保存しましたが、v0.4受信箱へ送信できませんでした。一覧から再送してください。\n\n${handoffError.message || handoffError}`);
      }
    } catch (error) {
      if (message) {
        message.textContent = `保存できませんでした: ${error.message || error}`;
        message.classList.add('error');
      } else {
        alert(`保存できませんでした: ${error.message || error}`);
      }
    } finally {
      submitMode = 'draft';
      saveInProgress = false;
      if (document.body.contains(form)) {
        saveButtons.forEach((button) => {
          button.disabled = false;
          button.removeAttribute('aria-disabled');
        });
      }
    }
  }
'''
    text = replace_regex(
        text,
        r"  async function saveCapture\(event\) \{.*?\n  \}\n\n  function sanitizeForHandoff",
        new_save_capture + "\n  function sanitizeForHandoff",
        "saveCapture implementation",
    )
    text = replace_once(
        text,
        "    if (queue.some((item) => item.dedupe_key === dedupeKey)) return;",
        "    if (queue.some((item) => item.dedupe_key === dedupeKey)) return false;",
        "handoff duplicate return",
    )
    text = replace_once(
        text,
        "    saveHandoffQueue(queue);\n  }",
        "    saveHandoffQueue(queue);\n    return true;\n  }",
        "handoff success return",
    )
    write(path, text)


def patch_v04() -> None:
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
        "weak status set",
    )
    text = replace_once(
        text,
        "const esc=value=>String(value??'').replace(/[&<>\\\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\\"':'&quot',\"'\":'&#039;'}[c]));",
        "const esc=value=>String(value??'').replace(/[&<>\\\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\\"':'&quot;',\"'\":'&#039;'}[c]));",
        "HTML quote escaping",
    )
    text = replace_once(
        text,
        "    const makeId=prefix=>`${prefix}-${uuid()}`;",
        "    const makeId=prefix=>`${prefix}-${uuid()}`;\n    const busyHandoffs=new Set();",
        "busy approval guard",
    )
    text = replace_once(
        text,
        "    function saveState(state){state.updated_at=now();state.server={workspaceId:'personal-owner',apiBase:location.origin,token:'',lastSyncAt:'',lastSyncStatus:'LOCAL_ONLY',syncMode:'LOCAL_ONLY',serverRevision:0,localRevision:0,...(state.server||{})};state.server.localRevision=Number(state.server.localRevision||0)+1;localStorage.setItem(V04_KEY,JSON.stringify(state))}",
        "    function saveState(state){state.updated_at=now();state.server={workspaceId:'personal-owner',apiBase:location.origin,token:'',lastSyncAt:'',lastSyncStatus:'LOCAL_ONLY',syncMode:'LOCAL_ONLY',serverRevision:0,localRevision:0,...(state.server||{})};state.server.localRevision=Number(state.server.localRevision||0)+1;localStorage.setItem(V04_KEY,JSON.stringify(state))}\n    function restoreStorage(key,raw){if(raw===null)localStorage.removeItem(key);else localStorage.setItem(key,raw)}\n    function saveApproval(state,queue){\n      const previousState=localStorage.getItem(V04_KEY),previousQueue=localStorage.getItem(HANDOFF_KEY);\n      const compacted=compactQueue(queue);\n      try{saveState(state);localStorage.setItem(HANDOFF_KEY,JSON.stringify(compacted))}\n      catch(error){\n        const rollbackErrors=[];\n        try{restoreStorage(V04_KEY,previousState)}catch(rollbackError){rollbackErrors.push(`マスター: ${rollbackError.message||rollbackError}`)}\n        try{restoreStorage(HANDOFF_KEY,previousQueue)}catch(rollbackError){rollbackErrors.push(`受信箱: ${rollbackError.message||rollbackError}`)}\n        throw new Error(`承認結果を保存できなかったため変更を元に戻しました: ${error.message||error}${rollbackErrors.length?`／復元失敗 ${rollbackErrors.join('、')}`:''}`);\n      }\n      return{saved:compacted.length,prunedReviewed:Math.max(0,queue.length-compacted.length)};\n    }",
        "atomic approval save",
    )
    text = replace_once(
        text,
        "    function firstMeaningful(...values){return values.find(hasMeaningfulValue)}\n    function preferIncoming(incoming,existing,fallback=''){return firstMeaningful(incoming,existing,fallback)}\n    function preferStatus(incoming,existing,fallback='unconfirmed'){\n      const incomingText=String(incoming??'');const existingText=String(existing??'');\n      if(!hasMeaningfulValue(incoming))return preferIncoming(existing,fallback);\n      if(WEAK_VALUES.has(incomingText)&&hasMeaningfulValue(existing)&&!WEAK_VALUES.has(existingText))return existing;\n      return incoming;\n    }",
        "    function firstMeaningful(...values){return values.find(hasMeaningfulValue)}\n    function preferIncoming(incoming,existing,fallback=''){return firstMeaningful(incoming,existing,fallback)}\n    function normalizeStatus(value){return String(value??'').trim().toLowerCase()}\n    function isWeakStatus(value){return WEAK_VALUES.has(normalizeStatus(value))}\n    function preferStatus(incoming,existing,fallback='unconfirmed'){\n      if(!hasMeaningfulValue(incoming))return preferIncoming(existing,fallback);\n      if(isWeakStatus(incoming)&&hasMeaningfulValue(existing)&&!isWeakStatus(existing))return existing;\n      return incoming;\n    }",
        "normalized status preference",
    )
    text = replace_once(
        text,
        "const incomingStructure=WEAK_VALUES.has(String(payload.basicYarnForm||''))?payload.yarnStructure:firstMeaningful(payload.yarnStructure,payload.basicYarnForm);",
        "const incomingStructure=isWeakStatus(payload.basicYarnForm)?payload.yarnStructure:firstMeaningful(payload.yarnStructure,payload.basicYarnForm);",
        "normalized yarn form check",
    )
    text = replace_once(text, "      saveState(state);return ids;", "      return{ids,state};", "deferred master save")
    text = replace_once(
        text,
        "<button class=\"btn\" data-approve=\"${esc(item.handoff_id)}\">承認してマスター反映</button><button class=\"btn danger\" data-reject=\"${esc(item.handoff_id)}\">却下</button>",
        "<button class=\"btn\" data-approve=\"${esc(item.handoff_id)}\" ${busyHandoffs.has(item.handoff_id)?'disabled aria-disabled=\"true\"':''}>${busyHandoffs.has(item.handoff_id)?'処理中…':'承認してマスター反映'}</button><button class=\"btn danger\" data-reject=\"${esc(item.handoff_id)}\" ${busyHandoffs.has(item.handoff_id)?'disabled aria-disabled=\"true\"':''}>却下</button>",
        "approval button guard",
    )

    new_approve = r'''    function approve(handoffId){
      if(busyHandoffs.has(handoffId))return;
      const queue=loadQueue(),item=queue.find(row=>row.handoff_id===handoffId);if(!item||item.review_status!=='PENDING')return;
      const type=document.querySelector(`[data-type="${CSS.escape(handoffId)}"]`).value;
      const finalIdValue=document.querySelector(`[data-final-id="${CSS.escape(handoffId)}"]`).value.trim();
      const ok=confirm(`この候補をHuman Review承認し、商品・糸・会社マスターへ確定反映します。\n\n対象: ${TYPE_OPTIONS.find(row=>row[0]===type)?.[1]||type}\n正式ID: ${finalIdValue||'自動採番'}\n\n続行しますか？`);if(!ok)return;
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
    text = replace_regex(
        text,
        r"    function approve\(handoffId\)\{.*?\n    \}\n    function reject",
        new_approve + "    function reject",
        "atomic approve implementation",
    )
    write(path, text)


def patch_versions_and_tests() -> None:
    index = read("index.html")
    index = index.replace("v=1.2.1", "v=1.2.2").replace("版: v1.2.1", "版: v1.2.2")
    write("index.html", index)

    sw = read("brand-intelligence/sw.js").replace("kc-brand-intelligence-v0-4-4", "kc-brand-intelligence-v0-4-5")
    write("brand-intelligence/sw.js", sw)

    validator = read("scripts/validate_handoff_safety.py")
    additions = """    require(app_text, \"handoffForEvent\", \"event-version-specific handoff status\")\n    require(app_text, \"saveInProgress\", \"Photo Capture duplicate-save guard\")\n    require(app_text, \"matchAll(/(\\\\d+(?:\\\\.\\\\d+)?)\\\\s*%/g)\", \"percentage-only composition total\")\n    require(inline_script, \"normalizeStatus\", \"normalized weak status protection\")\n    require(inline_script, \"saveApproval\", \"atomic approval storage\")\n    require(inline_script, \"busyHandoffs\", \"duplicate approval guard\")\n"""
    marker = "    require(inline_script, \"if(hasMeaningfulValue(value))existing[key]=value\", \"non-empty-only upsert\")\n"
    if additions not in validator:
        validator = replace_once(validator, marker, marker + additions, "follow-up validation checks")
    write("scripts/validate_handoff_safety.py", validator)


def update_registry_and_docs() -> None:
    app_sha = git_blob("app.js")
    root_index_sha = git_blob("index.html")
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
            for source in system.get("auxiliary_sources", []):
                if source.get("code_source") == "index.html@main":
                    source["code_revision"] = f"git-blob:{root_index_sha}"
            system["storage_detail"] = (
                "IndexedDB kc_independent_photo_capture_v1_0; sessionStorage kc_session_v1; "
                "localStorage kc_photo_capture_last_backup_v1 stores only the last backup timestamp; "
                "localStorage kc_v04_handoff_queue_v1 stores Human Review candidates without photo blobs; "
                "queue compaction retains all PENDING candidates; each event version is sent once and save buttons are guarded against duplicate submission"
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

    index = read("index.html")
    index = re.sub(r"Revision: [0-9a-f]{12}", f"Revision: {app_sha[:12]}", index, count=1)
    write("index.html", index)
    root_index_sha = git_blob("index.html")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for system in registry["systems"]:
        if system["system_id"] == "KC-PHOTO-CAPTURE":
            for source in system.get("auxiliary_sources", []):
                if source.get("code_source") == "index.html@main":
                    source["code_revision"] = f"git-blob:{root_index_sha}"
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    readme = read("README.md").replace("Photo Capture v1.2.1", "Photo Capture v1.2.2").replace("Knit Compass v0.4.4", "Knit Compass v0.4.5")
    if "同じイベント版の送信ボタンは送信後に無効化" not in readme:
        readme = readme.replace(
            "- 保存容量不足時は未承認候補を黙って削除せず、保存失敗として表示します。",
            "- 保存容量不足時は未承認候補を黙って削除せず、保存失敗として表示します。\n- 同じイベント版の送信ボタンは送信後に無効化し、保存・承認処理の連打を防止します。\n- Human Review承認時はマスターと受信箱を一組として保存し、片側だけ失敗した場合は元に戻します。",
        )
    write("README.md", readme)

    handoff = read("docs/PHOTO_CAPTURE_HANDOFF.md").replace("版: 1.0.1", "版: 1.0.2")
    if "承認保存の一体性" not in handoff:
        handoff += "\n## 承認保存の一体性\n\nHuman Review承認では、マスター更新と受信箱のAPPROVED更新を一組として保存します。どちらかのlocalStorage書込みが失敗した場合は、保存前の両方の値へ復元し、PENDINGのまま再確認できる状態を維持します。\n\n同じPhoto Captureイベント版は一度だけ受信箱へ送信でき、送信後のボタンは無効化します。保存・承認ボタンも処理中は無効化して二重実行を防止します。\n"
    write("docs/PHOTO_CAPTURE_HANDOFF.md", handoff)

    system_doc = read("docs/SYSTEM_REGISTRY.md")
    system_doc = system_doc.replace("版: 1.2.1", "版: 1.2.2").replace("`v1.2.1`", "`v1.2.2`").replace("`v0.4.4`", "`v0.4.5`")
    system_doc = re.sub(r"git-blob:[0-9a-f]{12,40}", lambda m: m.group(0), system_doc)
    if "片側保存" not in system_doc:
        system_doc = system_doc.replace(
            "### 会社IDの固定",
            "### 承認保存の一体性\n\nHuman Review承認ではマスターと受信箱を一組として保存し、片側保存に失敗した場合は両方を保存前へ復元します。Photo Capture側はイベント版単位で送信済みを判定し、同じ版の再送信と保存連打を防止します。\n\n### 会社IDの固定",
        )
    write("docs/SYSTEM_REGISTRY.md", system_doc)


def main() -> None:
    patch_photo_capture()
    patch_v04()
    patch_versions_and_tests()
    update_registry_and_docs()
    print("OK: applied PR #16 follow-up safety fixes")


if __name__ == "__main__":
    main()
