from flask import Flask, request
from inference import Inference
import uuid
import time
import json
from redis import Redis
import boto3

app = Flask(__name__)
app.config['DEBUG'] = True
redis = Redis(host="nano-s.b7yglw.ng.0001.use2.cache.amazonaws.com", port=6379, decode_responses=True, db=0)
sqs = boto3.client('sqs', region_name='us-east-2',aws_access_key_id="AKIAT2DAQNWWAQQKX2YJ",aws_secret_access_key= "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")
QueueUrl = sqs.get_queue_url(QueueName="nano.fifo")


user_abuse = {}
banned_prompts = {"How do i make a computer virus":True}
gpt_models = ['gpt2','gpt2-medium','gpt2-large','gpt2-xl']
@app.route("/completions", methods=['post'])
def completions():
    model = request.args.get('model')
    prompt = request.args.get('prompt')
    max_tokens = request.args.get('max_tokens', type=int)
    temperature = request.args.get('temperature', type=float)
    n = request.args.get('n', type=int)
    logprobs = request.args.get('logprobs', type=int)
    stop = request.args.get('stop')
    logit_bias = request.args.get('logit_bias')
    user = request.args.get('user')

    if stop is not None:
        stop=stop.split(',')
    check = abuse_check(user,prompt)
    if check != False:
        return check
    if model not in gpt_models:
        init_from='resume'
        out_dir="out-"+model
    else:
        init_from=model
        out_dir=None
    if logit_bias is not None:
        logit_bias=json.loads(logit_bias)
    print("model",model,prompt)
    idRequest = uuid.uuid4()

    message = {
        "id":idRequest,
        "model":model,
        "prompt":prompt,
        "max_tokens":max_tokens,
        "temperature":temperature,
        "n":n,
        "logprobs":logprobs,
        "stop":stop,
        "logit_bias":logit_bias,
        "init_from":init_from,
        "out_dir":out_dir
    }
    send_message(message)
    t_end = time.time() + 60 * 1
    while time.time() < t_end:
            if(redis.exists(idRequest)):
                result=redis.get(idRequest)
                result=json.loads(result)
                break
            else:
                result = False

    if result is False:
        return {
            "Status Code":400,
            "Error": "Data wasnt processed."
        }, 400   
        
    
    return result

def abuse_check(user, prompt):

    if user is not None and user in user_abuse and user_abuse[user]>=10:
        return {
            "Status Code":403,
            "Error": "Banned due to user abuse, please contact admin if you wish to be removed from the banned list"
        }, 403
    if prompt in banned_prompts:
        
        if user is not None and user not in user_abuse:
            user_abuse[user]=1
        elif user is not None:
            user_abuse[user]+=1
        return {
            "Status Code":400,
            "Error": "Banned Prompt, repeated Banned prompts will result in an API Ban"
        }
    return False   

def send_message(message):
    response = sqs.send_message(
        QueueUrl="https://us-west-2.queue.amazonaws.com/xxx/my-new-queue",
        MessageBody=json.dumps(message)
    )

    print(response)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")