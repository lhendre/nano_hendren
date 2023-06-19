from inference import Inference
import uuid
import time
import json
from redis.cluster import RedisCluster
from redis import Redis

import boto3
from botocore.exceptions import ClientError
import logging
redis = Redis(host="nano-s.b7yglw.ng.0001.use2.cache.amazonaws.com", port=6379, decode_responses=True, db=0)
sqs = boto3.client('sqs', region_name='us-east-2',aws_access_key_id="AKIAT2DAQNWWAQQKX2YJ",aws_secret_access_key= "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")
QueueUrl = sqs.get_queue_url(QueueName="nano.fifo")
logger = logging.getLogger(__name__)

gpt_models = ['gpt2','gpt2-medium','gpt2-large','gpt2-xl']
def app():
    deactivate = False   
    while deactivate is not True:

        message = receive_messages(QueueUrl)
        if message is None or message is False:
            continue
        model = message["model"]
        prompt = message["prompt"]
        max_tokens = message["max_tokens"]
        temperature = message["temperature"]
        n = message["n"]
        logprobs = message["logprobs"]
        stop = message["stop"]
        logit_bias = message["logit_bias"]
        init_from = message["init_from"]
        out_dir = message["out_dir"]
        idRequest = message["id"]
        if "deactivate" in  message:
            deactivate = message["deactivate"]
        i = Inference(init_from=init_from,out_dir=out_dir,start=prompt,num_samples=n,max_new_tokens=max_tokens,temperature=temperature)
        r = i.run(stop=stop,logprobs=logprobs,logit_bias=logit_bias)


        ts = time.time()

        result = {
            "id": "cmpl-"+str(idRequest),
            "object": "text_completion",
            "created": ts,
            "model":    model,
            "choices": r,
            "usage": {
                "prompt_tokens": "t",
                "completion_tokens": "t",
                "total_tokens": "t"
            }
        }
        result=redis.set(idRequest, json.dumps(result))
        print("success:",result)


def receive_messages(QueueUrl, max_number=1, wait_time=20):
    """
    Receive a batch of messages in a single request from an SQS queue.

    :param queue: The queue from which to receive messages.
    :param max_number: The maximum number of messages to receive. The actual number
                       of messages received might be less.
    :param wait_time: The maximum time to wait (in seconds) before returning. When
                      this number is greater than zero, long polling is used. This
                      can result in reduced costs and fewer false empty responses.
    :return: The list of Message objects received. These each contain the body
             of the message and metadata and custom attributes.
    """
    try:
        messages = sqs.receive_message(
            QueueUrl=QueueUrl["QueueUrl"],
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=max_number,
            WaitTimeSeconds=wait_time
        )
        if "Messages" not in messages:
            return None
        for msg in messages["Messages"]:
            if msg["Body"]=="test":
                receipt_handle = msg['ReceiptHandle']
                delete_result=sqs.delete_message(QueueUrl=QueueUrl["QueueUrl"],ReceiptHandle=receipt_handle)
                return False

            print("msg:",msg["Body"])
            logger.info("Received message: %s: %s", msg["MessageId"], msg["Body"])
            receipt_handle = msg['ReceiptHandle']
            delete_result=sqs.delete_message(QueueUrl=QueueUrl["QueueUrl"],ReceiptHandle=receipt_handle)
            print("delete_result:",delete_result)

            return json.loads(msg["Body"])
    except ClientError as error:
        print("Client Error:", error)
        return False
    else:
        return None

if __name__ == "__main__":
    app()