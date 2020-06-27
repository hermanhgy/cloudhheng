import sqlite3
from datetime import datetime, timedelta


connection = sqlite3.connect('education.db')
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

id = 7
date = "2020-06-06"
time = "18:30"
duration_hour = 1
duration_min = 30
time_plus = datetime.strptime(time, "%H:%M") + timedelta(hours=int(duration_hour), minutes=int(duration_min))
time_plus = time_plus.strftime("%H:%M")
time_minus = datetime.strptime(time, "%H:%M") - timedelta(hours=int(duration_hour), minutes=int(duration_min))
time_minus = time_minus.strftime("%H:%M")
print(time_plus)
print(time_minus)
# Then select all to check if there is any conflict with the new schedule
cursor.execute("""SELECT * FROM upcoming WHERE teacher_id=:id AND date=:date AND (time BETWEEN :time_minus AND :time_plus) """,
    {'id':id, 'date':date, 'time_minus':time_minus, 'time_plus':time_plus})  
rows = cursor.fetchall()

print(rows)










# cursor.execute("""SELECT *, TIME("time", '+1 hour') as time_plus
#                 FROM upcoming WHERE date < :current_date OR (date = :current_date AND time_plus < :current_time)""", 
#                 {'current_date':current_date, 'current_time':current_time})
# rows = cursor.fetchall()
# # + timedelta(hours=duration_hour, minutes=duration_min)
# for row in rows:
#     print(row["id"])
#     print(row["time"])
#     print(row["time_plus"])
#     if (row["time_plus"]) < current_time:
#         print("yes") 

# validate_id = 27
# teacher_id = 7
# date = "2020-06-03"
# time = "15:15"
# duration = 1
# type = "Music"
# subject = "Piano"
# name = "Simple Theory of Chord Progression"
# level = "Basic-to-Intermediate"
# count_students = 2

# cursor.execute("""INSERT INTO history (id, teacher_id, date, time, duration, type, subject, name, level, student_no) 
#                         VALUES (:id, :teacher_id, :date, :time, :duration, :type, :subject, :name, :level, :student_no)""", 
#                         {'id': validate_id, 
#                         'teacher_id': teacher_id, 
#                         'date': date, 
#                         'time': time, 
#                         'duration': duration, 
#                         'type': type, 
#                         'subject': subject, 
#                         'name': name, 
#                         'level': level,
#                         'student_no': count_students})

# connection.commit()
# print("success")
# connection.close_all()

# cursor.execute("""SELECT * from upcoming WHERE teacher_id=:id ORDER BY date, time""", {'id': id})          
# upcoming = cursor.fetchall()

# for row in upcoming: 

#     # Retrieve the date, time, duration of the upcoming 
#     date = row["date"]
#     time = row["time"]
#     duration_hour = row["duration_hour"]
#     duration_min = row["duration_min"]

#     # Adding the duration to start time to yield the end time
#     time_plus = datetime.strptime(time, "%H:%M") + timedelta(hours=int(duration_hour), minutes=int(duration_min))
#     time_plus = time_plus.strftime("%H:%M")

#     # Joining date time to form a datetime format
#     date_time = date + " " + time_plus + ":00"
#     now = datetime.now()
#     date_time = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')

#     # Checking if the date time has already passed
#     if date_time < now:

#         class_id = row["id"]

#         # Retrieve the student list 
#         cursor.execute("""SELECT * from people WHERE people.id IN (
#                         SELECT person_id FROM upcoming JOIN upcoming_students 
#                         ON upcoming.id=upcoming_students.class_id WHERE id=:id)""", {'id':class_id})
#         data = cursor.fetchall()
#         count_student = len(data)

#         if count_student != 0:

#             # Moved all the information to the validate table if there is a student list (the class was happening)
#             cursor.execute("""INSERT INTO validate (id, teacher_id, date, time, duration_hour, duration_min, type, subject, name, level, message) 
#                         VALUES (:id, :teacher_id, :date, :time, :duration_hour, :duration_min, :type, :subject, :name, :level, :message)""", 
#                         {'id':class_id, 
#                         'teacher_id':row["teacher_id"], 
#                         'date': row["date"], 
#                         'time': row["time"], 
#                         'duration_hour': row["duration_hour"], 
#                         'duration_min': row["duration_min"],
#                         'type': row["type"], 
#                         'subject': row["subject"], 
#                         'name': row["name"], 
#                         'level': row["level"], 
#                         'message': row["message"]})
            
#             # Also move the student list from upcoming_students to validate_students
#             for row in data:
#                 cursor.execute("""INSERT INTO validate_students (validate_id, person_id) VALUES (:validate_id, :person_id)""",
#                                 {'validate_id':class_id, 'person_id':row["id"]})
           
#         # And then delete the data from the upcoming table
#         cursor.execute("""DELETE FROM upcoming WHERE id=:id""", {'id':class_id})
#         cursor.execute("""DELETE FROM upcoming_students WHERE class_id=:id""", {'id':class_id})

