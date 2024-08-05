import os
import copy

import json
import logging
import pathlib
import torch
import random
import transformers
import tokenizers
from PIL import Image
from typing import Dict, Optional, Sequence, List
from dataclasses import dataclass, field
from torch.utils.data import Dataset
local_rank = None


def rank0_print(*args):
    if local_rank == 0:
        print(*args)

@dataclass
class DataArguments:
	data_path: str = field(default=None,
	                       metadata={"help": "Path to the training data."})
	lazy_preprocess: bool = False
	is_multimodal: bool = False
	image_folder: Optional[str] = field(default=None)
	image_aspect_ratio: str = 'square'
	more_data: Optional[str] = field(default=None) # new add


class LazySupervisedDataset(Dataset):
	"""Dataset for supervised fine-tuning."""

	def __init__(self, data_path: str,
	             tokenizer: transformers.PreTrainedTokenizer,
	             data_args: DataArguments):
		super(LazySupervisedDataset, self).__init__()
		list_data_dict = json.load(open(data_path, "r"))
		rank0_print(f"Total count of list_data_dict load from {data_path}: {len(list_data_dict)}")

        # new add
		if data_args.more_data is not None and data_args.more_data != "":
			rank0_print("Append more data.")
			more_data_dict = self.load_self_defined_data(data_args.more_data)
			list_data_dict += more_data_dict
			rank0_print(f"Total count of list_data_dict after append data.: {len(list_data_dict)}")

		rank0_print("Formatting inputs...Skip in lazy mode")

		self.tokenizer = tokenizer
		self.list_data_dict = list_data_dict
		self.data_args = data_args

	def __len__(self):
		return len(self.list_data_dict)

	@property
	def lengths(self):
		length_list = []
		for sample in self.list_data_dict:
			img_tokens = 128 if 'image' in sample else 0
			length_list.append(sum(len(conv['value'].split()) for conv in sample['conversations']) + img_tokens)
		return length_list

	@property
	def modality_lengths(self):
		length_list = []
		for sample in self.list_data_dict:
			try:
				cur_len = sum(len(conv['value'].split()) for conv in sample['conversations'])
				cur_len = cur_len if 'image' in sample else -cur_len
				length_list.append(cur_len)
			except Exception as e:
				rank0_print(f'modality_lengths line 701 {repr(e)}')
				rank0_print(sample)
				raise e

		return length_list

	def __getitem__(self, i) -> Dict[str, torch.Tensor]:
		image_folder = None
		image_file = None
		flag = False
		while not flag:
			try:
				sources = self.list_data_dict[i]
				if isinstance(i, int):
					sources = [sources]
				assert len(sources) == 1, "Don't know why it is wrapped to a list"  # FIXME
				if 'image' in sources[0]:
					image_file = self.list_data_dict[i]['image']
					image_folder = self.data_args.image_folder
					processor = self.data_args.image_processor
					image = Image.open(os.path.join(image_folder, image_file)).convert('RGB')
					if self.data_args.image_aspect_ratio == 'pad':
						def expand2square(pil_img, background_color):
							width, height = pil_img.size
							if width == height:
								return pil_img
							elif width > height:
								result = Image.new(pil_img.mode, (width, width), background_color)
								result.paste(pil_img, (0, (width - height) // 2))
								return result
							else:
								result = Image.new(pil_img.mode, (height, height), background_color)
								result.paste(pil_img, ((height - width) // 2, 0))
								return result

						image = expand2square(image, tuple(int(x * 255) for x in processor.image_mean))
						image = processor.preprocess(image, return_tensors='pt')['pixel_values'][0]
					else:
						image = processor.preprocess(image, return_tensors='pt')['pixel_values'][0]
					sources = preprocess_multimodal(
						copy.deepcopy([e["conversations"] for e in sources]),
						self.data_args
					)
				else:
					sources = copy.deepcopy([e["conversations"] for e in sources])

				data_dict = preprocess(
					sources,
					self.tokenizer,
					has_image=('image' in self.list_data_dict[i])
				)
				if isinstance(i, int):
					data_dict = dict(
						input_ids=data_dict["input_ids"][0],
						labels=data_dict["labels"][0]
					)

				# image exist in the data
				if 'image' in self.list_data_dict[i]:
					data_dict['image'] = image
				elif self.data_args.is_multimodal:
					# image does not exist in the data, but the model is multimodal
					crop_size = self.data_args.image_processor.crop_size
					data_dict['image'] = torch.zeros(3, crop_size['height'], crop_size['width'])

				flag = True
			except Exception as e:
				rank0_print(f"{repr(e)} image file can't open {image_folder} {image_file}")
				i = random.randint(0, len(self.list_data_dict) - 1)

		return data_dict

	def get_json_files(self, data_dir):
		json_files = []
		# 递归遍历目录，可以读到链接文件
		for root, dirs, files in os.walk(data_dir, followlinks=True):
			for file in files:
				if file.endswith('.json'):
					json_files.append(os.path.join(root, file))
		return json_files

	def load_self_defined_data(self, data_dir):
		more_data_dict = []
		json_files = None
		if data_dir.endswith('.json'):
			json_files = [data_dir]
		else:
			json_files = self.get_json_files(data_dir)
			
		for more_data_path in json_files:
			more_data = json.load(open(more_data_path, "r"))
			rank0_print(f"Count of {more_data_path}: {len(more_data)}")
			# rank0_print(more_data[0])

			more_data_dict += more_data

		rank0_print(f"Total json file {len(json_files)}")
		rank0_print(f"Total Count {len(more_data_dict)}")
		rank0_print(type(more_data_dict))
		rank0_print(more_data_dict[0])
		return more_data_dict
