from inference import Inference
import uuid
import time
import json
from redis import Redis
import boto3


redis = Redis(host="clustercfg.nanohendren.b7yglw.use2.cache.amazonaws.com", port=6379, decode_responses=True)
sqs = boto3.client('sqs', region_name='us-east-2',aws_access_key_id="AKIAT2DAQNWWAQQKX2YJ",aws_secret_access_key= "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")
QueueUrl = sqs.get_queue_url(QueueName="nano.fifo")


gpt_models = ['gpt2','gpt2-medium','gpt2-large','gpt2-xl']
def app():
    '''
    App processor.  Retrieves data to process from queue, process data then uploads to reddit
    '''
    deactivate = False    
    while deactivate is not True:

        message = receive_messages(QueueUrl)
        model = message.model
        prompt = message.prompt
        max_tokens = message.max_tokens
        temperature = message.temperature
        n = message.n
        logprobs = message.logprobs
        stop = message.stop
        logit_bias = message.logit_bias
        init_from = message.init_from
        out_dir = message.out_dir
        idRequest = message.id
        deactivate = message.deactivate
        if deactivate is None:
            deactivate = False
        i = Inference(init_from=init_from,out_dir=out_dir,start=prompt,num_samples=n,max_new_tokens=max_tokens,temperature=temperature)
        r = i.run(stop=stop,logprobs=logprobs,logit_bias=logit_bias)



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
        result=redis.set(idRequest, result)


def receive_messages(QueueUrl, max_number=1, wait_time=10):
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
        messages = queue.receive_messages(
            QueueUrl=QueueUrl,
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=max_number,
            WaitTimeSeconds=wait_time
        )
        for msg in messages:
            logger.info("Received message: %s: %s", msg.id, msg.body)
    except ClientError as error:
        return False
    else:
        return messages.body

if __name__ == "__main__":
    app()