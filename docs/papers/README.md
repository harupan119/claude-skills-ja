# 論文原本のミラー

[docs/research-notes.md](../research-notes.md) の作成にあたって読んだ論文22本（うち20本をスキル本文と local-llm-gate の監査記録に反映）の原本を、取得元・版・ハッシュつきで固定したもの。引用元の論文が後から改訂・移転しても、スキルの記述がどの版のどの記述に基づくかを検証できるようにしてある。取得日は2026-09-26。

## 構成

| パス | 中身 |
|---|---|
| `manifest.json` | 正本。各論文の取得元URL（arXiv は版番号つき）、ライセンス、SHA-256、バイト数、引用しているスキル |
| `pdf/` | 再配布が許されるライセンス（CC BY / CC BY-SA / CC0）の8本を同梱 |
| `cache/` | それ以外の14本を手元に取得する先。`.gitignore` 済みでコミットしない |
| `fetch_papers.py` | 取得とハッシュ検証、arXiv の新版の確認 |

```bash
python3 docs/papers/fetch_papers.py                  # 同梱8本のハッシュを検証
python3 docs/papers/fetch_papers.py --fetch          # 残り14本を cache/ に取得して検証（22本揃う）
python3 docs/papers/fetch_papers.py --check-updates  # arXiv に新しい版が出ていないか
```

SHA-256 が合わないときは、取得元が PDF を差し替えたか、別の版を返している。内容を確かめ、引用した数値や記述が変わっていないことを確認してから `manifest.json` を更新する。新しい版が出ていた場合も同じ手順で、スキル本文の数値を見直す。

## 同梱しているもの（再配布可）

各 PDF は取得元から無改変で複製したもの。適用されるのは表に示した各論文のライセンスで、このリポジトリの MIT ライセンスは適用されない。

| 論文 | ライセンス | 取得元 | ファイル |
|---|---|---|---|
| Kobak et al. (2025). Delving into LLM-assisted writing in biomedical publications through excess vocabulary. Science Advances 11(27) | [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/) | [2406.07016v5](https://arxiv.org/abs/2406.07016v5) | `pdf/kobak_excess_vocab.pdf` |
| Russell, Karpinska & Iyyer (2025). People who frequently use ChatGPT for writing tasks are accurate and robust detectors of AI-generated text. ACL 2025 | [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/) | [2501.15654v2](https://arxiv.org/abs/2501.15654v2) | `pdf/russell_expert_human_detectors.pdf` |
| Panickssery, Bowman & Feng (2024). LLM Evaluators Recognize and Favor Their Own Generations | [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) | [2404.13076v1](https://arxiv.org/abs/2404.13076v1) | `pdf/panickssery_self_preference.pdf` |
| Huang et al. (2024). Large Language Models Cannot Self-Correct Reasoning Yet. ICLR 2024 | [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) | [2310.01798v2](https://arxiv.org/abs/2310.01798v2) | `pdf/huang_cannot_self_correct.pdf` |
| Fatemi et al. (2024). Test of Time: A Benchmark for Evaluating LLMs on Temporal Reasoning | [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) | [2406.09170v1](https://arxiv.org/abs/2406.09170v1) | `pdf/fatemi_test_of_time.pdf` |
| Saxena, Gema & Minervini (2025). Lost in Time: Clock and Calendar Understanding Challenges in Multimodal LLMs. ICLR 2025 Workshop | [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) | [2502.05092v2](https://arxiv.org/abs/2502.05092v2) | `pdf/lost_in_time_clock_calendar.pdf` |
| Zheng et al. (2024). NATURAL PLAN: Benchmarking LLMs on Natural Language Planning | [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) | [2406.04520v1](https://arxiv.org/abs/2406.04520v1) | `pdf/zheng_natural_plan.pdf` |
| Gao et al. (2023). PAL: Program-aided Language Models. ICML 2023 | [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/) | [2211.10435v2](https://arxiv.org/abs/2211.10435v2) | `pdf/gao_pal.pdf` |

## 同梱していないもの（取得元へのリンクのみ）

arXiv の既定ライセンス（arXiv-nonexclusive）は arXiv 自身への配布許諾で、第三者の再配布を許していない。CC BY-NC-ND は非営利・無改変なら再配布できるが、このリポジトリは MIT（商用利用可）で公開しているため、混同を避けて同梱しない。学会・出版社の著作権下にあるものも同様。いずれも取得元で無料公開されており、`--fetch` で同じ版を取得できる。

| 論文 | ライセンス | 取得元 |
|---|---|---|
| Zaitsu & Jin (2023). Distinguishing ChatGPT(-3.5, -4)-generated and human-written papers through Japanese stylometric analysis. PLOS ONE 18(8) | arXiv-nonexclusive | [原本](https://arxiv.org/abs/2304.05534v3) |
| Liang et al. (2023). GPT detectors are biased against non-native English writers. Patterns | arXiv-nonexclusive | [原本](https://arxiv.org/abs/2304.02819v3) |
| Krishna et al. (2023). Paraphrasing evades detectors of AI-generated text, but retrieval is an effective defense. NeurIPS 2023 | arXiv-nonexclusive | [原本](https://arxiv.org/abs/2303.13408v2) |
| Reinhart et al. (2025). Do LLMs write like humans? Variation in grammatical and rhetorical styles. PNAS 122 | CC-BY-NC-ND-4.0 | [原本](https://arxiv.org/abs/2410.16107v2) |
| Zheng et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 2023 | arXiv-nonexclusive | [原本](https://arxiv.org/abs/2306.05685v4) |
| Min et al. (2023). FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation. EMNLP 2023 | arXiv-nonexclusive | [原本](https://arxiv.org/abs/2305.14251v2) |
| Bai et al. (2024). LongWriter: Unleashing 10,000+ Word Generation from Long Context LLMs | arXiv-nonexclusive | [原本](https://arxiv.org/abs/2408.07055v1) |
| Liu et al. (2023). Lost in the Middle: How Language Models Use Long Contexts. TACL | arXiv-nonexclusive | [原本](https://arxiv.org/abs/2307.03172v3) |
| Liu et al. (2023). G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment | CC-BY-NC-ND-4.0 | [原本](https://arxiv.org/abs/2303.16634v3) |
| Liang et al. (2024). Mapping the Increasing Use of LLMs in Scientific Papers | CC-BY-NC-ND-4.0 | [原本](https://arxiv.org/abs/2404.01268v1) |
| Wang et al. (2023). Large Language Models are not Fair Evaluators | arXiv-nonexclusive | [原本](https://arxiv.org/abs/2305.17926v2) |
| Wang et al. (2012). Undefined Behavior: What Happened to My Code? APSys 2012 | publisher-copyright | [原本](https://pdos.csail.mit.edu/papers/ub:apsys12.pdf) |
| Wang et al. (2013). Towards Optimization-Safe Systems: Analyzing the Impact of Undefined Behavior. SOSP 2013 | publisher-copyright | [原本](https://pdos.csail.mit.edu/papers/stack:sosp13.pdf) |
| Serebryany et al. (2012). AddressSanitizer: A Fast Address Sanity Checker. USENIX ATC 2012 | publisher-copyright | [原本](https://www.usenix.org/conference/atc12/technical-sessions/presentation/serebryany) |

`liang_mapping_llm_papers` と `wang_not_fair_evaluators` は参照したが、スキル本文には反映していない（`used_in` が空）。
