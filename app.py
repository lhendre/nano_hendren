from flask import Flask, request
from inference import Inference

app = Flask(__name__)

@app.route("/completions", methods=['post'])
def completions():
    model = request.args.get('model')
    prompt = request.args.get('prompt')
    suffix = request.args.get('suffix')
    max_tokens = request.args.get('max_tokens')
    n = request.args.get('n')
    logprobs = request.args.get('logprobs')
    echo = request.args.get('echo')
    stop = request.args.get('stop')
    presence_penalty = request.args.get('presence_penalty')
    frequency_penalty = request.args.get('frequency_penalty')
    best_of = request.args.get('best_of')
    logit_bias = request.args.get('logit_bias')
    user = request.args.get('user')
    i = Inference()
    r=i.run()
    print("r",r)

    print("test",model,prompt,suffix,max_tokens)
    return "Hello, World!"
