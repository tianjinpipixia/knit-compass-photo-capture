# Sales Story v1

## 目的
「市場で何が起きているか」→「どの素材・糸で応えるか」→「営業が何を伝えるか」を1本につなぐ。

## Story構造
1. Market Signal
2. Market Evidence
3. 提案素材・糸
4. 確認済み機能・サステナブル
5. Sales Angle
6. 必須確認
7. リスク・境界

## 初版3テーマ
### SS-T01 残暑の秋立ち上がり：秋見え×夏機能
NATURAL BEAUTY BASIC 2026FWの薄手ボレロで、秋立ち上がりにUV・接触冷感・マシンウォッシャブルが併存する実例を市場根拠にする。

### SS-T02 Non-Wool Mélange：非ウールで秋冬TOP調
綿・レーヨン・リヨセル等で杢・TOP調を表現し、早い時期から秋冬感を出す。実際の染色・紡績方式は別確認する。

### SS-T03 高捻コアスパン：シャリ感＋形態安定
R80/Polyester20の高捻コアスパン候補を起点に、春夏細番手のドライタッチ＋安定性を提案。ただしPET/PBTの区別を確認後に確定する。

## ガードレール
- 販売数量は根拠がある場合のみ。推定禁止。
- 未確認機能をSales Storyで断定しない。
- 候補素材はcandidate表示を残す。
- 競合商品は市場根拠であり、仕様コピーの根拠にしない。
- 顧客別文章はHuman Reviewを通す。

## Generator
`window.KnitCompassSalesStory.generate(...)` はテンプレート＋Knit Compassのmaterial/yarn/productを組み合わせ、Markdownの営業ストーリーを作る。
