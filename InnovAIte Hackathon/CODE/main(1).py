import openai
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from colorama import Fore, Style
import questionary
import webbrowser
import urllib.parse

# Set up the OpenAI API key
openai.api_key = ""


def generate_notes(subject, chapter):
  # Set up the prompt
  prompt = f"Generate notes for {subject} Chapter {chapter}."

  # Generate notes using the GPT-3.5-turbo-instruct model
  response = openai.Completion.create(engine="gpt-3.5-turbo-instruct",
                                      prompt=prompt,
                                      max_tokens=4000)

  # Extract and return the generated notes
  return response['choices'][0]['text'].strip()


def generate_spoken_notes(notes):
  # Set up text-to-speech API (gTTS)
  tts = gTTS(text=notes, lang='en')
  tts.save("spoken_notes.mp3")
  print("Spoken notes saved as spoken_notes.mp3")


def generate_image_notes(notes):
  # Create an image
  img = Image.new('RGB', (800, 600), color=(255, 255, 255))
  d = ImageDraw.Draw(img)
  font = ImageFont.load_default()

  # Split notes into lines
  lines = notes.split("\n")
  y_offset = 10
  for line in lines:
    d.text((10, y_offset), line, fill=(0, 0, 0), font=font)
    y_offset += 20

  img.save("image_notes.png")
  print("Image notes saved as image_notes.png")


# Function to input subjects for each day
def input_subjects():
  days = [
      'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
      'Sunday'
  ]
  subjects_per_day = {}
  for day in days:
    subjects = questionary.text(f"Enter subjects for {day}: ").ask().split(',')
    # Check if subjects list is empty
    if subjects and subjects != ['']:
      subjects_per_day[day] = [subject.strip() for subject in subjects]
  return subjects_per_day


# Function to input study time for each subject
def input_study_time(subjects_per_day):
  study_time_per_day = {}
  for day, subjects in subjects_per_day.items():
    study_time_per_subject = {}
    for subject in subjects:
      while True:
        study_time = questionary.text(
            f"How much time do you want to study {subject} on {day}? (hh:mm): "
        ).ask()
        if validate_time_format(study_time):
          study_time_per_subject[subject] = study_time
          break
        else:
          print("Invalid input format. Please enter time in hh:mm format.")
    study_time_per_day[day] = study_time_per_subject
  return study_time_per_day


# Function to validate time format
def validate_time_format(time):
  parts = time.split(':')
  if len(parts) != 2:
    return False
  try:
    hours = int(parts[0])
    minutes = int(parts[1])
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
      return False
  except ValueError:
    return False
  return True


# Function to input start time
def input_start_time():
  while True:
    start_time = questionary.text(
        "Enter start time for studying (hh:mm): ").ask()
    if validate_time_format(start_time):
      break
    else:
      print("Invalid input format. Please enter time in hh:mm format.")
  return start_time


# Function to create timetable
def create_timetable(subjects_per_day, study_time_per_day, start_time):
  timetable = {}
  for day, subjects in subjects_per_day.items():
    if subjects:  # Check if subjects list is not empty
      timetable[day] = []
      current_time = start_time
      for subject in subjects:
        # Check if subject has a study time
        if day in study_time_per_day and subject in study_time_per_day[day]:
          study_time = study_time_per_day[day][subject]
          timetable[day].append((current_time, subject))
          current_time = add_time(current_time, study_time)
      timetable[day].append(('End', current_time))
  return timetable


# Function to add time
def add_time(current_time, study_time):
  hours, minutes = map(int, current_time.split(':'))
  study_hours, study_minutes = map(int, study_time.split(':'))
  new_hours = hours + study_hours
  new_minutes = minutes + study_minutes
  if new_minutes >= 60:
    new_hours += 1
    new_minutes -= 60
  return f"{new_hours:02d}:{new_minutes:02d}"


# Function to create PDF timetable
def create_pdf_timetable(timetable):
  doc = SimpleDocTemplate("timetable.pdf", pagesize=letter)
  elements = []

  for day, schedule in timetable.items():
    if schedule:  # Only add day to timetable if there's a schedule
      data = [['Day', 'Time', 'Subject']]
      for time, subject in schedule:
        if time != 'End':
          data.append([day, time, subject])
      table = Table(data)
      style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.gray),
                          ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                          ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                          ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                          ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                          ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                          ('GRID', (0, 0), (-1, -1), 1, colors.black)])
      table.setStyle(style)
      elements.append(table)

  doc.build(elements)


# Function to generate YouTube link
def generate_youtube_link(subject, chapter):
  # Construct YouTube search query
  query = f"GCSE {subject} Chapter {chapter}"
  # Encode the query for URL
  encoded_query = urllib.parse.quote(query)
  # Construct the YouTube search URL
  youtube_url = f"https://www.youtube.com/results?search_query={encoded_query}"
  return youtube_url


# Main function
def main():
  print(Fore.GREEN + "Welcome to the Study Planner!" + Style.RESET_ALL)

  # Ask the user for their name
  name = questionary.text(
      "Hello, my name is daton. Please enter your name: ").ask()

  # Greet the user
  print(f"Hello, {name}!")

  # Ask the user to choose between the study schedule generator and notes generator
  choice = questionary.select(
      "Please choose an option:",
      choices=["Study Schedule Generator", "Notes Generator"]).ask()

  if choice == "Study Schedule Generator":
    print("Starting Study Schedule Generator...")
    subjects_per_day = input_subjects()
    if not subjects_per_day:
      print(Fore.RED + "No subjects entered. Exiting program." +
            Style.RESET_ALL)
      return
    study_time_per_day = input_study_time(subjects_per_day)
    start_time = input_start_time()
    timetable = create_timetable(subjects_per_day, study_time_per_day,
                                 start_time)
    create_pdf_timetable(timetable)  # Create PDF timetable
    print(Fore.GREEN + "\nTimetable generated and saved as timetable.pdf" +
          Style.RESET_ALL)

  elif choice == "Notes Generator":
    print("Starting Notes Generator...")
    # Ask the user for the subject
    subject = questionary.text("Enter the subject you want notes for: ").ask()

    # Ask the user for the chapter
    chapter = questionary.text("Enter the chapter: ").ask()

    # Ask the user how they want to receive the notes
    output_format = questionary.select("How do you want to receive the notes?",
                                       choices=["Text", "Speech",
                                                "Image"]).ask()

    if output_format == "Text":
      # Generate notes based on the subject and chapter
      notes = generate_notes(subject, chapter)
      # Print the generated notes
      print(Fore.GREEN + "Generated Notes:" + Style.RESET_ALL)
      print(notes)
    elif output_format == "Speech":
      # Generate and play spoken notes
      notes = generate_notes(subject, chapter)
      generate_spoken_notes(notes)
    elif output_format == "Image":
      # Generate and save image notes
      notes = generate_notes(subject, chapter)
      generate_image_notes(notes)

    # Ask the user if they want YouTube videos on the topic
    want_videos = questionary.confirm(
        "Do you want YouTube videos on the topic?").ask()
    if want_videos:
      youtube_link = generate_youtube_link(subject, chapter)
      print(
          f"Here is a YouTube link for {subject} Chapter {chapter}: {youtube_link}"
      )
      webbrowser.open(youtube_link)


if __name__ == "__main__":
  main()
