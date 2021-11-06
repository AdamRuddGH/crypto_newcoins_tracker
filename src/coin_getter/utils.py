"""
Shared utilities
"""

import arrow, json, time
import re, os
import boto3
import requests
from dotenv import load_dotenv
load_dotenv()

def datetime_now():
    """
    returns UTC now time
    add .format('YYYY-MM-DD HH:mm:ss ZZ') to convert to ISO
    add .format()
    """
    return arrow.utcnow()

def startofday_epohc_now():
    """
    give the epoch of the time at 00:00 hrs in epoch
    """
    now_date = arrow.utcnow().format("YYYY-MM-DD")
    now_epoch = arrow.get(now_date).format("X")
    now_epoch = re.sub(r"\.0","000",now_epoch)
    
    return now_epoch

def partition_path_from_date(input_date):
    """
    returns path for s3 partitioning from date:
    eg.
    `2021-11-27 00:00:00`
    becomes: 
    `year=2021/month=11/day=27`
    """
    date_value = arrow.get(input_date) #expects timestamp
    year = date_value.year
    month = date_value.month
    day = date_value.day

    return f"year={year}/month={month}/day={day}"


def epoch_to_timestamp(epoch_string):
    """
    converts data from epoch to athena friendly timestamp
    """
    
    epoch_string_clean = str(int(epoch_string/1000) ) #remove milliseconds
    try:
        formatted_timestamp = arrow.get(epoch_string_clean,"X").format("YYYY-MM-DD HH:mm:ss")
    except:
        formatted_timestamp = datetime_now().format("YYYY-MM-DD HH:mm:ss")
    return formatted_timestamp


def dict_to_jsonl(dict_input):
    """
    takes a dict object and turns it into a jsonl doc
    """

    jsonl_contents = json.dumps(dict_input)
    jsonl_contents = re.sub(f"\n","",jsonl_contents)
    return jsonl_contents


def list_of_dicts_to_jsonl(list_input):
    """
    takes a list of dict objects and turns it into a jsonl doc
    """

    jsonl_contents = ""
    for each_entry in list_input:
        jsonl_contents = jsonl_contents + "\n" + json.dumps(each_entry)

    
    return jsonl_contents


def write_to_storage(data, bucket, filename_path):
    """"
    will write data to a storage location
    """

    client = boto3.client('s3')
    return client.put_object(Body=data, Bucket=bucket, Key=filename_path)
    
def read_from_storage(bucket, filename_path):
    """
    will read data from a storage location *s3
    """
    client = boto3.client('s3')
    response = client.get_object(
        Bucket=bucket,
        Key=filename_path,
    )
    return response

def notify_discord_bot(text_string):
    """
    notifies the discord webhook
    """
    DISCORD_BOT_WEBHOOK = os.getenv('DISCORD_BOT_WEBHOOK')

    list_of_messages = split_string_discord(text_string)

    for each_message in list_of_messages:
        time.sleep(.5)
        data = {
            "content": str(each_message)
        }
        response = requests.post(url=DISCORD_BOT_WEBHOOK, json=data)
        print(response)
    
    print(f"notification complete")


def split_string_discord(input_string,character_limit=1500):
    """
    splits a string into chunks for discord notifications
    """
    chunks = input_string.split('\n')
    
    print(chunks)

    messages = []
    chunk_string = ""
    for each_item in chunks:
        old_chunkstring = chunk_string
        new_chunk_string = f"{chunk_string}\n{each_item}"
        if len(new_chunk_string) > character_limit:
            messages.append(old_chunkstring)
            chunk_string = each_item
        else:
            chunk_string = new_chunk_string 
        if each_item == chunks[-1]:
            print("last message")
            messages.append(chunk_string)
    
    return messages

def send_to_sqs(coin_id):
    """
    send a message to the sqs queue specified by the environment variable
    """
    # Create SQS client
    sqs = boto3.client('sqs')

    queue_url = 'SQS_QUEUE_URL'

    # Send message to SQS queue
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=1,
        MessageAttributes={
            'coin_id': {
                'DataType': 'String',
                'StringValue': str(coin_id)
            }
        },
        MessageBody=(
            'Sent for coin analysis'
        )
    )

    print(response['MessageId'])

def read_sqs_message(sqs_payload, key_to_find="coin_id"):
    """
    will read sqs messages and return the body message 
    """
    # try:
    # message = dict(sqs_payload)
    body = sqs_payload["Records"][0]["messageAttributes"][key_to_find]["stringValue"]
    print(body)
    # ["MessageAttributes"][key_to_find]["Value"]
    # key_we_need = body["MessageAttributes"][key_to_find]["Value"]
    return body

    # except Exception as e:
    #     print(f"unable to parse {key_to_find} from sqs message: {sqs_payload} ")
    # exit()


