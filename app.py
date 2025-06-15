import gradio as gr
import pdfplumber
import docx2txt
import re
import pandas as pd

from datetime import datetime

from dateutil import parser

# Extract resume text

def extract_text(file_obj):


   name = file_obj.name.lower()


   if name.endswith(".pdf"):


       with pdfplumber.open(file_obj.name) as pdf:


           return "\n".join(filter(None, [p.extract_text() for p in pdf.pages]))


   elif name.endswith(".docx"):


       return docx2txt.process(file_obj.name)


   else:


       return ""







# Extract candidate name


def get_candidate_name(text):


   lines = [l.strip() for l in text.splitlines() if l.strip()]


   for line in lines[:10]:


       words = line.split()


       if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w[0].isalpha()):


           if not re.search(r"(Resume|Curriculum Vitae)", line, re.I):


               return line


   return "Name not found"







# Extract all completed degrees


def extract_all_degrees(text):


   degrees = {


       "phd": 6, "doctorate": 6, "dphil": 6,


       "master": 5, "msc": 5, "mba": 5, "ma": 5, "meng": 5,


       "bachelor": 4, "bsc": 4, "ba": 4, "beng": 4,


       "associate": 3, "aas": 3, "a.s.": 3, "a.a.": 3,


       "high school diploma": 2, "ged": 2, "high school": 2


   }


   current_year = datetime.now().year


   found = []


   for deg_name, rank in degrees.items():


       if re.search(r'\b' + re.escape(deg_name) + r'\b', text.lower()):


           for line in text.splitlines():


               if deg_name in line.lower():


                   if "in progress" in line.lower() or "expected" in line.lower():


                       continue


                   match = re.search(r'\b(19|20)\d{2}\b', line)


                   if match:


                       year = int(match.group())


                       if year <= current_year:


                           found.append({"Degree": deg_name.title(), "Year": year})


   return found







# Extract work experience details


def get_experience_details(text):


   ranges = re.findall(


       r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)?\.?\s*\d{4})\s*[-–to]+\s*(present|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)?\.?\s*\d{4})",


       text, re.I


   )







   periods = []


   for start_str, end_str in ranges:


       try:


           start = parser.parse(start_str.strip(), dayfirst=False)


           end = datetime.today() if "present" in end_str.lower() else parser.parse(end_str.strip(), dayfirst=False)


           if start <= end:


               periods.append({'Start': start, 'End': end})


       except:


           continue







   # Merge overlapping periods


   periods.sort(key=lambda x: x['Start'])


   merged = []


   if periods:


       current = periods[0]


       for i in range(1, len(periods)):


           if periods[i]['Start'] <= current['End']:


               current['End'] = max(current['End'], periods[i]['End'])


           else:


               merged.append(current)


               current = periods[i]


       merged.append(current)







   detailed = []


   total_months = 0


   for p in merged:


       months = (p['End'].year - p['Start'].year) * 12 + (p['End'].month - p['Start'].month)


       if p['End'].day < p['Start'].day:


           months -= 1


       total_months += months


       detailed.append({


           "Start": p['Start'].strftime("%b %Y"),


           "End": p['End'].strftime("%b %Y"),


           "Months": months


       })







   return detailed, round(total_months / 12, 2)







# Master resume analysis function


def analyze_resume(file):


   text = extract_text(file)


   if not text.strip() or len(text.split()) < 50:


       return (


           "⚠️ Could not understand the resume content.\n🤖 Remember: humans are still better than programming sometimes!",


           "",


           "",


           pd.DataFrame(columns=["Degree", "Year"]),


           pd.DataFrame(columns=["Start", "End", "Months"])


       )







   name = get_candidate_name(text)


   degrees = extract_all_degrees(text)


   highest_edu = degrees[0]["Degree"] if degrees else "No completed degree found, please check manually!"


   edu_df = pd.DataFrame(degrees)







   work_data, total_years = get_experience_details(text)


   work_df = pd.DataFrame(work_data)







   return name, highest_edu, f"{total_years} years", edu_df, work_df







# Gradio interface


app = gr.Interface(


   fn=analyze_resume,


   inputs=gr.File(label="Upload a Resume (.pdf or .docx)"),


   outputs=[


       gr.Textbox(label="👤 Candidate Name"),


       gr.Textbox(label="🎓 Highest Completed Education"),


       gr.Textbox(label="📅 Total Full-Time Experience"),


       gr.Dataframe(label="📘 Completed Degrees"),


       gr.Dataframe(label="💼 Work Experience Periods")


   ],


   title="Resume Analyzer",


   description="Upload a resume to extract name, education, and full-time experience.\nNote: Even the smartest algorithms can’t match the nuance of human insight."


)







if __name__ == "__main__":


   app.launch()


