"""
Sample from a trained model
"""
import os
import pickle
from contextlib import nullcontext
import torch
import tiktoken
from model import GPTConfig, GPT
class Inference():
    """ class for preparing an drunning inference """

    def __init__(self,
        init_from = 'resume', # either 'resume' (from an out_dir) or a gpt2 variant (e.g. 'gpt2-xl')
        out_dir = 'out-shakespeare-char', # ignored if init_from is not 'resume'
        start = "\n", # or "<|endoftext|>" or etc. Can also specify a file, use as: "FILE:prompt.txt"
        num_samples = 10, # number of samples to draw
        max_new_tokens = 500, # number of tokens generated in each sample
        temperature = 0.8, # 1.0 = no change, < 1.0 = less random, > 1.0 = more random, in predictions
        top_k = 200, # retain only the top_k most likely tokens, clamp others to have 0 probability
        seed = 1337,
        device = 'cuda', # examples: 'cpu', 'cuda', 'cuda:0', 'cuda:1', etc.
        dtype = 'bfloat16' if torch.cuda.is_bf16_supported() else 'float16', # 'float32' or 'bfloat16' or 'float16'
        compile = False # use PyTorch 2.0 to compile the model to be faster
    ):
    '''
    Init.  Initializes inference class.  Description of arguments above
    '''
        self.init_from = init_from if init_from is not None else 'resume'
        self.out_dir = out_dir if out_dir is not None else 'shakespeare'
        self.start = start if start is not None else "\n"
        self.num_samples = num_samples if num_samples is not None else 10
        self.max_new_tokens = max_new_tokens if max_new_tokens is not None else 500
        self.temperature = temperature if temperature is not None else .8
        self.top_k = top_k if top_k is not None else 200
        self.seed = seed if seed is not None else 1337
        self.device = device if device is not None else 'cuda'
        self.dtype = dtype if dtype is not None else 'bfloat16' if torch.cuda.is_bf16_supported() else 'float16'
        self.compile = compile if compile is not None else False
        # This caused issues with guinicorn.  Overall I prefer to setup a config file then this method
        # exec(open('configurator.py').read()) # overrides from command line or config file
        print("Prompt",start)
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.backends.cuda.matmul.allow_tf32 = True # allow tf32 on matmul
        torch.backends.cudnn.allow_tf32 = True # allow tf32 on cudnn
        self.device_type = 'cuda' if 'cuda' in self.device else 'cpu' # for later use in torch.autocast
        self.ptdtype = {'float32': torch.float32, 'bfloat16': torch.bfloat16, 'float16': torch.float16}[dtype]
        self.ctx = nullcontext() if self.device_type == 'cpu' else torch.amp.autocast(device_type=self.device_type, dtype=self.ptdtype)

    def run(self, stop=None, logprobs=None, logit_bias=None):

        # model
        if self.init_from == 'resume':
            # init from a model saved in a specific directory
            ckpt_path = os.path.join(self.out_dir, 'ckpt.pt')
            checkpoint = torch.load(ckpt_path, map_location=self.device)
            gptconf = GPTConfig(**checkpoint['model_args'])
            model = GPT(gptconf)
            state_dict = checkpoint['model']
            unwanted_prefix = '_orig_mod.'
            for k,v in list(state_dict.items()):
                if k.startswith(unwanted_prefix):
                    state_dict[k[len(unwanted_prefix):]] = state_dict.pop(k)
            model.load_state_dict(state_dict)
        elif self.init_from.startswith('gpt2'):
            # init from a given GPT-2 model
            model = GPT.from_pretrained(self.init_from, dict(dropout=0.0))

        model.eval()
        model.to(self.device)
        if compile:
            model = torch.compile(model) # requires PyTorch 2.0 (optional)

        # look for the meta pickle in case it is available in the dataset folder
        load_meta = False
        if self.init_from == 'resume' and 'config' in checkpoint and 'dataset' in checkpoint['config']: # older checkpoints might not have these...
            meta_path = os.path.join('data', checkpoint['config']['dataset'], 'meta.pkl')
            load_meta = os.path.exists(meta_path)
        if load_meta:
            print(f"Loading meta from {meta_path}...")
            with open(meta_path, 'rb') as f:
                meta = pickle.load(f)
            # TODO want to make this more general to arbitrary encoder/decoder schemes
            stoi, itos = meta['stoi'], meta['itos']
            encode = lambda s: [stoi[c] for c in s]
            decode = lambda l: ''.join([itos[i] for i in l])
        else:
            # ok let's assume gpt-2 encodings by default
            print("No meta.pkl found, assuming GPT-2 encodings...")
            enc = tiktoken.get_encoding("gpt2")
            encode = lambda s: enc.encode(s, allowed_special={"<|endoftext|>"})
            decode = lambda l: enc.decode(l)

        # encode the beginning of the prompt
        if self.start.startswith('FILE:'):
            with open(self.start[5:], 'r', encoding='utf-8') as f:
                self.start = f.read()
        start_ids = encode(self.start)
        x = (torch.tensor(start_ids, dtype=torch.long, device=self.device)[None, ...])

        # run generation - Modified to add in new arguments and setup result object
        results = []
        with torch.no_grad():
            with self.ctx:
                for k in range(self.num_samples):
                    y, finish_reason, top_logprobs, tokens, token_logprobs = model.generate(x, self.max_new_tokens, temperature=self.temperature, top_k=self.top_k, stop=stop, logprobs=logprobs,decode=decode, logit_bias=logit_bias)
                    print(decode(y[0].tolist()))
                    print('---------------')
                    final_log_prob = {
                            "tokens":tokens,
                            "token_logprobs":token_logprobs,
                            "top_logprobs":top_logprobs,
                        }
                    if len(top_logprobs) == 0:
                        final_log_prob = None
                    result={
                        "text":decode(y[0].tolist()),
                        "index":k,
                        "logprobs":final_log_prob,
                        "finish_reason":finish_reason
                    }
                    results.append(result)
        return results
