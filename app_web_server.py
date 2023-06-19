from flask import Flask, request
import uuid
import time
import json
from redis import Redis
import boto3
import config as cfg

app = Flask(__name__)
app.config['DEBUG'] = True
redis = Redis(host="nano-s.b7yglw.ng.0001.use2.cache.amazonaws.com", port=6379, decode_responses=True, db=0)
sqs = boto3.client('sqs', region_name='us-east-2',aws_access_key_id=cfg.aws_access_key_id, aws_secret_access_key=cfg.aws_secret_access_key)
QueueUrl = sqs.get_queue_url(QueueName="nano.fifo")


user_abuse = {}
banned_prompts = {"How do i make a computer virus":True}
gpt_models = ['gpt2','gpt2-medium','gpt2-large','gpt2-xl']
@app.route("/completions", methods=['post'])
def completions():
    '''
    Completions post endpoint.  registers request to process then waits for response

            Parameters:
                    request: arguments from user
            Returns:
                    result: result from processed request
    '''
    #Gets and set up arguments
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
    
    idRequest = uuid.uuid4().int
    #message for queue
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
        "out_dir":out_dir,
    }
    #sends message
    send_message(message,idRequest)

    #waits 10 minutes for possible response on redis server before returning erro
    t_end = time.time() + 600 * 1
    while time.time() < t_end:
            if(redis.exists(str(idRequest))):
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
    
    #return results
    print("result:",result)
    return result

def abuse_check(user, prompt):
    '''
    Checks for and registers users abuse

            Parameters:
                    user: user id to check if user is banned or register abuse
                    prompt: promt to check for abuse            
    '''
    #checks for banned use
    if user is not None and user in user_abuse and user_abuse[user]>=10:
        return {
            "Status Code":403,
            "Error": "Banned due to user abuse, please contact admin if you wish to be removed from the banned list"
        }, 403
    #checks for banned prompts
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

def send_message(message,idMessaageGroup):
    '''
    Sends message to backend process for processing via sqs service.

            Parameters:
                    message: message to send with data for model
                    idMessaageGroup: uuid of the request                   
    '''
    response = sqs.send_message(
        MessageGroupId=str(idMessaageGroup),
        QueueUrl=QueueUrl["QueueUrl"],
        MessageBody=json.dumps(message),
        MessageDeduplicationId=str(idMessaageGroup)
    )

    print(response)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")