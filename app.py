from flask import Flask, request
from inference import Inference
import uuid
import time

app = Flask(__name__)

user_abuse = {}
banned_prompts = {"How do i make a computer virus":True}

@app.route("/completions", methods=['post'])
def completions():
    model = request.args.get('model')
    prompt = request.args.get('prompt')
    suffix = request.args.get('suffix')
    max_tokens = request.args.get('max_tokens', type=int)
    temperature = request.args.get('temperature', type=float)
    n = request.args.get('n', type=int)
    logprobs = request.args.get('logprobs', type=float)
    echo = request.args.get('echo')
    stop = request.args.get('stop')
    presence_penalty = request.args.get('presence_penalty')
    frequency_penalty = request.args.get('frequency_penalty')
    best_of = request.args.get('best_of')
    logit_bias = request.args.get('logit_bias')
    user = request.args.get('user')

    check = abuse_check(user,prompt)
    if check != False:
        return check

    i = Inference(start=prompt,num_samples=n,max_new_tokens=max_tokens,temperature=temperature)
    r = i.run()

    idRequest = uuid.uuid4()
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
    return result

def abuse_check(user, prompt):

    if user is not None and user_abuse[user]>=10:
        return {
            "Status Code":403,
            "Error": "Banned due to user abuse, please contact admin if you wish to be removed from the banned list"
        }, 403
    print("prompt",prompt)
    print("D",banned_prompts[prompt])
    if prompt in banned_prompts:
        
        if user is not None and user_abuse[user] is None:
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