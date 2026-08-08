# 2026-08-08 威海2社 Human Review 取込 — Batch 2

Batch ID: `KC-MANUAL-20260808-BATCH2-WEIHAI-YAXIN-CHENGYUN`

## 登録対象

1. 威海雅信纺织服装有限公司  
   English: WEIHAI YAXIN TEXTILE & GARMENTS CO., LTD.  
   Type: knitwear_manufacturer

2. 威海诚韵国际贸易有限公司  
   English: WEIHAI CHENGYUN INTERNATIONAL TRADE CO., LTD.  
   Type: trading_company

2社は別 `targetId` / `sourceOrganizationId` とし、同一会社へ統合しない。

## 会社関係の扱い

現行公式サイトは雅信を诚韵に `subordinate` と表現している。一方、Knit Compassでは資本関係の根拠を別途確認していないため、会社マスター上は次の扱いとする。

- `relationshipType`: `operationally_related`
- `capitalRelationshipStatus`: `unconfirmed`
- `parentDirectionStatus`: `not_asserted_in_master`

公式サイトの表現は業務上の関係根拠として保持するが、親会社・子会社の資本関係を自動確定しない。

## 担当者

- 丁晓威
- WeChat: `W102761652`
- 雅信への所属: confirmed_with_yaxin
- 诚韵への所属: related_contact_only_not_confirmed_employee_of_chengyun

## 連絡先

公式サイト確認値:

- Website: `https://www.cheng-yun.com/`
- Email: `nq.wang@cheng-yun.com`
- Tel: `86-631-5990269` / `86-631-5928829`
- Address: A1313, NO.23 BLUE STAR BUILDING, ECONOMIC TECHNICAL DEVELOPMENT ZONE, WEIHAI CHINA

ユーザー提供資料の履歴値:

- 诚韵 Email: `admin@cheng-yun.com`

履歴値で現行公式メールを上書きしない。

## 事業情報

### 威海雅信

- founded 2009
- knitwear manufacturer
- official site equipment: 12G / 7G / 5G / 3G
- BSCI claim on company site
- current regenagri certified-companies listing also identifies Weihai Yaxin Textile & Garments Co., Ltd. (CU-1482706)

### 威海诚韵

- founded 2004 according to the shared official company site
- international trading company
- official site describes target markets as Japan / Europe / America

## 関連素材・資料

Linked materials:

- THERMO WALKER®
- WARMPLUS-R

Linked documents:

- WARMPLUS-R吸湿発熱2019.pdf
- WARMPLUS-R抗ピリング.pdf
- QD-24-072239.pdf

これらは会社プロフィールの `linkedMaterials` / `linkedDocuments` と `notes` に保持する。

## Human Reviewでの保存

各itemは `targetType=organization` に加え `commonIds.researchId` を持つ。現行Human Reviewでは承認時に:

- 会社・組織マスターへ正式OR-IDで登録
- 同時に調査記録を作成し、`notes` をcandidateAnswer / verifiedFactsとして保持

とする。会社マスター本体の担当者専用フィールドは現行v0.4にないため、担当者・関係・資料詳細は調査記録と元のintake payloadを正本補助として保持する。

## 安全境界

- 2社は別会社として登録する
- 丁晓威を诚韵社員とは確定しない
- 雅信↔诚韵の資本親子関係を確定しない
- 公式サイトの `subordinate` 表現は関係根拠としてのみ記録する
- Human Review前にブラウザ内V04マスターへ直接書き込まない
