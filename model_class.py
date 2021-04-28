
from random import sample, uniform, seed, randint
import numpy as np
import seaborn as sns
from sklearn.metrics import r2_score

class model:

    def __init__(self, get_data, clean_data, feature_engineering, sk_model):
        self._model = sk_model
        self._get_data_function = get_data
        self._clean_data_function = clean_data
        self._feature_engineering_function = feature_engineering

    def init_data(self, fpl):
        
        self._data = self._get_dataset(fpl)

        self._clean_dataset(self._data)

        self._feature_engineering(self._data)

    def _get_dataset(self, fpl):
        self._data = self._get_data_function(fpl)
        
    def _clean_dataset(self):
        self._clean_data_function(self._data)

    def _feature_engineering(self):
        self._feature_engineering_function(self._data)

    def predict(self):
        self.predictions = self._model.predict(self._data)
        return self.predictions

    def get_predictions(self):
        return self._data["pred"]

class modeler:
    
    def __init__(self, X_train, X_test, y_train, y_test, random_seed = 1):
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self._models = {
            "params" : [],
            "model": [],
            "score" : [],
            "score_details" : []
        }
        self.seed = random_seed
        seed(random_seed)
        
    def _generate_k_fold(self, n):
        from sklearn.model_selection import KFold
        self._folds = KFold(n_splits = n, shuffle = True, random_state  = self.seed)
        
    def _select_params(self, parameters):
        params = {}
        for p in parameters.keys():
            if type(parameters[p]) != tuple:
                continue
            if type(parameters[p][0]) == int:
                params[p] = randint(parameters[p][0], parameters[p][1])
            else:
                params[p] = uniform(parameters[p][0], parameters[p][1])
        return params
        
    def _declare_model(self, model, parameters):
        params = self._select_params(parameters)
        if parameters["name"] == "random_forest":
            return model(
                n_estimators = params["estimators"],
                max_depth = params["max_depth"],
                min_samples_split = params["min_samples_split"],
                max_features = params["max_features"],
                ccp_alpha = params["ccp_alpha"]
            ), params
        
    def train(self, model, parameters, kfolds = 5, models = 20):
        from sklearn.metrics import mean_squared_error
        from sklearn.model_selection import cross_val_score
        
        self._generate_k_fold(kfolds)
        for m in range(models):
            mod, params = self._declare_model(model, parameters)
            
            score = []
            for  train_index, test_index in self._folds.split(self.X_train):
                mod.fit(self.X_train.iloc[train_index], self.y_train.iloc[train_index])
                pred = mod.predict(self.X_train.iloc[test_index])
                score.append(np.sqrt(np.power(pred - self.y_train.iloc[test_index], 2).sum())/len(pred))
                #score.append(r2_score(pred, self.y_train[test_index]))
            #mse =  cross_val_score(mod, self.X_train, self.y_train, cv = kfolds, scoring = "neg_mean_squared_error")
            self._models["params"].append(params)
            self._models["model"].append(parameters["name"])
            self._models["score"].append(np.mean(score))
            self._models["score_details"].append(score)
            print(m, "-", np.mean(score))
            
    def final_train(self, model):
        self.model = model
        self.model.fit(self.X_train, self.y_train)
        
    def plot(self):
        sns.scatterplot(self.predictions, self.y_test)
        
    def evaluate(self):
        self.predictions = self.model.predict(self.X_test)
        self.plot()
        self.score = np.sqrt(np.power(self.predictions - self.y_test, 2).sum())/len(self.predictions)
        #self.score = r2_score(self.predictions, self.y_test)
        print(self.score)
            