#         connection.commit()




# id=23

# cursor.execute("""SELECT * from upcoming ORDER BY date, time""")
# rows = cursor.fetchall()

# # Create a list of student's upcoming classes
# cursor.execute("""SELECT class_id from upcoming_students WHERE person_id=:id""", {'id':id})
# data = cursor.fetchall()
# classlist = []
# for row in data:
#     classlist.append(row["class_id"])
# print(classlist)

# # Retrieve what subjects he/she is learning
# cursor.execute("""SELECT * from subjects JOIN students ON subjects.id=students.subject_id 
#             WHERE students.person_id=:id""", {'id': id})  
# data = cursor.fetchall()
# learning = []
# for row in data:
#     learning.append(row["name"])
# print(learning)

# # If student has registered for this class, or if not the subject of interest, 
# # remove this record to be shown in "search"

# rows_temp = []

# for row in rows:
#     if row["id"] not in classlist and row["subject"] in learning: 
#         rows_temp.append(row)

# print(rows_temp)









# id = 11
# cursor.execute("""SELECT * from upcoming WHERE teacher_id=:id ORDER BY date, time""", {'id': id})  
# upcoming = cursor.fetchall()
# print(upcoming)

# students = []
# count = []

# for row in upcoming:
#     print(row["id"])
#     # For each upcoming class, retrieve all students enrolled in that class
#     cursor.execute("""SELECT * from people WHERE people.id IN (
#                     SELECT person_id FROM upcoming JOIN upcoming_students 
#                     ON upcoming.id=upcoming_students.class_id WHERE id=:id)""", {'id':row["id"]}) 
#     data = cursor.fetchall()
#     students.append(data)
#     count.append(len(data))

# for i in range (0, len(upcoming)):
#     print(upcoming[i]["name"])
#     for row in students[i]:
#         print(row["name"])
#     print(count[i])


# cursor.execute("""SELECT * from people WHERE id =:id""", {'id': id})
# teacher = cursor.fetchone()
# teacher_name = teacher["name"]
# teacher_organization = teacher["organization"]

# print(teacher_name)
# print(teacher_organization)

# cursor.execute("""SELECT * from upcoming ORDER BY date, time""")
# rows = cursor.fetchall()

# # Create a list of student's upcoming classes
# cursor.execute("""SELECT class_id from upcoming_students WHERE person_id=:id""", {'id':id})
# data = cursor.fetchall()
# classlist = []
# for row in data:
#     classlist.append(row["class_id"])
# print(classlist)

# # Retrieve what subjects he/she is learning
# cursor.execute("""SELECT * from subjects JOIN students ON subjects.id=students.subject_id 
#             WHERE students.person_id=:id ORDER BY name""", {'id': id})  
# data = cursor.fetchall()
# learning = []
# for row in data:
#     learning.append(row["name"])

# print(learning)

# # If student has registered for this class, or remove this record to be shown in "search"
# for row in rows:
#     if (row["id"] in classlist) or (not row["subject"] in learning):
#         rows.remove(row)

# for row in rows:
#     print(row["name"])

# # # Retrieve what subjects he/she is learning
# # cursor.execute("""SELECT * from subjects JOIN students ON subjects.id=students.subject_id 
# #             WHERE students.person_id=:id ORDER BY name""", {'id': id})  
# # learning = cursor.fetchall()

# # rows = []
# # for row in learning:
#     cursor.execute("""SELECT * from upcoming WHERE subject=:subject""", {'subject': row["name"]})  
#     data = cursor.fetchall()
#     rows.append(data) 

# print(rows)

# # Create a list of student's upcoming classes
# cursor.execute("""SELECT class_id from upcoming_students WHERE person_id=:id""", {'id':id})
# data = cursor.fetchall()

# classlist = []
# for row in data:
#     classlist.append(row["class_id"])

# for row in rows:
#     for row in row:
#         if row["id"] in classlist:
#             rows.remove(row)


# # Retrieve the type list based on the subjects selected
# typelist = []
# for row in subjects:
#     print(row["name"])
#     cursor.execute("""SELECT type FROM subjects WHERE name=:name""", {'name': row["name"]})
#     data = cursor.fetchone()["type"]
#     if not data in typelist:
#         typelist.append(data)

# print(typelist)

# cursor.execute("""SELECT * from upcoming ORDER BY date, time""")
# rows = cursor.fetchall()
# print(rows)

# cursor.execute("""SELECT class_id from upcoming_students WHERE person_id=:id""", {'id':id})
# data = cursor.fetchall()

# classlist = []
# for row in data:
#     classlist.append(row["class_id"])

# print(classlist)

# for row in rows:
#     print(row["id"])
#     if row["id"] in classlist:
#         print("yes")
#         rows.remove(row)
 
# print(rows)








#  id = 14

