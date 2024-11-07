# MMInstruct

The official implementation of the paper "[MMInstruct: A High-Quality Multi-Modal Instruction Tuning Dataset with Extensive Diversity](http://arxiv.org/abs/2407.15838)".

The dataset is available on Hugging Face at [🤗 yuecao0119/MMInstruct](https://huggingface.co/datasets/yuecao0119/MMInstruct-GPT4V).

## 📣 News

- **[Oct 14, 2024]** Our paper is accepted by SCIENCE CHINA Information Sciences!
- **[Aug 6, 2024]**  The dataset is already accessible on Hugging Face at [🤗 yuecao0119/MMInstruct](https://huggingface.co/datasets/yuecao0119/MMInstruct-GPT4V).
- **[Jul 22, 2024]** The paper has been released on [arXiv](https://arxiv.org/abs/2407.15838)!
- **[Jul 22, 2024]** Code has been released.

## Todo List

- [x] Data Engine.
- [x] Open Source Datasets.
- [ ] Release the checkpoint.

## Introduction

Vision-language supervised fine-tuning effectively enhances VLLM performance, but existing visual instruction tuning datasets have limitations:

1. **Instruction Annotation Quality**: Despite strong performance, advanced VLLMs may generate instructions with inaccuracies, such as hallucinations.
2. **Instruction and Image Diversity**: Limited instruction types and lack of diverse image data impact the model's ability to generate varied and realistic outputs.


### MMInstruct Dataset

To address these challenges, we created the MMInstruct dataset, featuring:
- **973K instructions** from **24 domains**
- Four instruction types: Judgement, Multiple-Choice, Long Visual Question Answering, and Short Visual Question Answering.

<img width="1117" alt="image" src="https://github.com/user-attachments/assets/92ef8128-89e3-4891-9dad-6c64da2c9de3">

The open source datasets on Hugging Face [🤗 yuecao0119/MMInstruct](https://huggingface.co/datasets/yuecao0119/MMInstruct-GPT4V) include:

* `caption_cn`: 144K English detailed image caption data generated using *gpt-4-vision-preview*.
* `caption_en`: 18.2K Chinese detailed image caption data generated using *gpt-4-vision-preview*.
* `qa_en`: 216K instruction data generated using *GPT-3.5-turbo*, including 161K multi-round long questions and answers and 55K manually corrected instruction data from 23 fields, as shown in the figure below.

We also expand MMInstruct with other open-source data, including:

| Domain                 | Dataset                                                      |
| -------------------- | ------------------------------------------------------------ |
| mathematics datasets | [GEOS](https://aclanthology.org/D15-1171.pdf); [UniGeo](https://arxiv.org/abs/2212.02746); [GeoQA+](https://aclanthology.org/2022.coling-1.130/); [Geometry3k](https://arxiv.org/abs/2105.04165); [CLEVR-Math](https://arxiv.org/abs/2208.05358); [Supre-CLEVR](https://openaccess.thecvf.com/content/CVPR2023/html/Li_Super-CLEVR_A_Virtual_Benchmark_To_Diagnose_Domain_Robustness_in_Visual_CVPR_2023_paper.html); [TabMWP](https://arxiv.org/abs/2209.14610) |
| charts and plots     | [DVQA (100K)](https://openaccess.thecvf.com/content_cvpr_2018/html/Kafle_DVQA_Understanding_Data_CVPR_2018_paper.html); [FigureQA](https://arxiv.org/abs/1710.07300) |
| scientific figure    | [TQA](https://openaccess.thecvf.com/content_cvpr_2017/html/Kembhavi_Are_You_Smarter_CVPR_2017_paper.html) |
| map chart            | [MapQA](https://arxiv.org/abs/2211.08545)                    |

### Data Engine

We developed an instruction generation data engine leveraging GPT-4V, GPT-3.5, and manual correction. This engine allows semi-automatic, low-cost, multi-domain instruction generation at 1/6 the cost of manual construction.

<img width="1589" alt="image" src="https://github.com/user-attachments/assets/8513df0f-f3d3-4145-bc81-baa1db656a4e">

As described in [our paper](http://arxiv.org/abs/2407.15838), we mainly proposed a semi-automatic and low-cost instruction generation data engine using GPT-4V, GPT-3.5 and manual correction. Our data engine consists of six steps: (a) image collection, (b) image caption generation, (c) seed question collection, (d) automatic instruction generation, (e) dataset expansion and (f) manual correction.

(a) First, we collect a large number of different images from various sources, which are mainly obtained through some selected source images, and then retrieved by crawlers and clips, etc., as shown in [image_retrieval_bing_spider.py](https://github.com/yuecao0119/MMInstruct/blob/main/data_engine/image_retrieval_bing_spider.py) and [image_retrieval_clip.py](https://github.com/yuecao0119/MMInstruct/blob/main/data_engine/image_retrieval_clip.py).

(b) And use GPT-4V to generate detailed image captions, as shown in [gpt4v_caption.py](https://github.com/yuecao0119/MMInstruct/blob/main/data_engine/gpt4v_caption.py).

(c) Then experts designed corresponding [seed questions](https://github.com/yuecao0119/MMInstruct/tree/main/data_engine/all_seed) for different fields. 

(d) We use image captions and seed questions to automatically generate a rich and diverse set of instruction data through GPT-3.5, as shown in [gpt35_qa.py](https://github.com/yuecao0119/MMInstruct/blob/main/data_engine/gpt35_qa.py).

(e), (f) In addition, we also use various methods to expand our dataset. Finally, manual correction is performed to ensure data quality and accuracy.


### Performance

<img width="1220" alt="image" src="https://github.com/user-attachments/assets/eca16ea4-8e73-4e92-8a5b-3036557abb94">

## Citation

If this work is helpful for your research, please consider citing the following BibTeX entry.

```
@article{liu2024mminstruct,
  title={MMInstruct: A High-Quality Multi-Modal Instruction Tuning Dataset with Extensive Diversity},
  author={Liu, Yangzhou and Cao, Yue and Gao, Zhangwei and Wang, Weiyun and Chen, Zhe and Wang, Wenhai and Tian, Hao and Lu, Lewei and Zhu, Xizhou and Lu, Tong and others},
  journal={arXiv preprint arXiv:2407.15838},
  year={2024}
}
```
