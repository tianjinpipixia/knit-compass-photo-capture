# 64ブランド日次軽量巡回 — 2026-08-18

## 実施範囲

- Issue #53のオーナー決定を反映し、アクティブBrand64の正本を `config/brand64-active-brands.json` に一本化。
- 旧10ブランド（RAGEBLUE / repipi armario / ALAND / CRAFT STANDARD BOUTIQUE / GARAGE OF GOOD CLOTHING / J.Press / 五大陸 / uncrave / #Newans / MATINEE LINE）はアクティブ監視から外し、過去観測・商品URL・根拠を削除せず `INACTIVE_LEGACY_REFERENCE` として保持。旧BR-IDは再利用しない。
- 代わりにPAL系10ブランドをBR-00065〜BR-00074で追加し、PAL CLOSET公式ブランドページと共通ニット入口を初回基準化。
- 2026-08-18の旧構成64行は履歴として保持したまま、アクティブ集計では旧10行を除外し、`2026-08-18-pal10-daily.jsonl` の新規10行を重ねて**アクティブ64件**とする。
- 販売数量は一次根拠がないため全件 `NOT_AVAILABLE`、推定なし。同一URL/同一品番は重複追加しない。PUBLISH_HOLD / HUMAN_REVIEW_REQUIREDを維持。

## 新規PAL10ブランド — 初回鮮度回復

1. **GALLARDAGALANTE** — 公式PALページでNEW ARRIVAL / PRE ORDER / RANKING / NEWS導線を現行確認。初秋予約・シアー系の公式特集を基準化。
2. **Whim Gazette** — 2026AW THE PAUSEでスラブニットカーディガン¥20,900予約、MIXヤーンカーディガン¥18,700等を確認。
3. **LOUNGEDRESS** — PRE ORDER / PRE FALL COLLECTION / NEW LOOK / SALE入口を基準化。
4. **RIVE DROITE** — PRE ORDER / NEW ARRIVAL / 人気ランキング / SPECIAL PRICE入口を基準化。
5. **DOUDOU** — 新作 / SALE / MONTHLY RANKING / 先取りSTYLE BOOK入口を基準化。
6. **SHENERY** — 2026 PRE FALL ORDER EVENT、NEW PRE ORDER、Weekly / Monthly Ranking入口を基準化。
7. **un dix cors** — メッシュスリーブプルオーバー¥5,940、強撚ミックスラメトッパー¥5,500、UVドルマンニットのSALE等を確認。
8. **La boutique BonBon** — ヘアリーフェザー前後2WAYフレンチニット¥11,550予約、ラメペプラム前後2WAYカーデ¥17,820予約、ロングフェザーベルリボンニット¥14,850予約等を確認。
9. **natural couture** — UV / 接触冷感 / 吸水速乾の機能特集、異素材ペプラム半袖ニットSALE、秋先取り新着/予約導線を基準化。
10. **DISCOAT** — EARLY AUTUMN / PRE ORDER / SALE / RANKINGを基準化。WEB限定前後2wayシャギー系予約など秋先取り表面感を確認。

PAL共通ニット入口:
`https://www.palcloset.jp/display/display/?mode=zSearch&SearchItem.SORT_KEY=POPULARITY_DESC&b=&sex=&c=1104,1105&type=01`

## 既存アクティブブランドの鮮度回復

- 前日まで鮮度不足だった既存ブランドではUNIQLO / GU / MUJI / ikka / any SiS / 23区 / ICB / 自由区 / 組曲 / UNTITLED / B.C STOCK / SLOBE IENA / Mila Owen等の公式入口・索引を再取得し、商品比較基準を更新。
- **green label relaxing** はカテゴリ鮮度を回復したが、商品名・品番・混率の直接商品ページ取得がまだ不足。
- **AMERICAN HOLIC `0H001683000`** は公式系ソース間の価格状態競合を維持し、ライブ商品ページ確定前は上書きしない。
- **UNFILO `KRUMSW0424`** も¥3,995・50%OFF保全値と¥2,396・70%OFF/SOLD OUT索引が時系列競合しているため、ライブ状態確定前は当日差分と扱わない。
- **ROPÉ PICNIC** 新規3商品は発見時の価格/予約状態を保持したが、直接商品URL・品番・混率は次回補完。

## 本日の重要MD差分

- **残暑機能の意匠化**: 既存ブランドに加え、natural couture / un dix corsでもUV・冷感・強撚・メッシュ等の端境期機能を着映え方向へつなぐ動きが確認できる。
- **軽量毛羽・表面感の拡大**: Whim Gazette / La boutique BonBon / DISCOATの追加で、スラブ、MIX、フェザー、シャギー、2WAYなど秋表面感の比較レンジが広がった。
- **予約/ランキングの先行性**: PAL系はPRE ORDERとランキング導線が明確で、週次MDでは人気順変化を素材・型の先行シグナルとして使える。
- **上質ハイゲージの外衣化**: IÉNA / ROPÉ / Mila Owen / Whim Gazette等の比較から、細番手〜中肉の上質見えニットをカーデ、ポロ、ZIP、ジレへ外衣化する流れを継続監視する。

## 素材開発への示唆

- 14G/16G: 接触冷感・UV・吸水速乾・抗ピル・洗えるを、秋色、配色、ペプラム、襟、ラメ、メッシュ等の意匠へ載せる。
- 10G〜12G: 軽量フェザー / シャギー / モヘヤ / ブークレ / MIXヤーンを、ウォッシャブル・静電気軽減・抗ピルと組み合わせる。
- 16G〜18G: メリノ / カシミヤ / シルク混、レーヨン/ナイロン等の細番手を、ポロ・金釦・ZIP・ジャケット/ジレ向けに展開。
- PAL系は日次で新着・予約・SALE・ランキングを軽量確認し、週次では人気順変化をブランド別MDへ集約する。
- 新規商品は初回発見時に商品URL・品番・通常/SALE価格・混率・機能・色・予約状態を優先保存し、未取得項目は推定せず次回補完する。

Publication: **PUBLISH_HOLD / HUMAN_REVIEW_REQUIRED**
