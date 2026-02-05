# Evaluation Report (Retrieval Only)

**Evaluation Mode**: Retrieval Accuracy Analysis
**Metric K**: 5

| Query | Expected Source | Top-K Found | Accuracy | Precision@K |
|---|---|---|---|---|
| What is the gross revenue of Wipro for Q3 FY26? | `wipro_press-release-q1fy26.pptx` | wipro press-release-q2fy26.pptx<br>wipro press-release-q2fy26.pptx<br>wipro_press-release-q1fy26.pptx... | ✅ | 0.40 |
| Show me Nike products currently on discount | `nike_discounts.json` | nike_discounts.json<br>nike_discounts.json<br>nike_discounts.json... | ✅ | 1.00 |
| Details about Aarav Sharma's employment | `employees.csv` | employees.csv<br>infosys-esg-employee-wellness-and-experience.pdf<br>employees.csv... | ✅ | 0.40 |
| What are the common factors leading to employee attrition? | `WA_Fn-UseC_-HR-Employee-Attrition.csv` | ibm-annual-report-2024.docx<br>ibm-annual-report-2024.docx<br>WA_Fn-UseC_-HR-Employee-Attrition.csv... | ✅ | 0.60 |
| Summary of IBM's 2023 annual report | `ibm-annual-report-2023.pdf` | ibm-annual-report-2024.docx<br>ibm-annual-report-2024.docx<br>ibm-annual-report-2024.docx... | ❌ | 0.00 |
| Are there any deals on Nike Air Jordan shoes? | `nike_discounts.json` | nike_discounts.json<br>nike_discounts.json<br>nike_discounts.json... | ✅ | 1.00 |
| What department does Rohan Mehta work in? | `employees.csv` | email sentiment analysis dataset.csv<br>email sentiment analysis dataset.csv<br>Tech_Mahindra.json... | ❌ | 0.00 |
| Wipro IT services segment revenue performance | `wipro_press-release-q1fy26.pptx` | Wipro.json<br>wipro press-release-q2fy26.pptx<br>wipro_press-release-q1fy26.pptx... | ✅ | 0.40 |

### Aggregate Metrics
- **Mean Top-5 Accuracy**: 75.00%
- **Mean Precision@5**: 0.4750
