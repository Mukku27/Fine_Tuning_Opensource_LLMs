# -*- coding: utf-8 -*-
"""Llama2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/16MZnBqWFwv51FjL_1dMYvs4qk3Wf42P9
"""

!pip install -q accelerate==0.21.0 peft==0.4.0 bitsandbytes==0.40.2 transformers==4.31.0 trl==0.4.7

import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    HfArgumentParser,
    TrainingArguments,
    pipeline,
    logging,
)
from peft import LoraConfig, PeftModel
from trl import SFTTrainer

"""# Prompt Template for Llama-2
System prompt  User Prompt

< INS T>SYS< INST >
< INST > QUESTION USER PROMPT< INST > MODEL ANSWER

# PEFT  LORA QLORA
***Parameter Efficient Finetuning Techniques***

1.  **Low Rank Adaption**
2.**Quantized Low Rank Adaption**

Qlora will use a rank 64 with a scaling parameter of 16.We'll load the llama 2 model directly in 4 bit precision using the NF4 type and train it for 3 epoch
"""

model_name='NousResearch/Llama-2-7b-chat-hf'
dataset_name='mlabonne/guanaco-llama2-1k'
new_model='llama-2-7b-FT'

#LORA Dimensions
lora_r=64
lora_alpha=16
lora_dropout=0.1

#bitsandbytes parameters
use_4bit=True
bnb_4bit_compute_dtype=torch.float16
use_nested_quant=False

#TrainingArguements parameters
output_dir="./results"
num_train_epochs=2

fp16=False
bf16=False
per_device_train_batch_size=4
per_device_eval_batch_size=4
gradient_accumulation_steps=1
gradient_checkpointing=True

max_grad_norm=0.3
learning_rate=2e-4
weight_decay=0.001
optim="paged_adamw_32bit"
lr_scheduler_type="cosine"

max_steps=-1
warmup_ratio=0.03
group_by_length=True
save_steps=25
logging_steps=25
eval_steps=25

#SFT parameters
max_seq_length=None
packing=False

#GPU0
device_map={"":0}

dataset=load_dataset(dataset_name,split="train")

compute_dtype= getattr(torch,'float16')
if compute_dtype==torch.float16 and use_4bit:
  compute_dtype=torch.bfloat16

print(f'compute_dtype: {compute_dtype}')

bnb_config=BitsAndBytesConfig(
    load_in_4bit=use_4bit,
    bnb_4bit_use_double_quant=use_nested_quant,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=compute_dtype,)


if compute_dtype==torch.float16 and use_4bit:
  major, _ = torch.cuda.get_device_capability()
  if major >= 8:
    print("=" * 80)
    print("Your GPU supports bfloat16: accelerate training with bf16=True")
    print("=" * 80)


model=AutoModelForCausalLM.from_pretrained(
    model_name,
    use_cache=False,
    quantization_config=bnb_config,
    device_map=device_map
)
model.config.use_cache=False
model.config.pretraining_tp=1

tokenizer=AutoTokenizer.from_pretrained(model_name,trust_remote_code=True)
tokenizer.pad_token=tokenizer.eos_token
tokenizer.padding_side="right"

peft_config=LoraConfig(
    lora_alpha=lora_alpha,
    lora_dropout=lora_dropout,
    r=lora_r,
    bias="none",
    task_type="CAUSAL_LM"
)

training_arguments=TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=num_train_epochs,
    per_device_train_batch_size=per_device_train_batch_size,
    gradient_accumulation_steps=gradient_accumulation_steps,
    optim=optim,
    save_steps=save_steps,
    logging_steps=logging_steps,
    learning_rate=learning_rate,
    weight_decay=weight_decay,
    fp16=fp16,
    bf16=bf16,
    max_grad_norm=max_grad_norm,
    max_steps=max_steps,
    warmup_ratio=warmup_ratio,
    group_by_length=group_by_length,
    lr_scheduler_type=lr_scheduler_type,
    report_to="tensorboard"
)

trainer=SFTTrainer(
    model=model,
    train_dataset=dataset,
    peft_config=peft_config,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    tokenizer=tokenizer,
    args=training_arguments,
    packing=packing,
)

model.config.use_cache=False

trainer.train()

trainer.model.save_pretrained(new_model)

trainer.model.save_pretrained(new_model)

# Commented out IPython magic to ensure Python compatibility.
# %load_ext tensorboard
# %tensorboard --logdir results/runs

logging.set_verbosity(logging.CRITICAL)

prompt="What is a facebook?"
pipe=pipeline(task="text-generation",model=model,tokenizer=tokenizer,max_length=200)

result=pipe(f'<s>[INST]{prompt}[/INST]')
print(result[0]['generated_text'])