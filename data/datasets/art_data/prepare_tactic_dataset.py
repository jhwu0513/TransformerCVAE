import os
import random
import yaml

# 创建一个空字典
technique_to_tactic = {}

# 打开txt文件进行读取
with open('technique2tactic.txt', 'r') as file:
    # 逐行读取文件内容
    for line in file:
        # 分割每一行，并去除空格
        data = line.strip().split(' ',1)
        # 将读取的内容添加到字典中
        technique_to_tactic[data[0]] = data[1]

# 打印字典
# print(technique_to_tactic)
tactic_sample = {}

executors = {}
yaml_paths = []
cls = {}
cls_idx = 0
num_cls = {}

def truncate_string_at_dot(input_string):
    dot_index = input_string.find('.')
    if dot_index != -1:
        return input_string[:dot_index]
    else:
        return input_string


print('Collecting atomic red team yaml files ...')
techniques = [t for t in os.listdir('./atomic-red-team/atomics') if t.startswith('T')]
for t in techniques:
    technique_path = os.path.join('./atomic-red-team/atomics', t)
    yaml_file = [y for y in os.listdir(technique_path) if y.startswith('T') and y.endswith('.yaml')][0]
    yaml_path = os.path.join(technique_path, yaml_file)
    yaml_paths.append(yaml_path)

print('Parsing yaml files ...')
for y in yaml_paths:
    # print(y)
    with open(y, 'r') as f:
        data = yaml.safe_load(f)
        for test in data['atomic_tests']:
            if 'command' not in test['executor']: continue # 如果沒有payload，就跳過

            if test['executor']['name'] in ['powershell', 'cmd', 'command_prompt'] :
                payload = ';'.join([c for c in test['executor']['command'].strip('\n').split('\n')]) # payload 儲存一個 atomic test 的 command
            elif test['executor']['name'] in ['sh', 'bash']:
                payload = '&&'.join([c for c in test['executor']['command'].strip('\n').split('\n')])
            else: print(f"unknown name {test['executor']['name']}")

            if technique_to_tactic[truncate_string_at_dot(data['attack_technique'])] not in executors: # executors 裡面存放 {'Tactic Name':[ Payload List ]}
                executors[technique_to_tactic[truncate_string_at_dot(data['attack_technique'])]] = [payload] # executors 紀錄所有 Tactic 的 payload
                cls[technique_to_tactic[truncate_string_at_dot(data['attack_technique'])]] = cls_idx # cls 用來記錄 tactic 對應的 Label ID，cls = {Tactic Name : Tactic Label ID}
                cls_idx += 1
                num_cls[technique_to_tactic[truncate_string_at_dot(data['attack_technique'])]] = 1
            else:
                executors[technique_to_tactic[truncate_string_at_dot(data['attack_technique'])]].append(payload)
                num_cls[technique_to_tactic[truncate_string_at_dot(data['attack_technique'])]] += 1

ratio = 0.9
train = []
test = []
print(f"Splitting train and test with ratio {ratio} ...")

for t, ps in executors.items(): # 遍歷 executors 的鍵值對，executors 是一個 dictionary
    split_idx = int(0.9*len(ps))
    for p in ps[:split_idx]:
        pline = [p for p in p.split('\n')]
        train.append((cls[t], p)) # 將 (Tactic Label ID, Payload) 加入到 train 中
    for p in ps[split_idx:]:
        test.append((cls[t], p))

print(f"Train: {len(train)}")
print(f"Test: {len(test)}")
print(f"Total number of techniques: {len(cls)}")

print('Shuffling ...')
random.shuffle(train) # 將 train 中的元素作隨機排序，打亂 List 的元素順序
random.shuffle(test)

print('Writing to files ...')
# VAE
with open('train_tactic_vae.txt', 'w') as f:
    for cls_idx, p in train:
        f.write(p + '\n')
with open('test_tactic_vae.txt', 'w') as f:
    for cls_idx, p in test:
        f.write(p + '\n')

# Classifier
with open('train_tactic_cls.txt', 'w') as f:
    for cls_idx, p in train:
        f.write(f"{cls_idx}\t{p}\n")
with open('test_tactic_cls.txt', 'w') as f:
    for cls_idx, p in test:
        f.write(f"{cls_idx}\t{p}\n")

# GAN
with open('train_tactic_gan.txt', 'w') as f:
    for cls_idx, p in train:
        f.write(f"0\t{p}\n")
with open('test_tactic_gan.txt', 'w') as f:
    for cls_idx, p in test:
        f.write(f"0\t{p}\n")

# Tactic, Class, Count
with open('tactic_cls_c.txt', 'w') as f:
    f.write('tactic, class, count\n')
    for t in cls:
        f.write(f"{t} {cls[t]} {num_cls[t]}\n")