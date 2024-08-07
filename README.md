# MMInstruct

The official implementation of the paper "[MMInstruct: A High-Quality Multi-Modal Instruction Tuning Dataset with Extensive Diversity](http://arxiv.org/abs/2407.15838)".

The dataset is available on Hugging Face at [yuecao0119/MMInstruct](https://huggingface.co/datasets/yuecao0119/MMInstruct).

## Todo List

- [x] Data Engine.
- [x] Open Source Datasets.
- [ ] Release the checkpoint.

## Introduction

### Data composition 

The open source datasets on Hugging Face [yuecao0119/MMInstruct](https://huggingface.co/datasets/yuecao0119/MMInstruct) include:

* `caption_cn`: 144K English detailed image caption data generated using *gpt-4-vision-preview*.
* `caption_en`: 18.2K Chinese detailed image caption data generated using *gpt-4-vision-preview*.
* `qa_en`: 216K instruction data generated using *GPT-3.5-turbo*, including 161K multi-round long questions and answers and 55K manually corrected instruction data from 23 fields, as shown in the figure below.

<image src='figs/example_in_domain.png'></image>

## Dataset Expansion

we also expand MMInstruct with other open source data, including:

| Domain                 | Dataset                                                      |
| -------------------- | ------------------------------------------------------------ |
| mathematics datasets | [GEOS](https://aclanthology.org/D15-1171.pdf); [UniGeo](https://arxiv.org/abs/2212.02746); [GeoQA+](https://aclanthology.org/2022.coling-1.130/); [Geometry3k](https://arxiv.org/abs/2105.04165); [CLEVR-Math](https://arxiv.org/abs/2208.05358); [Supre-CLEVR](https://openaccess.thecvf.com/content/CVPR2023/html/Li_Super-CLEVR_A_Virtual_Benchmark_To_Diagnose_Domain_Robustness_in_Visual_CVPR_2023_paper.html); [TabMWP](https://arxiv.org/abs/2209.14610) |
| charts and plots     | [DVQA(100K)](https://openaccess.thecvf.com/content_cvpr_2018/html/Kafle_DVQA_Understanding_Data_CVPR_2018_paper.html); [FigureQA](https://arxiv.org/abs/1710.07300) |
| scientific figure    | [TQA](https://openaccess.thecvf.com/content_cvpr_2017/html/Kembhavi_Are_You_Smarter_CVPR_2017_paper.html) |
| map chart            | [MapQA](https://arxiv.org/abs/2211.08545)                    |




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
