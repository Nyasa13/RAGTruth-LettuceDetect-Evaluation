# RAGTruth–LettuceDetect Evaluation

## 📌 Project Overview

This project presents an **empirical evaluation and error analysis of LettuceDetect for RAG hallucination detection using the RAGTruth dataset**.

The work focuses on understanding where LettuceDetect succeeds and fails, particularly through **false-positive (FP) and false-negative (FN) analysis**, and evaluates whether targeted rule-based improvements can reduce missed hallucinations.

## 🎯 Objectives

- Evaluate LettuceDetect against RAGTruth
- Analyze false positives and false negatives
- Identify common failure patterns in hallucination detection
- Categorize false-negative cases
- Develop a targeted rule-based improvement
- Evaluate whether the rule improves overall detection performance
- Apply regression checks to prevent precision and F1 degradation

## 🔬 Methodology

The evaluation was performed in multiple phases.

### Phase 3 — Evaluation Corrections

The evaluation of LettuceDetect against RAGTruth was corrected by addressing:

- Incomplete gold annotations
- An overly strict span-matching threshold

These corrections primarily affected the false-positive side of the evaluation.

The original false negatives were then analyzed separately.

### Phase 4 — False Negative Analysis

Phase 4 focuses on the **false negatives that LettuceDetect missed**.

A pool of **783 false-negative cases** at a matching threshold of `0.1` was used, from which **100 cases were randomly sampled and manually categorized**.

## 📊 False Negative Categories

The sampled false negatives were categorized into five groups:

| Category | Count | Percentage |
|---|---:|---:|
| Attribute-related | 30 | 30% |
| Subtle-phrasing | 25 | 25% |
| Long-span | 20 | 20% |
| Numeric-buried | 17 | 17% |
| Other | 8 | 8% |

### Key Finding

**Attribute-related errors were the largest false-negative category (30%).**

These involved incorrect claims about structured fields such as:

- Hours
- WiFi
- Parking
- Reservations
- Music

This pattern was also observed in the false-positive analysis, making attribute-related hallucinations the most evidence-backed target for a rule-based improvement.

## 📈 False Negative Breakdown

![False Negative Category Breakdown](phase4_fn_breakdown.png)

## 🛠️ Rule-Based Improvement

A rule-based post-processor called `check_attributes()` was developed to cross-check generated answers against structured source information.

The rule checks for:

- **Attribute invention** — claims about fields marked as unknown or `None`
- **Hours mismatch** — stated times that do not match the source's available opening or closing times

## 🔄 Rule Iterations

Multiple versions of the rule were tested using the same `threshold=0.1` evaluation setup.

| Version | Precision | Recall | F1 | Result |
|---|---:|---:|---:|---|
| Baseline | 0.504 | 0.489 | 0.497 | — |
| Full rule | 0.372 | 0.552 | 0.445 | Regression |
| Narrow rule | 0.465 | 0.530 | 0.495 | Slightly below baseline |
| **Gap-fill rule** | **0.495** | **0.500** | **0.498** | **Marginal improvement** |

## 📊 Rule Iteration Results

![Rule Iteration Results](phase4_rule_iterations.png)

### Final Result

The final gap-fill approach produced a small improvement:

**F1: 0.497 → 0.498**

The rule was restricted to cases where LettuceDetect predicted **nothing at all**, allowing it to focus on detector blind spots instead of competing with existing predictions.

## 🔍 Error Analysis Findings

The analysis revealed several important failure modes.

### 1. Attribute-related hallucinations

Incorrect claims involving structured fields were the largest identified FN category.

### 2. Subtle phrasing

Some hallucinations were expressed naturally and fluently, without obvious linguistic signals.

### 3. Long spans

Long or multi-clause hallucinations can dilute model confidence and make detection more difficult.

### 4. Numeric information

Incorrect numbers embedded inside otherwise correct sentences were another common failure mode.

## ⚠️ Regression Analysis

The first rule-based version improved recall but significantly reduced precision.

The full rule produced:

- Precision: **0.372**
- Recall: **0.552**
- F1: **0.445**

This demonstrated that increasing recall alone does not necessarily improve the overall detector.

A hedge-phrase filter and improvements to hours parsing recovered much of the lost precision.

The final gap-fill version produced the best overall result with:

- Precision: **0.495**
- Recall: **0.500**
- F1: **0.498**

## 💡 Key Takeaways

- Attribute-related hallucinations were the largest identified FN category.
- Simple keyword-based rules can introduce many false positives.
- Rule-based improvements require careful regression testing.
- Improving recall without monitoring precision can make the overall system worse.
- Restricting the rule to detector blind spots produced a small net F1 improvement.
- The final improvement should be treated cautiously because the gain was only **+0.001 F1**.

## 🚀 Future Improvements

- Perform bootstrap resampling to test statistical significance
- Develop a more precise attribute-value extractor
- Compare generated attribute values directly against source values
- Improve detection of subtle-phrasing hallucinations
- Investigate long-span hallucinations
- Improve detection of numeric-buried hallucinations
- Evaluate the approach on a larger manually reviewed sample
- Explore more advanced model-based hallucination detection methods

## 🛠️ Technologies

- Python
- Jupyter Notebook
- Natural Language Processing (NLP)
- Retrieval-Augmented Generation (RAG)
- Large Language Models (LLMs)
- Hallucination Detection
- Error Analysis
- Rule-Based Classification
- RAGTruth
- LettuceDetect

## 📂 Project Structure

```text
RAGTruth-LettuceDetect-Evaluation/
│
├── .gitignore
├── README.md
├── requirements.txt
│
├── RAGTruth_LettuceDetect_Evaluation.ipynb
│
├── phase3a_fp_adjudication_export.py
├── phase3b_boundary_diagnosis.py
├── phase3c_baseless_export.py
├── phase4a_fn_analysis.py
├── phase4b_attribute_rule.py
│
├── phase4_summary.md
├── phase4_fn_breakdown.png
└── phase4_rule_iterations.png
