# nanoGPT Take Home Project

This is a take home project.  I made4 inference of NanoGPT available over an HTTP endpoint that supports a subset of the OpenAI completions API (https://platform.openai.com/docs/api-reference/completions).  It supports prompt, max_tokens, stop, n, logprobs, temperature, user, and logit_bias.  It also allows you to switch between models.  

Models avaiable are gpt2, gpt2_medium, gpt2_large, gtp_xl, nano_gpt's shakespeare, nano_gpt's shakespear finetune, and a final model I made that is a deeper and wider version of shakespeare.  It should be noted the ability to timely run these models is dependent on the hardware you use and batch size has an effect.

Additionally, there is a simple abuse checker for banned or abusive users. 

There is has also been data paralleism added to this with DataParallel being added to the model.  I added a few layers of this.  As I will get into later, It didnt significantly boost efficiency due to machine limitiations.  Additionally, torchrun allows for more gpu usage depending on usage.

There are also two ways to run this application.  App.py will run it all within a single service.  Running a combination of app_web_server.py/wsgi.py and processor.py will break up the service with a pub sub queue and redis server for better scaling.



## install

Dependencies:

- [pytorch](https://pytorch.org) 
- [numpy](https://numpy.org/install/) 
- `pip install transformers` for huggingface transformers  (to load GPT-2 checkpoints)
- `pip install datasets` for huggingface datasets  (if you want to download + preprocess OpenWebText)
- `pip install tiktoken` for OpenAI's fast BPE code 
- `pip install wandb` for optional logging 
- `pip install tqdm` 
- `pip install -U Flask`
- `pip install boto3`
- `pip install redis`

## quick start

Follow the readme instructions for installation and environment setup, be sure to install flask/guinicorn, boto3 and redis additionally, setup a config file with your aws keys, follow instructions for setting gup redis and your sqs service and creating your models.

After following the previous readme for setting up your environment(including data and model setup).  To run the single server version, which doesnt require redis or sqs,  do the following 
```
$ python app.py
```

To run the multi server version, on one server rune
```
$ gunicorn --bind=0.0.0.0:5000 --timeout 600 wsgi:app 
```

and on the other run
```
$ python processor.py
```

Make sure your config file, sqs and redis server are running for this.


## Methology and Results

Overall, I deployed a scalable server providing much functionality of the completion api from openai which, a video of the results can be seen below.

[Demo](https://drive.google.com/file/d/1-x2gmj_km3pddwV341Vcqn5rgbAHfV6m/view?usp=drive_link)


I started off by building a simpel single server version that accomplished the base goals, then expanded to include additional parameters, the model switching and mulit-gpu.

I did a simple version of the multi-gpu setup just because of resource resctrictions with DataParallel.  Testing on multi gpus is resource expensive and would significantly up the cost, as such I installed a basic level and examples of it that could be expanded later.  Overall, the current level of it doesnt do much to boost the results, primarily due to batch size restrictions on the hardware I am using, but they provide a framework going forward.  Additionally, as I will go into, the more advance setup has the api turned into a seperate server from the portion of the code that process the data, for that I used guinicorn which allows a user to easily make that process have multiple workers In the future, as better hardware would be available, I would increase the batch sizes which would allow DataParallel to function more powerfully. 

For hardware, I started by running this locally on my mac to ensure everything ran, then upgraded to a server with a single gpu for testing, then finally a multi-gpu server for final testing.  I wasnt able to test it on more production size servers. To follow both nano-gpts suggestion, or from my own experience, I would want a multi gpu server with A100s, which would cost 30-40 dollars and would have a decent costs for this.  

For the parameters, some came built in with nano-gpt, others like stop, logprob and logit_bias I needed to add in.  I wanted to do a combination of them to show my skill set then move on to other items.

I also wanted to include a small custom model as a demonstration of experience in dealing with models.  It was fairly limited, as I dont expect to be able to get better results in a short time frame then gpt2 and would rather focus on efficiencies and features.

I also added the base user check for fraud and testing as a sample of future features.

Based on my experience, scaling and making systems more efficient seemed like a good use of time.  As such, after getting the first version working. I broke this system up into one server to take in requests, and another to process requests.  This is a better and more scalable system as you can now ensure no request gets dropped and resources are managed appropriately.  I went with your suggestions, as a future change, I woudl suggest considering having another endpoint(get), to get the requests.  Some of these requests can take a long time to process, it maybe better to have the user intermittently poll to see if their request is done processing instead of waiting.  There are other improvements that can be made as well but this break up of tasks into seperate processes seems like a good step.

For server hosting.  It was primarily based on available credits.  Azure would normally be my first choice; however, I recently completed a graduate certificate course through Stanford and gained access to aws credits for it, allowing me to use better servers then my current hardware for free.  You can sub out sqs for the azure service bus, and azure cache for redis and make the switch fairly easily.  For final testing i used a Deep Learning AMI GPU PyTorch 1.13.1 (Ubuntu 20.04) with a g4dn.12xlarge.  For production in azure I would likely start testing with a ND A100 v4-series and for dev work I would likely start looking at the NC-series


One additional note on methodology.  It was my goal to keep changes to nano-gpt itself to a minimum for this excersize.  Firstly, I didnt want to waste time and resources reinventing the wheel when unnecessary.  Secondly, every change increases the likihood of bugs which I sought to keep at a mimimum.


Overall, I believe the results are good.  This added in alot of the functionality of the openai endpoint, in a highly scalable matter.  The processing time is a bit slow(~1 minute for normal shakespeare, ~2 minutes and 40 seconds for gpt2), but results on that are partially limited due to hardware constraints.
