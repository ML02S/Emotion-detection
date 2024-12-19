import cv2
import face_recognition
from fer import FER
import time
from threading import Thread
from queue import Queue
import serial

# Arduino setup
arduino = serial.Serial('COM5', 9600)  # Pas de COM-poort aan indien nodig
time.sleep(2)  # Wacht tot de verbinding is opgezet

# Initialize variables
known_face_encodings = []
known_face_ids = []
next_id = 1
last_seen = {}
last_happy_times = {}
timeout = 600  # 10 minutes in seconds
face_detection_interval = 2
emotion_detection_interval = 3
cooldown_time = 120  # Cooldown tijd voor waterpomp in seconden
waterpump_active = False

# Initialize emotion detector
emotion_detector = FER(mtcnn=True)

# Video capture voor externe camera
video_capture = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # Gebruik 0 voor de eerste externe camera, of 1 als dat niet werkt
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not video_capture.isOpened():
    print("Kan de externe camera niet openen. Controleer of de camera is aangesloten.")
    exit()

print("Programma gestart. Druk op 'q' om te stoppen.")

frame_count = 0
face_queue = Queue(maxsize=5)
emotion_queue = Queue(maxsize=5)

def process_faces(frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    face_queue.put((face_locations, face_encodings))

def process_emotions(frame, face_location):
    top, right, bottom, left = face_location
    face_image = frame[top:bottom, left:right]
    emotions = emotion_detector.detect_emotions(face_image)
    emotion_queue.put((face_location, emotions))

def activate_waterpump(person_id):
    global waterpump_active
    waterpump_active = True
    print(f"Blijdschap gedetecteerd voor {person_id}, waterpomp geactiveerd voor 8 seconden.")
    arduino.write(b'WATER_ON')
    time.sleep(8)
    arduino.write(b'WATER_OFF')
    print(f"Waterpomp uitgeschakeld voor {person_id}.")
    waterpump_active = False

try:
    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Kan geen frame van de camera lezen. Opnieuw proberen...")
            time.sleep(1)
            continue

        frame_count += 1
        current_time = time.time()

        if frame_count % face_detection_interval == 0:
            Thread(target=process_faces, args=(frame.copy(),)).start()

        if not face_queue.empty():
            face_locations, face_encodings = face_queue.get()
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                face_id = "Onbekend"

                if True in matches:
                    first_match_index = matches.index(True)
                    face_id = known_face_ids[first_match_index]
                else:
                    face_id = f"Persoon {next_id}"
                    known_face_encodings.append(face_encoding)
                    known_face_ids.append(face_id)
                    next_id += 1

                last_seen[face_id] = current_time

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, face_id, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                if frame_count % emotion_detection_interval == 0:
                    Thread(target=process_emotions, args=(frame.copy(), (top, right, bottom, left))).start()

        if not emotion_queue.empty():
            face_location, emotions = emotion_queue.get()
            if emotions:
                top, right, bottom, left = face_location
                sorted_emotions = sorted(emotions[0]['emotions'].items(), key=lambda x: x[1], reverse=True)
                
                # Toon de top 3 emoties
                emotion_text = " | ".join([f"{emotion}: {conf:.2f}" for emotion, conf in sorted_emotions[:3]])
                cv2.putText(frame, emotion_text, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Debug informatie
                print(f"Gedetecteerde emoties: {sorted_emotions}")
                
                # Controleer op 'happy' emotie met lagere drempelwaarde
                if sorted_emotions[0][0] == 'happy' and sorted_emotions[0][1] > 0.5:
                    face_id = next((id for id, loc in last_seen.items() if loc == current_time), None)
                    if face_id:
                        last_happy_time = last_happy_times.get(face_id, 0)
                        if (current_time - last_happy_time) > cooldown_time:
                            if not waterpump_active:
                                last_happy_times[face_id] = current_time
                                Thread(target=activate_waterpump, args=(face_id,)).start()

        for face_id in list(last_seen.keys()):
            if current_time - last_seen[face_id] > timeout:
                if face_id in known_face_ids:
                    index = known_face_ids.index(face_id)
                    known_face_encodings.pop(index)
                    known_face_ids.pop(index)
                del last_seen[face_id]
                print(f"Gezicht met ID {face_id} verwijderd wegens inactiviteit.")

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Programma onderbroken door gebruiker.")

finally:
    video_capture.release()
    cv2.destroyAllWindows()
    arduino.close()
    print("Programma beëindigd.")
