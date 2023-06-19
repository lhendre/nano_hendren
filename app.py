from flask import Flask, request
from inference import Inference
import uuid
import time
import json

app = Flask(__name__)
app.config['DEBUG'] = True

user_abuse = {}
banned_prompts = {"How do i make a computer virus":True}
gpt_models = ['gpt2','gpt2-medium','gpt2-large','gpt2-xl']

threaded=True
@app.route("/completions", methods=['post'])
def completions():
    '''
    Completions post endpoint.  registers request and process

            Parameters:
                    request: arguments from user
            Returns:
                    result: result from processed request
    '''

    #gets and parses data
    model = request.args.get('model')
    prompt = request.args.get('prompt')
    suffix = request.args.get('suffix')
    max_tokens = request.args.get('max_tokens', type=int)
    temperature = request.args.get('temperature', type=float)
    n = request.args.get('n', type=int)
    logprobs = request.args.get('logprobs', type=int)
    echo = request.args.get('echo')
    stop = request.args.get('stop')
    presence_penalty = request.args.get('presence_penalty')
    frequency_penalty = request.args.get('frequency_penalty')
    best_of = request.args.get('best_of')
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

    #runs model    
    i = Inference(init_from=init_from,out_dir=out_dir,start=prompt,num_samples=n,max_new_tokens=max_tokens,temperature=temperature)
    r = i.run(stop=stop,logprobs=logprobs,logit_bias=logit_bias)
    idRequest = uuid.uuid4()
    ts = time.time()

    #set up results
    result = {
        "id": "cmpl-"+str(idRequest),
        "object": "text_completion",
        "created": ts,
        "model":    model,
        "choices": r,
    }
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

     

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")