# cursor.execute("""SELECT * from upcoming JOIN upcoming_students ON upcoming.id = upcoming_students.class_id 
#                 WHERE upcoming_students.person_id =:id ORDER BY date, time""", {'id': id})  
# upcoming = cursor.fetchall()

# rows = []

# for row in upcoming:
#     cursor.execute("""SELECT name from people WHERE id =:id""", {'id': row["teacher_id"]})
#     teacher = cursor.fetchone()["name"]

#     data = {'date':row["date"], 'time':row["time"], 'duration_hour':row["duration_hour"], 
#             'duration_min':row["duration_min"], 'type':row["type"], 'subject':row["subject"], 
#             'name':row['name'], 'level':row['level'], 'message':row['message'], 'teacher':teacher}
#     rows.append(data)
    
# print(rows)

# for row in rows:
#     print(row["name"])
#     print(row["teacher"])




# # Design a list that would store "type" and "list of subject"
# type_subj_lists = []

# # Repeat this for n numbers of types
# for i in range (0, count):
    
#     # Design a list that would store list of subject
#     subject_list = []

#     # Retrieve all the subjects correspond to the type
#     cursor.execute("""SELECT name FROM subjects WHERE type=:type""", {'type': type_list[i]["type"]})
#     a_list = cursor.fetchall()
#     for row in a_list:
#         subject_list.append(row["name"])

#     # Store the type + list of subjects together 
#     type_subj_lists.append((type_list[i]["type"], (subject_list)))

#  print(type_subj_lists)

# for item in type_subj_lists:
#     print(item[0])
#     for item in item[1]:
#         print(item)





# person_id = 7
# cursor.execute("""DELETE FROM teachers WHERE person_id=:person_id""", {'person_id':person_id})

# subjects = ['Spanish', 'English', 'Social Media']
# for item in subjects:
#     cursor.execute("""SELECT id FROM subjects WHERE name=:name""", {'name':item})
#     subject_id = cursor.fetchone()["id"]
  
#     cursor.execute("""INSERT INTO teachers (subject_id, person_id) VALUES (:subject_id, :person_id)""", 
#             {'subject_id':subject_id, 'person_id':person_id})

# connection.commit()


# # Retrieve all upcoming classes 
#         cursor.execute("""SELECT * from upcoming WHERE teacher_id=:id ORDER BY date, time""", {'id': id})          
#         upcoming = cursor.fetchall()


#         # Check if the upcoming classes has passed
#         for row in upcoming: 

#             # Retrieve the date, time, duration of the upcoming 
#             date = row["date"]
#             time = row["time"]
#             duration_hour = row["duration_hour"]
#             duration_min = row["duration_min"]

#             # Adding the duration to start time to yield the end time
#             time_plus = datetime.strptime(time, "%H:%M") + timedelta(hours=int(duration_hour), minutes=int(duration_min))
#             time_plus = time_plus.strftime("%H:%M")

#             # Joining date time to form a datetime format
#             date_time = date + " " + time_plus + ":00"
#             now = datetime.now()
#             date_time = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')

#             # Checking if the date time has already passed
#             if date_time < now:

#                 class_id = row["id"]

#                 # Retrieve the student list 
#                 cursor.execute("""SELECT * from people WHERE people.id IN (
#                                 SELECT person_id FROM upcoming JOIN upcoming_students 
#                                 ON upcoming.id=upcoming_students.class_id WHERE id=:id)""", {'id':class_id})
#                 data = cursor.fetchall()
#                 count_student = len(data)

#                 if count_student != 0:

#                     # Moved all the information to the validate table if there is a student list (the class was happening)
#                     cursor.execute("""INSERT INTO validate (id, teacher_id, date, time, duration_hour, duration_min, type, subject, name, level, message) 
#                                 VALUES (:id, :teacher_id, :date, :time, :duration_hour, :duration_min, :type, :subject, :name, :level, :message)""", 
#                                 {'id':class_id, 
#                                 'teacher_id':row["teacher_id"], 
#                                 'date': row["date"], 
#                                 'time': row["time"], 
#                                 'duration_hour': row["duration_hour"], 
#                                 'duration_min': row["duration_min"],
#                                 'type': row["type"], 
#                                 'subject': row["subject"], 
#                                 'name': row["name"], 
#                                 'level': row["level"], 
#                                 'message': row["message"]})
                    
#                     # Also move the student list from upcoming_students to validate_students
#                     for row in data:
#                         cursor.execute("""INSERT INTO validate_students (validate_id, person_id) VALUES (:validate_id, :person_id)""",
#                                         {'validate_id':class_id, 'person_id':row["id"]})
           
#                 # And then delete the data from the upcoming table
#                 cursor.execute("""DELETE FROM upcoming WHERE id=:id""", {'id':class_id})
#                 cursor.execute("""DELETE FROM upcoming_students WHERE class_id=:id""", {'id':class_id})

#                 connection.commit()