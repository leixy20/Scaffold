
# 大規模マルチモーダルモデルにおける視覚言語調整を促進するための足場座標

このリポジトリには、私たちの論文「大規模マルチモーダルモデルにおける視覚言語調整を促進するための足場座標」の情報、データ、コードが含まれています。

## 🔥 最新情報

[2024.02.22] 標準的なScaffoldプロンプティングを視覚言語タスクに適用するためのコードをリリースしました。

## 📍 はじめに

最先端の大規模マルチモーダルモデル（LMMs）は、視覚言語タスクにおいて優れた能力を示しています。高度な機能にもかかわらず、複数レベルの視覚情報を用いた複雑な推論が必要とされる困難なシナリオでは、LMMsのパフォーマンスはまだ限定的です。LMMsの既存のプロンプティング技術は、テキストによる推論の改善または画像前処理のためのツールの活用に焦点を当てており、LMMsにおける視覚言語調整を促進するシンプルで汎用的な視覚プロンプティング手法が欠けています。本研究では、視覚言語調整を促進するための足場となる座標をスキャフォールドするScaffoldプロンプティングを提案します。具体的には、Scaffoldは画像内にドットマトリックスを視覚情報のアンカーとして重ね合わせ、多次元座標をテキストの位置参照として活用します。様々な難しい視覚言語タスクでの広範な実験により、テキストのCoTプロンプティングを用いたGPT-4Vに対するScaffoldの優位性が実証されました。

![overall](https://raw.githubusercontent.com/Sunwood-ai-labs/Scaffold-JP/main/assets/overall.jpg)

Scaffoldの全体的なフレームワークを上図に示し、視覚言語調整を促進するための全体的なアプローチを説明しています。

Scaffoldの詳細については、論文を参照してください：[Scaffold](https://arxiv.org/abs/2402.12058)

---

## 📦 クイックスタート

ここでは、GPT-4Vを使用して、Scaffoldプロンプティングを視覚言語タスクに適用するためのクイックガイドを紹介します。サンプルの質問と正解は `data/examples/example.jsonl` に、対応する画像は `data/examples/imgs` に配置されています。

**ステップ0** 準備。

以下のコマンドを実行して、必要なモジュールをインストールする必要があります。

```bash
pip install -r requirements.txt
```

Scaffoldプロンプティングを独自のデータに適用したい場合は、データを `data/examples/example.jsonl` のサンプルと同じ形式で整理する必要があります。有効なサンプルの例は次のとおりです。

```python
{
  "question_id": 1, 
  "image_path": "data/examples/imgs/1.jpg", 
  "question": "次の文が正しいか誤っているかを判断してください：人はバナナに向かっている。", 
  "answer": 1
}
```

そして、`image_path` で指定したパスに画像を配置する必要があります。

**ステップ1** 画像の処理。

以下のコマンドを実行することで、元の画像にドットマトリックスと座標を重ね合わせることができます。

```bash
python image_processor.py
```

注意：私たちの実装では、ハイパーパラメータのデフォルト設定を採用しています。例えば、ドットマトリックスのサイズは $6 \times 6$ に設定されています。ハイパーパラメータをカスタマイズしたり、新しい方法をさらに探求したりする場合は、`image_processor.py` を確認して変更してください。

**ステップ2** GPT-4V APIを呼び出す。

まず、`call-api.py` の `API_KEY` の位置（TODOでマークされている）に自分のOpenAI APIキーを入力する必要があります。その後、以下のコマンドを実行してサンプルを実行できます。

```bash
python call-api.py \
	--data-file data/examples/example.jsonl \
	--mode scaffold \
	--parallel 1
```
	
	
最後に、結果は `log` ディレクトリに保存されます。

---

## ⚙️ 手法

![wino_example_1](https://raw.githubusercontent.com/Sunwood-ai-labs/Scaffold-JP/main/assets/wino_example_1.jpg)

Scaffoldプロンプティングは、LMMsにおける視覚言語調整を強化するために設計されています。この手法には、画像のオーバーレイとテキストのガイドラインの両方が含まれています。したがって、視覚的および言語的な観点から手法の実装について紹介します。

**視覚的には**、各入力画像に、一様に分布した長方形のドットマトリックスを重ね合わせ、各ドットに多次元のデカルト座標をラベル付けします。これらのドットは視覚的な位置のアンカーとして機能し、その座標はテキスト応答におけるテキストの参照として利用されます。

**テキスト的には**、LMMsへのタスク指示の前にテキストのガイダンスを付加します。これには、ドットマトリックスと座標の簡単な説明と、それらを効果的に使用するためのいくつかの一般的なガイドラインが含まれます。

---

## 🚀 ユースケース

ここでは、私たちの実験からいくつかのケースを紹介します。

1. 空間推論能力の向上。

   <div align=center>
   <img src="https://raw.githubusercontent.com/Sunwood-ai-labs/Scaffold-JP/main/assets/vsr_example.jpg" alt="vsr_example" width="75%" style="zoom: 50%;" />
   </div>

2. 構成的推論能力の改善。

   <div align=center>
   <img src="https://raw.githubusercontent.com/Sunwood-ai-labs/Scaffold-JP/main/assets/wino_example_2.jpg" alt="wino_example_2" width="75%" style="zoom:50%;" />
   </div>

3. 高解像度画像における視覚検索能力の引き出し。

   <div align=center>
   <img src="https://raw.githubusercontent.com/Sunwood-ai-labs/Scaffold-JP/main/assets/vstar_example.jpg" alt="vstar_example" width="75%" style="zoom:50%;" />
   </div>

---

## 📂 結果

GPT-4Vを使用して11の難しい視覚言語ベンチマークで広範な実験を行い、結果は次のとおりです。

![results](https://raw.githubusercontent.com/Sunwood-ai-labs/Scaffold-JP/main/assets/results.jpg)

![active_perception](https://raw.githubusercontent.com/Sunwood-ai-labs/Scaffold-JP/main/assets/active_perception.jpg)

さらに、Scaffoldと能動知覚を組み合わせ、V* Bench direct_attributesサブセットで実験を行いました。次に詳述する結果は、Scaffoldが能動知覚のための効果的な足場として機能できることを示しています。

<div align=center>
<img src="https://raw.githubusercontent.com/Sunwood-ai-labs/Scaffold-JP/main/assets/results_active.jpg" alt="results_active" width="75%" style="zoom:33%;" />
</div>

## 👏 引用

```
@misc{lei2024scaffolding,
      title={Scaffolding Coordinates to Promote Vision-Language Coordination in Large Multi-Modal Models}, 
      author={Xuanyu Lei and Zonghan Yang and Xinrui Chen and Peng Li and Yang Liu},
      year={2024},
      eprint={2402.12058},
      archivePrefix={arXiv},
      primaryClass={cs.CV}
}
```