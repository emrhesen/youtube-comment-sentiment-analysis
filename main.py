

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# Data kütüphaneleri
import pandas as pd

# Chartlar
import matplotlib.pyplot as plt

# NLP Kütüphanesi
from textblob import TextBlob

# Diğer Kütüphaneler
import pickle
import os


from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def get_authenticated_service():
    credentials = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    #  Check if the credentials are invalid or do not exist
    if not credentials or not credentials.valid:
        # Check if the credentials have expired
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_console()

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def get_video_comments(service, **kwargs):
    comments = []
    results = service.commentThreads().list(**kwargs).execute()

    while results:
        for item in results['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)

        # Check if another page exists
        if 'nextPageToken' in results:
            kwargs['pageToken'] = results['nextPageToken']
            results = service.commentThreads().list(**kwargs).execute()
        else:
            break

    return comments


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    service = get_authenticated_service()
    videoId = input('Youtube VideoId : ')
    comments = get_video_comments(service, part='snippet', videoId=videoId, textFormat='plainText')

    polarity = []
    subjectivity = []

    for i in comments:
        try:
            analysis = TextBlob(i)
            polarity.append(analysis.sentiment.polarity)
            subjectivity.append(analysis.sentiment.subjectivity)
        except:
            polarity.append(0)
            subjectivity.append(0)

    df = pd.DataFrame(comments, columns=['Comment'])
    df['Polarity'] = polarity
    df['Subjectivity'] = subjectivity

    df.loc[df.Polarity == 0 , 'Polarity'] = 0
    df.loc[df.Polarity > 0 , 'Polarity'] = 1
    df.loc[df.Polarity < 0 , 'Polarity'] = -1



    df['Polarity'].value_counts().plot.bar();
    plt.show();

    df.to_excel("output.xlsx")
