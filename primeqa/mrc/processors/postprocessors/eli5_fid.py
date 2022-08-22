from primeqa.mrc.processors.postprocessors.abstract import AbstractPostProcessor
from primeqa.mrc.data_models.eval_prediction_with_processing import EvalPredictionWithProcessing
from transformers import PreTrainedTokenizerFast
from datasets import Dataset
from typing import List, Dict, Any, Tuple

class ELI5FiDPostProcessor(AbstractPostProcessor):
    """
    Post processor for extractive QA (use with `ExtractiveQAHead`).
    """
    def __init__(self,
                 *args,
                 tokenizer: PreTrainedTokenizerFast,
                 **kwargs):
        """
        Args:
            *args: Arguments for super class constructor.
            n_best_size: Max number of start/end logits to consider (max values).
            scorer_type: Scoring algorithm to use.
            **kwargs: Keyword Arguments for super class constructor.
        """
        super().__init__(*args, **kwargs)
        self.tokenizer = tokenizer
        
    def process(self, examples: Dataset, features: Dataset, predictions: tuple):
         # Decode the predicted tokens.
        preds = predictions.predictions
        if isinstance(preds, tuple):
            preds = preds[0]
        decoded_preds = self.tokenizer.batch_decode(preds, skip_special_tokens=True)

        # Build a map example to its corresponding features.
        example_id_to_index = {k: i for i, k in enumerate(examples["id"])} 

        feature_per_example = {example_id_to_index[feature["example_id"]]: i for i, feature in enumerate(features)}
        predictions = {}

        # Let's loop over all the examples!
        for example_index, example in enumerate(examples):
            # This is the index of the feature associated to the current example.
            feature_index = feature_per_example[example_index]
            predictions[example["id"]] = decoded_preds[feature_index]

        formatted_predictions = [{"id": k, "prediction_text": v} for k, v in predictions.items()]
        return formatted_predictions        

    
    def prepare_examples_as_references(self, examples: Dataset) -> List[Dict[str, Any]]:
        references = [{"id": ex["id"], "answers": [x["answer"] for x in ex['output'] if x["answer"] is not None]} for ex in examples] # muli references
        return references
    
    def process_references_and_predictions(self, examples, features, predictions) -> EvalPredictionWithProcessing:
        references = self.prepare_examples_as_references(examples)
        predictions = self.process(examples, features, predictions)

        return EvalPredictionWithProcessing(
            label_ids=references,
            predictions=predictions,
            processed_predictions=predictions
        )