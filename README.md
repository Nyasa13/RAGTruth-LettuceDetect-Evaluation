# RAGTruth + LettuceDetect: Hallucination Detection Evaluation

An empirical evaluation of LettuceDetect for detecting hallucinated spans in Retrieval-Augmented Generation (RAG) responses using the RAGTruth dataset.

## Overview

This project evaluates the ability of LettuceDetect to identify hallucinated spans in RAG-generated answers.

LettuceDetect predictions are compared against RAGTruth ground-truth hallucination spans using character-level Intersection over Union (IoU).

The project also performs detailed error analysis and investigates whether targeted rule-based source verification can address specific failure cases.

## Project Pipeline

RAGTruth Dataset
↓
LettuceDetect
↓
Hallucination Span Detection
↓
IoU-based Evaluation
↓
Precision / Recall / F1
↓
IoU Threshold Analysis
↓
False Positive / False Negative Analysis
↓
Error Categorization
↓
Boundary Diagnosis
↓
Structured Source Verification
↓
Hybrid Evaluation

## Main Components

- RAGTruth dataset
- LettuceDetect transformer model
- Character-level span matching
- IoU threshold analysis
- Precision, Recall and F1 evaluation
- False-positive analysis
- False-negative analysis
- Boundary/tokenization diagnosis
- Unsupported information analysis
- Source contradiction analysis
- Structured attribute verification
- Business-hours verification
- Rule-based hybrid detection

## Dataset

The project uses the processed RAGTruth dataset:

`wandb/RAGTruth-processed`

The dataset is loaded programmatically using Hugging Face Datasets.

## Model

LettuceDetect:

`KRLabsOrg/lettucedect-v2-mmbert-base`

## Technologies

- Python
- PyTorch
- Hugging Face Datasets
- LettuceDetect
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- Seaborn
- Regular Expressions
- AST parsing
- Jupyter Notebook

## Evaluation

The project evaluates hallucination span detection using multiple IoU thresholds.

The evaluation includes:

- True Positives
- False Positives
- False Negatives
- Precision
- Recall
- F1 Score

## Error Analysis

Detected errors are investigated through categories including:

- Boundary/tokenization artifacts
- Baseless or unsupported information
- Source contradictions
- Numbers/value mismatches
- Wrong occurrence / partial matches
- False alarms on supported content
- Cases not annotated by gold labels

## Rule-Based Verification

A structured-data verification layer checks claims involving attributes such as:

- WiFi
- Reservations
- Outdoor seating
- Takeout
- Groups
- Music
- Parking
- Business hours

These rules are evaluated independently and as part of hybrid approaches with LettuceDetect.

## How to Run

Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
cd RAGTruth-LettuceDetect-Evaluation