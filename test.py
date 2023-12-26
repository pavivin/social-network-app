import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging

# Set up the Firebase Admin SDK
cred = credentials.Certificate("voices_firebase_secrets.json")
firebase_admin.initialize_app(cred)

message = messaging.Message(
    data={
        "score": "850",
        "time": "2:45",
    },
    token="cTLpwvmZQc6OlC4yJ5odi0:APA91bHVZzoS8cu1SuG31HslyidzGq_fCwEvayxkn684_PZrLbHPUZ3-PBhKUHOlJOgwGIlmTqd--jSeNckmJ7MJweGQznmdBf8fMvXu28D8xacVMOfbHSkpW-I6lBjo19gqdtCM-R3k",
)

# Send the message
response = messaging.send(message)
print("Successfully sent message:", response)
