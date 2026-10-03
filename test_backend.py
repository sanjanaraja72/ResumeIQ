from utils.analyzer import analyze_resume

sample = """
John Doe
john@gmail.com | 9876543210 | github.com/john
Summary
Final year CSE student.
Skills
Python, Flask, SQL, HTML, CSS, JS, Git, Machine Learning
Projects
Developed a sales dashboard using Python and Pandas, improved reporting speed by 40%.
Education
B.E. Computer Science 2026
"""
r = analyze_resume(sample)
print("ATS:", r["ats_score"])
print("Best role:", r["best_role"]["role"], r["best_role"]["match"], "%")
print("Missing:", r["best_role"]["missing"])
print("Tips:", r["tips"])