# Materials DB v1

## 目的
Knit Compassの「素材」を、糸・商品とは別のマスターとして扱う。素材は原料、ブランド繊維、ポリマー、フィラメント、機能剤、機能技術、染色・仕上げ、加工技術を含む。

## 境界
- Material identity と Yarn identity を分離する。
- 商標・ブランド名と一般素材名を分離する。
- 商品名・商標から混率を推定しない。
- 機能は evidence status を持ち、未確認の主張を製品へ自動継承しない。
- メーカーと販売会社の役割を分離する。
- Human Review前に confirmed master へ昇格しない。

## Material Type
`fiber_generic / branded_fiber / polymer / filament / functional_additive / functional_technology / dye_finish / processing_technology / other`

## 糸・商品との関係
`bulk / core / sheath / cover / plating / blend_component / finish / additive / technology / unknown`

例:
- ICEJADE 70D/68F → filament / plating
- Sorona® → branded_fiber / blend_component
- PCM技術 → functional_technology / technology
- UV吸収剤 → functional_additive / additive

## 既存データ移行
既存 `state.materials[]` の `name / composition / functionalProperties / sustainableAttributes` は保持し、不足項目は `other / unknown / unconfirmed` で補完する。既存IDを変更しない。

## 運用
1. Photo Capture / Human Reviewで候補を受ける。
2. Material Masterで一般名・商標・メーカー・形態を整理する。
3. 糸との関係（芯・カバー・プレーティング等）を紐付ける。
4. 試験・公式資料のevidenceを登録する。
5. Sales Storyではconfirmed evidenceだけを断定表現に使う。
