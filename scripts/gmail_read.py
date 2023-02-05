from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import base64
import email
from googleapiclient import errors

# Set working path
if os.getcwd() == 'C:\\Users\\Laurie\\Documents\\GitHub\\lvd\\scripts':
    print("Working directory already set to gmail_read")
else:
    os.chdir('C:\\Users\\Laurie\\Documents\\GitHub\\gmail_read')
    print("Working directory now set to gmail_read")

def GetAttachments(service, user_id, msg_id, store_dir, already_in):
  """Get and store attachment from Message with given id.
  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: ID of Message containing attachment.
    store_dir: The directory used to store attachments.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    for part in message['payload']['parts']:
        print(part['filename'])
        filename = None
        data = None
        if 'data' in part['body']:
            data=part['body']['data']
            data = data.replace('-','+').replace('_','/')
            if not part['filename']:
                filename = msg_id+'.pdf'
        else:
            if len(part['body'].keys()) == 1 and  'attachmentId' not in part['body']:
                data = None
                pass
            else:
                att_id=part['body']['attachmentId']
                att=service.users().messages().attachments().get(userId=user_id, messageId=msg_id,id=att_id).execute()
                data=att['data']
                data = data.replace('-','+').replace('_','/')
        if data:
            file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
            if not filename:
                filename = part['filename']
            filename = filename.replace(' ','_').replace(',','_').replace(':','-').replace('(','').replace(')','')
            if filename not in already_in and filename[0:2] != 16:
                path = store_dir+filename
                print(path)
                with open(path, 'wb') as f:
                    f.write(file_data)
            else:
                print(filename + ' was skipped as it is already in the directory.')
  except errors.HttpError as error:
    print('An error occurred: %s' % error)
    return message



def GetMessage(service, user_id, msg_id):
  """Get a Message with given ID.
  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.
  Returns:
    A Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    print('Message snippet: %s' % message['snippet'])
    return message
  except errors.HttpError as error:
    print('An error occurred: %s' % error)


def ListMessagesMatchingQuery(service, user_id, query=''):
  """List all Messages of the user's mailbox matching the query.
  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    query: String used to filter messages returned.
    Eg.- 'from:user@some_domain.com' for Messages from a particular sender.
  Returns:
    List of Messages that match the criteria of the query. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate ID to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,
                                               q=query).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])
    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id, q=query,
                                         pageToken=page_token).execute()
      messages.extend(response['messages'])
    return messages
  except errors.HttpError as error:
    print('An error occurred: %s'%error)


def ListMessagesWithLabels(service, user_id, label_ids=[]):
  """List all Messages of the user's mailbox with label_ids applied.
  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    label_ids: Only return Messages with these labelIds applied.
  Returns:
    List of Messages that have all required Labels applied. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate id to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,
                                               labelIds=label_ids).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id,
                                                 labelIds=label_ids,
                                                 pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError as error:
    print('An error occurred: %s' % error)


def get_creds():
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token, encoding='latin1')
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'C:/Users/Laurie/Documents/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
    return creds


# def main():
"""Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
"""

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
creds = get_creds()

service = build('gmail', 'v1', credentials=creds)



def main():
    user_id = 'me'
    queries = ['has:attachment subject:"Lesbian Visibility Day"']
    attachment_dir = 'C:/Users/Laurie/Documents/LVD/'

    already_in = []
    # get the current files in there so we don't create the same ones again
    for root, dirs, files in os.walk(attachment_dir):
        for name in files:
            already_in.append(name)

    for query in queries:
        messages = ListMessagesMatchingQuery(service, user_id, query=query)
        for item in messages:
            msg_id = item['id']
            GetAttachments(service, user_id, msg_id, attachment_dir, already_in)

# Call the Gmail API
# results = service.users().labels().list(userId='me').execute()
# labels = results.get('labels', [])

# if not labels:
#     print('No labels found.')
# else:
#     print('Labels:')
#     for label in labels:
#         print(label['name'])

if __name__ == '__main__':
    main()