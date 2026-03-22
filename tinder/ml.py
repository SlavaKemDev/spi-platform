import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel


class TinderML:
    tokenizer = None
    model = None

    @staticmethod
    def init():
        if TinderML.tokenizer is None:
            print("Loading tokenizer...")
            TinderML.tokenizer = AutoTokenizer.from_pretrained("cointegrated/LaBSE-en-ru")
        if TinderML.model is None:
            print("Loading model...")
            TinderML.model = AutoModel.from_pretrained("cointegrated/LaBSE-en-ru")

    @staticmethod
    def get_embeddings(texts: list | str, max_length=256) -> np.ndarray:
        is_str = isinstance(texts, str)
        if is_str:
            texts = [texts]

        TinderML.init()

        encoded_input = TinderML.tokenizer(texts, padding=True, truncation=True, max_length=max_length, return_tensors='pt')
        with torch.no_grad():
            model_output = TinderML.model(**encoded_input)
        embeddings = model_output.pooler_output
        embeddings = torch.nn.functional.normalize(embeddings).cpu().numpy()

        if is_str:
            return embeddings[0]
        return embeddings
