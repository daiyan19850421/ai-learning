# TokenTextSplitter 文档切分

`TokenTextSplitter` 按 token 数切分 Document，避免超出模型上下文。

常用参数：chunk size、chunk overlap。overlap 可保留段落边界上下文，减少语义断裂。

切分过大：检索粒度粗，噪声多。切分过小：语义不完整，召回片段缺背景。

Week 1 建议固定 chunk size 做 baseline，Week 2 用 golden set 对比调参。
