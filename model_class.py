
class model:

    def __init__(self, clean_data, feature_engineering, sk_model):
        self._model = sk_model
        self._clean_data_function = clean_data
        self._feature_engineering_function = feature_engineering

    def init_data(self, dataset):
        self._data = dataset.copy()

        self._clean_dataset()

        self._feature_engineering()

    def _clean_dataset(self):
        self._clean_data_function(self._data)

    def _feature_engineering(self):
        self._feature_engineering_function(self._data)

    def predict(self):
        self.predictions = self._model.predict(self._data)
        return self.predictions

    def get_predictions(self):
        return self._data["pred"]
